FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Pre-pull the Gemma 3 model
RUN nohup ollama serve > /tmp/ollama.log 2>&1 & \
    sleep 5 && \
    ollama pull gemma3:270m

# Expose Ollama and API ports
EXPOSE 8080

# Copy app files
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

COPY app .

# Start Ollama
CMD ["bash", "-c", "ollama serve & uvicorn main:app --host 0.0.0.0 --port 8080"]
