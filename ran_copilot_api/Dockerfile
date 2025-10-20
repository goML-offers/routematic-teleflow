# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the src directory into the container at /app
COPY ./src .

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variables (can be overridden at runtime)
# These are important for the application to connect to AWS services
ENV AWS_REGION=ap-south-1
ENV ATHENA_DATABASE=ran_copilot
ENV ATHENA_OUTPUT_LOCATION=s3://ran-copilot-data-lake/athena-results/
# These must be provided when running the container
ENV BEDROCK_AGENT_ID=""
ENV BEDROCK_AGENT_ALIAS_ID=""
ENV AWS_ACCESS_KEY_ID=""
ENV AWS_SECRET_ACCESS_KEY=""

# Run app.py when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
