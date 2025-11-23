FROM python:3.11.8-slim

WORKDIR /app

# copy requirements first for better caching
COPY server/requirements.txt .

# fix openai version compatibility and install requirements
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    curl \
    wget \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --upgrade pip \
 && pip uninstall -y openai \
 && pip install openai==1.88.0 \
 && pip install -r requirements.txt



# copy the entire server directory contents to /app (flattening the structure)
# this makes imports like 'core.tasks' work directly
COPY ./server/ /app/

# ensure we have the config directory at the root level too
COPY ./server/config /app/config

# set python environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app