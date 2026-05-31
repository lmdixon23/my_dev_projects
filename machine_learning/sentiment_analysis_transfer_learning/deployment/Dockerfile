FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
    && rm -rf /var/lib/apt/lists/*

COPY deployment/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the fine-tuned BERT model and the Flask app.
COPY saved_models/ /app/saved_models/
COPY deployment/app.py /app/app.py

EXPOSE 5002
ENV MODEL_DIR=/app/saved_models/bert

CMD ["python", "app.py"]
