# Use an official Python runtime as a parent image
FROM python:3.9

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory in the container
WORKDIR /app

# Create a new user 'suleyman_kaya' and set a password 'mypassword'
RUN useradd -ms /bin/bash suleyman_kaya
RUN echo "suleyman_kaya:admin" | chpasswd

# Install dependencies:
COPY requirements requirements/
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements/local.txt
RUN chown -R suleyman_kaya:suleyman_kaya /app/static
RUN chmod -R 755 /app/static


# Change to the new user
USER suleyman_kaya