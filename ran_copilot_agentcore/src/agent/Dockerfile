# Use a standard, slim Python base image for a smaller footprint
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Set environment variables for the container
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    PYTHONPATH=/app

# Copy the application source code and requirements file
COPY src/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY src/agent/app.py ./agent.py

# Expose port 8080 to the AgentCore Runtime
EXPOSE 8080

# Add a health check to ensure the service is running
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import httpx; exit(0 if httpx.get('http://localhost:8080/ping').status_code == 200 else 1)"

# The command to run the AgentCore SDK application
# Using the simpler SDK integration approach from Strands documentation
CMD ["uvicorn", "agent:app", "--host", "0.0.0.0", "--port", "8080"]
