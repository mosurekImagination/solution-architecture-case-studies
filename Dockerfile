FROM python:3.9-slim

# Install Graphviz and required system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    graphviz \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Ensure /app is in Python's module search path
ENV PYTHONPATH="/app"

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy diagram scripts
COPY *.py .

# Default command (can be overridden)
CMD ["python", "demo_diagram.py"]
