FROM python:3.11.2
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . .
VOLUME /app/storage
#EXPOSE 3000

ENTRYPOINT ["python", "main.py"]