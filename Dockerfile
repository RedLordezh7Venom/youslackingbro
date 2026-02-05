# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Install system dependencies for Tesseract and Grab
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama binary
RUN curl -L https://ollama.com/download/ollama-linux-amd64 -o /usr/bin/ollama && chmod +x /usr/bin/ollama

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in pyproject.toml
# Note: Since it's a pyproject.toml, we can install using pip .
RUN pip install .

# Environment variables for Ollama
ENV OLLAMA_HOST=0.0.0.0

# Expose the Ollama port
EXPOSE 11434

# Start Ollama in the background, wait for it to be ready, pull the model, then run the app
# Note: Screen capture in Docker is limited (no X11/Display usually), 
# so this is primarily for development/server-side analysis of uploaded/bound screenshots.
CMD ["sh", "-c", "ollama serve & sleep 5 && ollama pull llama3.2 && python main.py"]
