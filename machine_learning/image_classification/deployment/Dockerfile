FROM python:3.11-slim

WORKDIR /app

# System deps for Pillow (libjpeg, zlib are already in slim).
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first to leverage Docker layer caching.
COPY deployment/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the trained model and the Flask app.
COPY saved_models/ /app/saved_models/
COPY deployment/app.py /app/app.py

EXPOSE 5000
ENV FLASK_APP=app.py

CMD ["python", "app.py"]
