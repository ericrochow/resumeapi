FROM python:3.10

WORKDIR /api

COPY . /api
COPY .env /api/.env

RUN pip install -r requirements.txt

ENTRYPOINT ["python3"]
CMD ["/api/entrypoint.py"]

EXPOSE 8000
