FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY indexer/requirements.txt ./indexer/requirements.txt

RUN pip install --no-cache-dir -r indexer/requirements.txt

# Install click (required by spaCy CLI)
RUN pip install --no-cache-dir click

# Download spaCy model
RUN python -m spacy download en_core_web_sm

COPY . .

CMD ["python", "-m", "indexer.main"]