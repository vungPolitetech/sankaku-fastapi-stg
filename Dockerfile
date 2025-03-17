FROM python:3.10

WORKDIR /app

COPY . .

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE ${HOST_PORT}

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${HOST_PORT}"]
