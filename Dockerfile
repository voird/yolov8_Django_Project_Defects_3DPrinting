FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DockerHome=Django-Yolov8-API-App-main/Django-Yolov8-API-App-main
WORKDIR $DockerHome

COPY . $DockerHome

RUN pip install --no-cache-dir -r requirements.txt