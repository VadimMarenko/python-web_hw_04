import json
import pathlib
import urllib.parse
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
from threading import Thread
import logging
from datetime import datetime

BASE_DIR = pathlib.Path()
SOCKET_SERVER_IP = "127.0.0.1"
SOCKET_SERVER_PORT = 5000
HTTP_SERVER_IP = "0.0.0.0"
SOCKET_BUFFER_SIZE = 1024
HTTP_SERVER_PORT = 3000
HTTP_STATUS_OK = 200
HTTP_STATUS_FOUND = 302
HTTP_STATUS_NOT_FOUND = 404

def send_data_to_socket(body):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(body, (SOCKET_SERVER_IP, SOCKET_SERVER_PORT))
    client_socket.close()


class HTTPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        send_data_to_socket(body)
        self.send_response(HTTP_STATUS_FOUND)
        self.send_header("Location", "index.html")
        self.end_headers()

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case "/":
                self.send_html("index.html")
            case "/message":
                self.send_html("message.html")
            case _:
                file = BASE_DIR / route.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html("error.html", HTTP_STATUS_NOT_FOUND)

    def send_html(self, filename, status_code=HTTP_STATUS_OK):
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        with open(filename, "rb") as f:
            self.wfile.write(f.read())

    def send_static(self, filename):
        self.send_response(HTTP_STATUS_OK)
        mime_type, *rest = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header("Content-Type", mime_type)
        else:
            self.send_header("Content-Type", "text/plain")
        self.end_headers()
        with open(filename, "rb") as f:
            self.wfile.write(f.read())


def run(server=HTTPServer, handler=HTTPHandler):
    address = (HTTP_SERVER_IP, HTTP_SERVER_PORT)
    http_server = server(address, handler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


def save_data(data):
    body = urllib.parse.unquote_plus(data.decode())
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S.%f")
    try:
        data_dict = {
            formatted_time: {
                key: value for key, value in [el.split("=") for el in body.split("&")]
            }
        }
        BASE_DIR.joinpath('storage').mkdir(exist_ok=True)
        
        if BASE_DIR.joinpath("storage/data.json").exists():
            print("OK")
            
            with open(BASE_DIR.joinpath("storage/data.json"), "r") as fd:
                data = fd.read()
                if not data:
                    existing_data = dict()
                else:
                    existing_data = json.load(fd)

                existing_data.update(data_dict)
        else:

            existing_data = data_dict
            print(existing_data)

        with open(BASE_DIR.joinpath("storage/data.json"), "w", encoding="utf-8") as fd:
            json.dump(
                existing_data,
                fd,
                ensure_ascii=False,
                indent=4,
            )
    except ValueError as err:
        logging.error(f"Field parse data {body} with error {err}")
    except OSError as err:
        logging.error(f"Field write data {body} with error {err}")    
    except json.JSONDecodeError as err:
        logging.error(f"Field write data {body} with error {err}")


def run_socket_server(ip, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    server_socket.bind(server)
    try:
        while True:
            data, address = server_socket.recvfrom(SOCKET_BUFFER_SIZE)
            save_data(data)
    except KeyboardInterrupt:
        logging.info("The socket server is stopped")
    finally:
        server_socket.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(threadName)s %(message)s")
    thread_server = Thread(target=run)
    thread_server.start()

    thread_socket = Thread(
        target=run_socket_server(SOCKET_SERVER_IP, SOCKET_SERVER_PORT)
    )
    thread_socket.start()
