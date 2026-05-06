FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and models
COPY app /app/app
COPY models /app/models

# Set environment variables
ENV MODEL_PATH=/app/models/xgboost_model.onnx
ENV KAFKA_BROKERS=kafka:9092

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
