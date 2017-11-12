FROM python:3.6-alpine

COPY requirements.txt /

RUN pip install -r /requirements.txt

EXPOSE 5000

WORKDIR /app

ENTRYPOINT [ "python", "/app/black.py", "--port", "5000"  ]
