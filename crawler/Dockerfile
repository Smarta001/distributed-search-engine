FROM python:3.10-slim

WORKDIR /app

COPY crawler/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY crawler/ .

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]