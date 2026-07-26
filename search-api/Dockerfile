FROM python:3.10-slim

WORKDIR /app

COPY search-api/requirements.txt ./search-api/requirements.txt

RUN pip install --no-cache-dir -r search-api/requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

WORKDIR /app/search-api

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]