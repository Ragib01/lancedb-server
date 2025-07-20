# LanceDB Server - Remote Deployment Guide

A production-ready LanceDB server deployment that can be used remotely like LanceDB Cloud.

## 📋 Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM
- 20GB+ available disk space
- Network access for remote connections

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd lancedb-server
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (see Configuration section below)
nano .env
```

### 3. Deploy with Docker Compose

```bash
# Start the services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f lancedb
```

### 4. Verify Installation

```bash
# Health check
curl http://localhost:9000/health

# List databases
curl http://localhost:9000/v1/databases
```

## 🔧 Port Configuration

### External Port Mappings (Host → Container)

| Service | External Port | Internal Port | Description |
|---------|---------------|---------------|-------------|
| **LanceDB Server** | `9000` | `9000` | Main API server |
| **PostgreSQL** | `9432` | `5432` | Metadata database |
| **Redis** | `9379` | `6379` | Cache and sessions |
| **Nginx HTTP** | `90` | `80` | Reverse proxy (production) |
| **Nginx HTTPS** | `9443` | `443` | SSL reverse proxy (production) |
| **Prometheus** | `9091` | `9090` | Metrics collection (monitoring) |
| **Grafana** | `9301` | `3000` | Dashboard (monitoring) |

### Access URLs

```bash
# Main API
http://localhost:9000/health
http://localhost:9000/docs

# Database connections (if needed)
psql -h localhost -p 9432 -U lancedb
redis-cli -h localhost -p 9379

# Monitoring (with --profile monitoring)
http://localhost:9091  # Prometheus
http://localhost:9301  # Grafana

# Production web (with --profile production)
http://localhost:90    # HTTP
https://localhost:9443 # HTTPS
```

## ⚙️ Configuration

### Environment Variables (.env)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LANCEDB_PORT` | Server port | `9000` | No |
| `LANCEDB_HOST` | Bind address | `0.0.0.0` | No |
| `LANCEDB_DATA_DIR` | Data directory | `/data` | No |
| `LANCEDB_LOG_LEVEL` | Log level | `INFO` | No |
| `LANCEDB_MAX_CONNECTIONS` | Max concurrent connections | `100` | No |
| `LANCEDB_AUTH_ENABLED` | Enable authentication | `true` | No |
| `LANCEDB_JWT_SECRET` | JWT secret key | `your-secret-key` | Yes* |
| `LANCEDB_CORS_ORIGINS` | CORS allowed origins | `*` | No |
| `POSTGRES_DB` | PostgreSQL database | `lancedb` | No |
| `POSTGRES_USER` | PostgreSQL user | `lancedb` | No |
| `POSTGRES_PASSWORD` | PostgreSQL password | `password` | Yes |
| `REDIS_PASSWORD` | Redis password | `redis_pass` | Yes |

*Required when authentication is enabled

### Security Configuration

For production deployments:

1. **Change default passwords**
2. **Set strong JWT secret**
3. **Configure CORS properly**
4. **Enable HTTPS with reverse proxy**
5. **Use proper firewall rules**

## 🐳 Docker Deployment Options

### Option 1: Docker Compose (Recommended)

```bash
docker-compose up -d
```

### Option 2: Docker Run

```bash
# Create network
docker network create lancedb-net

# Start Redis
docker run -d --name redis \
  --network lancedb-net \
  -e REDIS_PASSWORD=redis_pass \
  redis:7-alpine redis-server --requirepass redis_pass

# Start PostgreSQL
docker run -d --name postgres \
  --network lancedb-net \
  -e POSTGRES_DB=lancedb \
  -e POSTGRES_USER=lancedb \
  -e POSTGRES_PASSWORD=password \
  postgres:15-alpine

# Start LanceDB
docker run -d --name lancedb \
  --network lancedb-net \
  -p 9000:9000 \
  -v lancedb_data:/data \
  -e LANCEDB_JWT_SECRET=your-secret-key \
  lancedb-server:latest
```

## 🔧 Client Usage

### Python Client

```python
import lancedb

# Connect to remote LanceDB instance
uri = "http://your-server:9000"
client = lancedb.connect(uri, api_key="your-api-key")

# Create database
db = client.create_database("my_database")

# Create table
table = db.create_table("my_table", data=[
    {"id": 1, "vector": [1.0, 2.0], "text": "hello"},
    {"id": 2, "vector": [3.0, 4.0], "text": "world"}
])

# Query
results = table.search([1.0, 2.0]).limit(5).to_list()
print(results)
```

### JavaScript Client

```javascript
import { connect } from '@lancedb/lancedb';

// Connect to remote LanceDB instance
const uri = 'http://your-server:9000';
const client = await connect(uri, { apiKey: 'your-api-key' });

// Create database
const db = await client.createDatabase('my_database');

// Create table
const table = await db.createTable('my_table', [
    { id: 1, vector: [1.0, 2.0], text: 'hello' },
    { id: 2, vector: [3.0, 4.0], text: 'world' }
]);

// Query
const results = await table.search([1.0, 2.0]).limit(5).toArray();
console.log(results);
```

### REST API

```bash
# Create database
curl -X POST http://your-server:9000/v1/databases \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "my_database"}'

# Insert data
curl -X POST http://your-server:9000/v1/databases/my_database/tables/my_table/data \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '[{"id": 1, "vector": [1.0, 2.0], "text": "hello"}]'

# Search
curl -X POST http://your-server:9000/v1/databases/my_database/tables/my_table/search \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"vector": [1.0, 2.0], "limit": 5}'
```

## 🔐 Authentication

### API Key Management

```bash
# Generate new API key
curl -X POST http://localhost:9000/v1/auth/api-keys \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-app", "permissions": ["read", "write"]}'

# List API keys
curl http://localhost:9000/v1/auth/api-keys \
  -H "Authorization: Bearer admin-token"

# Revoke API key
curl -X DELETE http://localhost:9000/v1/auth/api-keys/key-id \
  -H "Authorization: Bearer admin-token"
```

## 📊 Monitoring

### Health Checks

```bash
# Server health
curl http://localhost:9000/health

# Detailed status
curl http://localhost:9000/v1/status
```

### Metrics (Prometheus)

```bash
# Metrics endpoint
curl http://localhost:9000/metrics
```

### Logs

```bash
# View logs
docker-compose logs -f lancedb

# With specific service
docker-compose logs -f postgres redis
```

## 🚀 Production Deployment

### Reverse Proxy (Nginx)

See `nginx/nginx.conf` for production Nginx configuration with SSL.

### Kubernetes

See `k8s/` directory for Kubernetes deployment manifests.

### Scaling

- **Horizontal**: Deploy multiple LanceDB instances behind load balancer
- **Vertical**: Increase CPU/memory resources
- **Storage**: Use high-performance SSD storage

## 🔧 Troubleshooting

### Common Issues

1. **Connection refused**
   ```bash
   # Check if service is running
   docker-compose ps
   
   # Check logs
   docker-compose logs lancedb
   ```

2. **Authentication errors**
   ```bash
   # Verify JWT secret is set
   docker-compose exec lancedb env | grep JWT
   ```

3. **Performance issues**
   ```bash
   # Check resource usage
   docker stats
   
   # Monitor database size
   du -sh volumes/lancedb_data/
   ```

### Performance Tuning

1. **Memory**: Increase available RAM
2. **Storage**: Use SSD storage
3. **Network**: Ensure low latency network
4. **Connections**: Tune max connections based on load

## 📚 API Documentation

Full API documentation is available at: `http://your-server:9000/docs`

## 🛡️ Security Best Practices

1. Use strong passwords and API keys
2. Enable HTTPS in production
3. Configure proper CORS settings
4. Use firewall rules to restrict access
5. Regular security updates
6. Monitor access logs
7. Backup data regularly

## 🔄 Backup and Recovery

### Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U lancedb lancedb > backup.sql
tar -czf lancedb_backup.tar.gz volumes/lancedb_data/

# Schedule automatic backups
# See scripts/backup.sh
```

### Recovery

```bash
# Restore database
docker-compose exec postgres psql -U lancedb lancedb < backup.sql

# Restore data
tar -xzf lancedb_backup.tar.gz -C volumes/
```

## 📞 Support

- Documentation: [LanceDB Docs](https://lancedb.github.io/lancedb/)
- Issues: Create an issue in this repository
- Community: [Discord](https://discord.gg/lancedb)

## 📄 License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details. 