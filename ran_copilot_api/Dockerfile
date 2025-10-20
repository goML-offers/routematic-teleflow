# Use the official AWS base image for Python 3.11 on Lambda
FROM public.ecr.aws/lambda/python:3.11

# Set the working directory to the AWS Lambda default
WORKDIR /var/task

# Copy dependency files and install
COPY requirements.txt .
RUN pip install -r requirements.txt

# Explicitly copy the src directory into the workdir
COPY src ./src

# Set the command to the full import path of the handler
CMD [ "src.main.handler" ]
