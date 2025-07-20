# Quick Deployment Guide

## Development Deployment

1. **Clone and configure**:
   ```bash
   git clone <repo-url>
   cd lancedb-server
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Start services**:
   ```bash
   docker-compose up -d
   ```

3. **Verify deployment**:
   ```bash
   curl http://localhost:9000/health
   ```

## Production Deployment

1. **Configure for production**:
   ```bash
   cp .env.example .env
   # Set production values in .env:
   # - Strong passwords
   # - JWT secret
   # - CORS origins
   ```

2. **Generate SSL certificates**:
   ```bash
   ./scripts/generate-ssl.sh
   ```

3. **Deploy with production profile**:
   ```bash
   docker-compose --profile production up -d
   ```

4. **Create first API key**:
   ```bash
   # Access the container and use the API
   curl -X POST http://localhost:8000/v1/auth/api-keys \
     -H "Content-Type: application/json" \
     -d '{"name": "admin", "permissions": ["read", "write", "admin"]}'
   ```

## Monitoring

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **API Docs**: http://localhost:8000/docs

## Backup

```bash
./scripts/backup.sh
```

## Client Usage

```python
import lancedb

# Connect to your instance
client = lancedb.connect("http://your-server:8000", api_key="your-api-key")

# Use as normal LanceDB
db = client.create_database("test")
table = db.create_table("vectors", [{"id": 1, "vector": [1,2,3]}])
results = table.search([1,2,3]).limit(10).to_list()
``` 