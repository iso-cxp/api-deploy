FROM python:slim

RUN \
  pip install Flask paramiko && \
  pip install gevent

ADD . /var/www/api-deploy

WORKDIR /var/www/api-deploy

EXPOSE 5000

ENTRYPOINT python serve.py
