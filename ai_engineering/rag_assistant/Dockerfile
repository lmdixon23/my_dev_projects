FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY rag/ /app/rag/
COPY app.py cli.py /app/
COPY index/ /app/index/

EXPOSE 8080
ENV RAG_STORE=/app/index
ENV PORT=8080

CMD ["python", "app.py"]
