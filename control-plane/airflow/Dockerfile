FROM python:3.11-slim

# Set environment variables
ENV AIRFLOW_HOME=/opt/airflow
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__CORE__EXECUTOR=LocalExecutor
ENV AIRFLOW__WEBSERVER__EXPOSE_CONFIG=True
ENV AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=True

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Create airflow user and directories
RUN useradd -ms /bin/bash -d ${AIRFLOW_HOME} airflow && \
    mkdir -p ${AIRFLOW_HOME}/dags ${AIRFLOW_HOME}/logs ${AIRFLOW_HOME}/plugins ${AIRFLOW_HOME}/config

# Set working directory
WORKDIR ${AIRFLOW_HOME}

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy DAGs and plugins
COPY dags/ ${AIRFLOW_HOME}/dags/
COPY plugins/ ${AIRFLOW_HOME}/plugins/
COPY config/ ${AIRFLOW_HOME}/config/

# Set permissions
RUN chown -R airflow: ${AIRFLOW_HOME}

# Switch to airflow user
USER airflow

# Initialize the database (will be overridden by entrypoint in docker-compose)
# This is just for documentation purposes
# RUN airflow db init

EXPOSE 8080

# Default command (will be overridden in docker-compose)
CMD ["airflow", "webserver"]
