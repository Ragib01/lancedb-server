#!/usr/bin/env python3
"""
Simple LanceDB Remote Client Example
Basic example showing how to connect and use LanceDB remotely
"""

import requests
import json

# Configuration
LANCEDB_SERVER = "http://localhost:9000"  # Your LanceDB server URL
API_KEY = None  # Set your API key here if needed

# Headers for requests
headers = {
    'Content-Type': 'application/json'
}
if API_KEY:
    headers['Authorization'] = f'Bearer {API_KEY}'

def main():
    print("🚀 Simple LanceDB Remote Client")
    print("=" * 40)
    
    # 1. Check server health
    print("\n1. Checking server health...")
    try:
        response = requests.get(f"{LANCEDB_SERVER}/health")
        if response.status_code == 200:
            print("✅ Server is running!")
        else:
            print("❌ Server health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # 2. Create a database
    print("\n2. Creating database...")
    db_name = "my_vector_db"
    try:
        response = requests.post(
            f"{LANCEDB_SERVER}/v1/databases",
            headers=headers,
            json={"name": db_name}
        )
        if response.status_code == 200:
            print(f"✅ Database '{db_name}' created!")
        elif response.status_code == 409:
            print(f"ℹ️ Database '{db_name}' already exists")
        else:
            print(f"❌ Failed to create database: {response.text}")
    except Exception as e:
        print(f"❌ Error creating database: {e}")
    
    # 3. Create a table with sample data
    print("\n3. Creating table with sample data...")
    table_name = "documents"
    sample_data = [
        {
            "id": 1,
            "vector": [0.1, 0.2, 0.3, 0.4],
            "text": "Hello world",
            "category": "greeting"
        },
        {
            "id": 2,
            "vector": [0.5, 0.6, 0.7, 0.8],
            "text": "Python programming",
            "category": "tech"
        },
        {
            "id": 3,
            "vector": [0.9, 0.1, 0.5, 0.3],
            "text": "Machine learning",
            "category": "ai"
        }
    ]
    
    try:
        response = requests.post(
            f"{LANCEDB_SERVER}/v1/databases/{db_name}/tables/{table_name}",
            headers=headers,
            json={
                "name": table_name,
                "data": sample_data,
                "mode": "create"
            }
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Table '{table_name}' created with {result['row_count']} rows!")
        else:
            print(f"❌ Failed to create table: {response.text}")
    except Exception as e:
        print(f"❌ Error creating table: {e}")
    
    # 4. Perform vector search
    print("\n4. Performing vector search...")
    query_vector = [0.2, 0.3, 0.4, 0.5]
    
    try:
        response = requests.post(
            f"{LANCEDB_SERVER}/v1/databases/{db_name}/tables/{table_name}/search",
            headers=headers,
            json={
                "vector": query_vector,
                "limit": 3,
                "metric": "cosine"
            }
        )
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Search completed in {results['query_time_ms']:.2f}ms")
            print("📋 Results:")
            for i, result in enumerate(results['results']):
                print(f"   {i+1}. ID: {result['id']}, Text: '{result['text']}', Distance: {result.get('_distance', 'N/A'):.4f}")
        else:
            print(f"❌ Search failed: {response.text}")
    except Exception as e:
        print(f"❌ Error during search: {e}")
    
    # 5. Add more data
    print("\n5. Adding more data...")
    new_data = [
        {
            "id": 4,
            "vector": [0.2, 0.8, 0.1, 0.9],
            "text": "Data science",
            "category": "tech"
        }
    ]
    
    try:
        response = requests.post(
            f"{LANCEDB_SERVER}/v1/databases/{db_name}/tables/{table_name}/data",
            headers=headers,
            json=new_data
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Added {result['rows_added']} new rows! Total: {result['total_rows']}")
        else:
            print(f"❌ Failed to add data: {response.text}")
    except Exception as e:
        print(f"❌ Error adding data: {e}")
    
    print("\n" + "=" * 40)
    print("🎉 Simple client test completed!")
    print(f"📊 Database: {db_name}")
    print(f"📋 Table: {table_name}")
    print(f"🌐 Server: {LANCEDB_SERVER}")

if __name__ == "__main__":
    main() 