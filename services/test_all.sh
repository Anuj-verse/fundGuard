#!/bin/bash
set -e

echo "Running Edge Service Tests..."
cd /home/anuj-gope/fundguard/fundguard/services/edge-service
# Mock out the Redis/Kafka requirements for edge if needed, or rely on integration tests.
echo "Skipping local edge tests due to Redis/Kafka deps. Use integration tests instead."

echo "Running Risk Engine Tests..."
cd ../risk-engine
pip install -q pytest httpx
pytest tests/

echo "Running Graph Service Tests..."
cd ../graph-service
pip install -q pytest
echo "Skipping graph tests due to neo4j deps"

echo "All local unit tests checked."
echo "For full integration testing, ensure docker-compose is running and run:"
echo "python /home/anuj-gope/fundguard/fundguard/services/integration_test.py"
