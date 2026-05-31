FROM python:3.11-slim

WORKDIR /app

# Install Python deps first to leverage Docker layer caching.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the library + a default suite so the image runs out of the box.
COPY evals/           /app/evals/
COPY sample_suite.yaml /app/sample_suite.yaml

# Mount /reports as a volume to retrieve the generated HTML; mount /suites
# to bring your own suite YAMLs in: `docker run -v $PWD/reports:/app/reports
# -e OPENAI_API_KEY=... llm-eval-harness --suite sample_suite.yaml --report /app/reports/out.html`.
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "-m", "evals.cli"]
CMD ["--suite", "sample_suite.yaml", "--report", "/app/reports/eval_report.html"]
