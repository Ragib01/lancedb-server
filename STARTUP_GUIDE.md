# 🚀 LanceDB Server Startup Guide

This guide shows you how to start the LanceDB server and connect to it remotely from Python.

## 📋 Prerequisites

Make sure you have these installed:
- Docker Engine 20.10+
- Docker Compose 2.0+
- Python 3.8+ (for client scripts)

## 🏁 Quick Start

### Step 1: Start the LanceDB Server

1. **Configure environment**:
   ```bash
   # Copy the environment template
   cp .env.example .env
   
   # Edit the .env file with your settings
   nano .env
   ```

2. **Start all services**:
   ```bash
   # Start LanceDB server with PostgreSQL and Redis
   docker-compose up -d
   
   # Check if services are running
   docker-compose ps
   ```

3. **Verify the server is running**:
   ```bash
   # Test health endpoint
   curl http://localhost:9000/health
   
   # Should return: {"status":"healthy","service":"lancedb-server","version":"1.0.0"}
   ```

### Step 2: Install Python Dependencies

For the client scripts, install required packages:

```bash
# Install required packages
pip install requests numpy

# Or create a virtual environment (recommended)
python -m venv lancedb_client
source lancedb_client/bin/activate  # On Windows: lancedb_client\Scripts\activate
pip install requests numpy
```

### Step 3: Run Test Clients

1. **Simple test** (basic functionality):
   ```bash
   python simple_client.py
   ```

2. **Comprehensive test** (full features):
   ```bash
   python test_client.py
   ```

## 📊 Server Management

### Start/Stop Services

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f lancedb
```

### Monitor Services

```bash
# Check service status
docker-compose ps

# View resource usage
docker stats

# Check specific service logs
docker-compose logs postgres
docker-compose logs redis
```

## 🔧 Configuration Options

### Development Mode

For development with authentication disabled:

```bash
# Edit .env file
LANCEDB_AUTH_ENABLED=false
LANCEDB_LOG_LEVEL=DEBUG

# Restart services
docker-compose restart lancedb
```

### Production Mode

For production with monitoring:

```bash
# Start with monitoring stack
docker-compose --profile production --profile monitoring up -d

# Access monitoring
# Prometheus: http://localhost:9091
# Grafana: http://localhost:9301 (admin/admin)
```

## 🔐 Authentication Setup

### Enable Authentication

1. **Edit .env file**:
   ```bash
   LANCEDB_AUTH_ENABLED=true
   LANCEDB_JWT_SECRET=your-very-secure-secret-key-here
   ```

2. **Restart services**:
   ```bash
   docker-compose restart lancedb
   ```

3. **Create API key** (if authentication is enabled):
   ```bash
   # This requires manual setup in the database or use the API
   # For now, you can disable auth for testing
   ```

## 🌐 Remote Access

### Access from Another Machine

1. **Update server URL** in client scripts:
   ```python
   # In simple_client.py or test_client.py
   LANCEDB_SERVER = "http://YOUR_SERVER_IP:9000"
   ```

2. **Configure firewall** (if needed):
   ```bash
   # Allow port 9000
   sudo ufw allow 9000
   ```

3. **Update CORS settings** (for web clients):
   ```bash
   # In .env file
   LANCEDB_CORS_ORIGINS=http://your-client-domain.com,http://localhost:3000
   ```

## 📝 Client Examples

### Basic Python Client

```python
import requests

# Server configuration
server_url = "http://localhost:9000"

# Health check
response = requests.get(f"{server_url}/health")
print(response.json())

# Create database
response = requests.post(
    f"{server_url}/v1/databases",
    json={"name": "my_db"},
    headers={"Content-Type": "application/json"}
)
print(response.json())
```

### Vector Search Example

```python
import requests

server_url = "http://localhost:9000"
db_name = "my_db"
table_name = "vectors"

# Create table with data
data = [
    {"id": 1, "vector": [0.1, 0.2, 0.3], "text": "Hello"},
    {"id": 2, "vector": [0.4, 0.5, 0.6], "text": "World"}
]

requests.post(
    f"{server_url}/v1/databases/{db_name}/tables/{table_name}",
    json={"name": table_name, "data": data, "mode": "create"},
    headers={"Content-Type": "application/json"}
)

# Search
search_result = requests.post(
    f"{server_url}/v1/databases/{db_name}/tables/{table_name}/search",
    json={"vector": [0.2, 0.3, 0.4], "limit": 5},
    headers={"Content-Type": "application/json"}
)

print(search_result.json())
```

## 🔍 Troubleshooting

### Common Issues

1. **Port conflicts**:
   ```bash
   # Check what's using port 9000
   lsof -i :9000
   
   # Change port in .env if needed
   LANCEDB_PORT=9001
   ```

2. **Docker not starting**:
   ```bash
   # Check Docker daemon
   docker --version
   docker-compose --version
   
   # Check logs
   docker-compose logs
   ```

3. **Connection refused**:
   ```bash
   # Check if container is running
   docker-compose ps
   
   # Check container logs
   docker-compose logs lancedb
   ```

4. **Authentication errors**:
   ```bash
   # Disable auth for testing
   # In .env:
   LANCEDB_AUTH_ENABLED=false
   
   # Restart
   docker-compose restart lancedb
   ```

### Health Checks

```bash
# Server health
curl http://localhost:9000/health

# Detailed status (requires auth if enabled)
curl http://localhost:9000/v1/status

# API documentation
open http://localhost:9000/docs
```

## 📚 API Endpoints

### Core Endpoints

- **Health**: `GET /health`
- **API Docs**: `GET /docs`
- **Metrics**: `GET /metrics`

### Database Operations

- **List databases**: `GET /v1/databases`
- **Create database**: `POST /v1/databases`
- **Get database**: `GET /v1/databases/{name}`
- **Delete database**: `DELETE /v1/databases/{name}`

### Table Operations

- **Create table**: `POST /v1/databases/{db}/tables/{table}`
- **Search vectors**: `POST /v1/databases/{db}/tables/{table}/search`
- **Add data**: `POST /v1/databases/{db}/tables/{table}/data`
- **Get data**: `GET /v1/databases/{db}/tables/{table}/data`

## 🎯 Next Steps

1. **Run the test scripts** to verify everything works
2. **Explore the API docs** at http://localhost:9000/docs
3. **Check monitoring** (if enabled) at http://localhost:9091
4. **Build your application** using the REST API or Python client

## 💡 Tips

- Use `docker-compose logs -f` to monitor server activity
- The server data persists in Docker volumes
- For production, enable authentication and HTTPS
- Monitor performance with the included Prometheus setup
- Use the backup script for data protection

## 📞 Support

- Check the main README.md for detailed configuration
- View API documentation at `/docs` endpoint
- Monitor logs for troubleshooting
- Use the test scripts to verify functionality 