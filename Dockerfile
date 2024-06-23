# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app and install dependencies
COPY . /app

# Copy the SSL certificates to a secure location within the container
COPY new_private.key /etc/ssl/private/private.key
COPY new_certificate.crt /etc/ssl/certs/certificate.crt

# Upgrade pip and install any needed packages specified in requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Make port 5011 and WebSocket port available to the world outside this container
EXPOSE 5011 6790

# Define environment variable
ENV NAME ServiceNowKB

# Run the application using a script to handle both servers
CMD ["./run.sh"]
