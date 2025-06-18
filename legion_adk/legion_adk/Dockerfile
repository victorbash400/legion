# legion_adk/Dockerfile

FROM python:3.11-slim

# Set environment variables for non-interactive installs
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies (if any, not strictly needed for this basic setup)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     # Add any necessary system packages here, e.g., curl, git, build-essential
#     && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file and install Python dependencies
# It's good practice to copy requirements.txt separately to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install google-generative-ai-toolkit and any other direct dependencies
RUN pip install google-generative-ai-toolkit httpx python-dotenv

# Copy the entire application code into the container
COPY . /app

# Expose the port FastAPI will run on
EXPOSE 3001

# Set environment variables for API keys
# These should ideally be passed at runtime or managed by a secret manager in production
# For local development, they can be read from .env but for Docker, define them here
ENV GEMINI_API_KEY=${GEMINI_API_KEY}
ENV SONAR_API_KEY=${SONAR_API_KEY}

# Command to run the FastAPI application using Uvicorn
# The --host 0.0.0.0 makes it accessible from outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3001"]