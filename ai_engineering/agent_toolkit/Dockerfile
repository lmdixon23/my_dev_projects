FROM python:3.11-slim

WORKDIR /app

# Install Python deps first to leverage Docker layer caching.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the library + the demo CLI + the built-in tools.
COPY agent/         /app/agent/
COPY builtin_tools.py cli.py /app/

# Default entrypoint demonstrates the CLI; override at runtime as needed,
# e.g. `docker run --rm -e OPENAI_API_KEY=... agent-toolkit "your prompt"`.
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "cli.py"]
CMD ["What is 17 * 24, and what does RAG stand for?", "--verbose"]
