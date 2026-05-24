FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install tree-sitter languages for parsers
RUN pip install --no-cache-dir tree-sitter==0.22.3 tree-sitter-python tree-sitter-typescript tree-sitter-go tree-sitter-rust tree-sitter-java

COPY . .

ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
