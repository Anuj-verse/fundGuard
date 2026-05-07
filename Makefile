# FundGuard Makefile

```makefile
.PHONY: dev build test lint format deploy down clean logs

# Target for local development up
dev:
	cd services && docker compose up -d --build

# Bring down local services
down:
	cd services && docker compose down

# Check logs of all local services
logs:
	cd services && docker compose logs -f

# Run integration tests
test:
	. v_env/bin/activate && python services/integration_test.py

# Lint Python code across all services
lint:
	. v_env/bin/activate && flake8 services/

# Format Python code
format:
	. v_env/bin/activate && black services/

# Generate mock data
generate-data:
	. v_env/bin/activate && cd data/generator && python main.py

# Cleanup virtual environments and dangling files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
```