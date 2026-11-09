FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    apt-get update && apt-get install -y --no-install-recommends openssh-client && \
    rm -rf /var/lib/apt/lists/*
COPY app.py entrypoint.sh ./
RUN chmod +x /app/entrypoint.sh
EXPOSE 5000
ENTRYPOINT ["/app/entrypoint.sh"]