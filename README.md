# FundGuard 🛡️

FundGuard is a real-time, event-driven microservices architecture designed to detect, analyze, and prevent financial fraud. By combining high-speed streaming machine learning at the edge with deep graph-based pattern recognition, FundGuard provides a comprehensive, low-latency defense against complex financial crimes like money laundering, account takeovers, and organized fraud rings.

---

## 🏗️ System Architecture

FundGuard leverages a pub/sub event mesh powered by **Apache Kafka** to decouple processing stages, ensuring sub-50ms latency from ingestion to final decision.

### High-Level Data Flow
1. **Ingestion & Edge Scoring**: Transactions enter the system via the Edge Service.
2. **Streaming Pipeline**: Evaluated events are published to Kafka topics.
3. **Graph Analysis**: Transactions are ingested into Neo4j; continuous pattern algorithms identify sub-networks and complex relationships.
4. **Risk Synthesis**: A unified Risk Engine aggregates model scores, graph signals, and static rules to produce a final determination.
5. **Real-time Monitoring**: Results are streamed via WebSockets to a React-based Dashboard.

---

## 🧩 Microservices Overview

The repository is modularized into distinct, containerized services located in the `services/` directory:

### 1. Edge Service (`edge-service`)
- **Role**: Frontline transaction ingestion and fast inference.
- **Tech Stack**: FastAPI, ONNX, Redis.
- **Function**: Receives HTTP POST requests, validates schemas, updates/fetches real-time velocity metrics from Redis, and runs high-speed XGBoost inference via ONNX. Publishes the transaction and `edge_score` to the `transactions-live` Kafka topic.

### 2. Graph Service (`graph-service`)
- **Role**: Complex pattern detection and relational deep-analysis.
- **Tech Stack**: Python, Neo4j, Apache Kafka.
- **Function**: Consumes from `transactions-live`. Ingests accounts, devices, and transactions into a **Neo4j** graph database. Runs continuous Graph Data Science (GDS) algorithms to detect sophisticated topologies like "mule activation" and "hub and spoke" behaviors. Emits findings to the `graph-events` topic.

### 3. Unified Risk Engine (`risk-engine`)
- **Role**: Final decisioning and rule aggregation.
- **Tech Stack**: FastAPI, Kafka Consumer/Producer.
- **Function**: Subscribes to `graph-events`. Combines the ONNX ML `edge_score`, the Neo4j `graph_score`/flags, and hardcoded static risk rules (e.g., extremely high transfer amounts). Computes a final continuous `unified_score` and discrete decision (`ALLOW`, `REVIEW`, `REJECT`). Publishes the output to `risk-scores`.

### 4. Dashboard API (`dashboard-api`)
- **Role**: Real-time websocket gateway for the UI.
- **Tech Stack**: FastAPI, AIOKafka, WebSockets.
- **Function**: Consumes the final `risk-scores` topic and streams these directly to connected clients via WebSockets, allowing the ops team to monitor the fraud posture live.

### 5. LLM Service (`llm-service`)
- **Role**: Generative AI explainer.
- **Tech Stack**: Python, FastAPI.
- **Function**: Provides human-readable, plain-text explanations of *why* a specific transaction was flagged, utilizing Generative AI.

### 6. Operations Dashboard (`dashboard`)
- **Role**: Frontend monitoring application.
- **Tech Stack**: React, TypeScript.
- **Function**: Connects to the Dashboard API via WebSockets to render a live, dynamic feed of incoming transactions, risk scores, and anomaly warnings.

---

## 🛠️ Infrastructure

FundGuard relies on several robust infrastructure components, all fully containerized:
- **Apache Kafka & Zookeeper**: The messaging backbone handling `transactions-live`, `graph-events`, and `risk-scores`.
- **Neo4j (w/ GDS Plugin)**: Graph database used to map accounts, physical locations, and transfer edges to identify fraud rings.
- **Redis**: High-speed, in-memory cache used by the Edge Service for tracking sliding-window transaction velocities.

---

## 🚀 Getting Started

### Prerequisites
- Docker Engine & Docker Compose
- Python 3.11+
- Virtual Environment (recommended)

### Up and Running
1. **Initialize the Infrastructure and Services**
   Navigate to the `services` directory and execute Docker Compose:
   ```bash
   cd services
   docker compose up -d --build
   ```
   *This spins up Kafka, Zookeeper, Redis, Neo4j, and all FundGuard microservices.*

2. **Verify Containers**
   Ensure all containers are running properly:
   ```bash
   docker ps
   ```

3. **Run the Integration Test**
   FundGuard includes a synthetic generator that pushes realistic financial traffic (normal transactions, whales, and velocity attacks):
   ```bash
   # Activate your local environment
   source v_env/bin/activate
   
   # Run the integration suite
   python services/integration_test.py
   ```

4. **Monitor the Dashboard**
   Open your browser and navigate to `http://localhost:3000` to watch the transactions get scored and routed in real-time.

---

## 🧪 Testing & Data Generation

The project includes a highly sophisticated synthetic data generator (`data/generator`) capable of simulating various user locales, fraud typologies, and transactional behaviors to effectively test the machine learning and graph heuristic models. 

---
*FundGuard - Protecting the financial ecosystem through AI, Graphs, and Event-Driven Architecture.*