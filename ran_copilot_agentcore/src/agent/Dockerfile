# This Dockerfile is for the main Strands Agent.
# Build context should be the project root (ran_copilot_agentcore).
# Example: docker build -f src/agent/Dockerfile -t ran-agent .

FROM public.ecr.aws/lambda/python:3.12

# Copy the entire 'src' directory into the container
COPY src/ ${LAMBDA_TASK_ROOT}/

# Install dependencies
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt

# The agent's handler is in /src/agent/main.py
CMD [ "agent.main.handler" ]
