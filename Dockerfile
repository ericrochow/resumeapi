FROM python:3.10

WORKDIR /api

COPY . /api
COPY .env /api/.env

USER api

RUN pip install -r requirements.txt


ENTRYPOINT ["python3"]
CMD ["/api/entrypoint.py"]
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD [ "curl", "-f", "127.0.0.1:8000" ]

EXPOSE 8000
