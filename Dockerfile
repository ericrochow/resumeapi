# FROM ubuntu:20.04
FROM python:3.7-slim-buster

WORKDIR /api
COPY . /api
# COPY /etc/default/resumeapi /api/.env
RUN apt-get update && apt-get install --yes --no-install-recommends build-essential libffi-dev python3.7-dev python3-pip
RUN pip3 install -r requirements.txt
RUN apt-get purge --yes build-essential libffi-dev
RUN apt-mark hold python3 && apt-mark hold python3.7 && apt-get autoremove --yes
RUN rm -rf /usr/lib/gcc/

ENTRYPOINT ["python3"]
CMD ["/api/entrypoint.py"]

EXPOSE 8000
