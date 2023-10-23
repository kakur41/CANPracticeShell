# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory in the container to /app
WORKDIR /app

# Install necessary dependencies
RUN apt-get update && apt-get install -y socat && pip install pika

# Copy the script
COPY ./can_shell.py /app/can_shell.py

# Expose the port
EXPOSE 12345

RUN chmod +x /app/can_shell.py

# Command to run 
CMD ["socat", "TCP-LISTEN:12345,reuseaddr,fork", "EXEC:/app/can_shell.py 2>&1"]