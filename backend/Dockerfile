FROM python:alpine3.21

WORKDIR /app

COPY requirements.txt .

RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev python3-dev cargo build-base &&\
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000" ]
