# Use an official Python runtime as a parent image
FROM python:3.9

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory in the container
WORKDIR /app

# Install dependencies:
COPY requirements requirements/
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements/local.txt
