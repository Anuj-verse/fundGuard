FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY app /app/app

# Default environment variables
ENV NEO4J_URI=bolt://neo4j:7687
ENV NEO4J_USER=neo4j
ENV NEO4J_PASS=fraud123456
ENV KAFKA_BROKERS=kafka:29092
ENV KAFKA_TOPIC=edge-decisions

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
