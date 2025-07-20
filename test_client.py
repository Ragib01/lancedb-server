#!/usr/bin/env python3
"""
LanceDB Remote Client Test
This script demonstrates how to connect to and use a remote LanceDB server
"""

import requests
import json
import time
import numpy as np
from typing import List, Dict, Any

class LanceDBRemoteClient:
    """Remote LanceDB client using REST API"""
    
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Content-Type': 'application/json'
        }
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
    
    def health_check(self) -> bool:
        """Check if server is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
    
    def list_databases(self) -> List[Dict]:
        """List all databases"""
        response = requests.get(f"{self.base_url}/v1/databases", headers=self.headers)
        response.raise_for_status()
        return response.json()['databases']
    
    def create_database(self, name: str) -> Dict:
        """Create a new database"""
        data = {"name": name}
        response = requests.post(f"{self.base_url}/v1/databases", 
                               headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def get_database(self, name: str) -> Dict:
        """Get database information"""
        response = requests.get(f"{self.base_url}/v1/databases/{name}", 
                              headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def create_table(self, database_name: str, table_name: str, data: List[Dict], mode: str = "create") -> Dict:
        """Create a table with data"""
        payload = {
            "name": table_name,
            "data": data,
            "mode": mode
        }
        response = requests.post(f"{self.base_url}/v1/databases/{database_name}/tables/{table_name}",
                               headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def search_table(self, database_name: str, table_name: str, vector: List[float], 
                    limit: int = 10, metric: str = "cosine") -> Dict:
        """Perform vector search on table"""
        payload = {
            "vector": vector,
            "limit": limit,
            "metric": metric
        }
        response = requests.post(f"{self.base_url}/v1/databases/{database_name}/tables/{table_name}/search",
                               headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def add_data(self, database_name: str, table_name: str, data: List[Dict]) -> Dict:
        """Add data to existing table"""
        response = requests.post(f"{self.base_url}/v1/databases/{database_name}/tables/{table_name}/data",
                               headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def get_table_data(self, database_name: str, table_name: str, limit: int = 100, offset: int = 0) -> Dict:
        """Get data from table"""
        params = {"limit": limit, "offset": offset}
        response = requests.get(f"{self.base_url}/v1/databases/{database_name}/tables/{table_name}/data",
                              headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()


def generate_sample_data(num_samples: int = 100, vector_dim: int = 128) -> List[Dict]:
    """Generate sample data for testing"""
    data = []
    for i in range(num_samples):
        vector = np.random.random(vector_dim).tolist()
        data.append({
            "id": i,
            "vector": vector,
            "text": f"Sample text {i}",
            "category": f"category_{i % 5}",
            "score": np.random.random()
        })
    return data


def main():
    """Main test function"""
    # Configuration
    SERVER_URL = "http://localhost:9000"  # Update with your server URL
    API_KEY = None  # Set your API key here if authentication is enabled
    
    print("🚀 LanceDB Remote Client Test")
    print("=" * 50)
    
    # Initialize client
    client = LanceDBRemoteClient(SERVER_URL, API_KEY)
    
    # 1. Health Check
    print("\n1. 🏥 Health Check")
    if client.health_check():
        print("✅ Server is healthy!")
    else:
        print("❌ Server is not responding")
        return
    
    # 2. List existing databases
    print("\n2. 📂 List Databases")
    try:
        databases = client.list_databases()
        print(f"Found {len(databases)} databases:")
        for db in databases:
            print(f"  - {db['name']} (ID: {db['id']}, Tables: {db.get('table_count', 'N/A')})")
    except Exception as e:
        print(f"❌ Failed to list databases: {e}")
        return
    
    # 3. Create test database
    print("\n3. 🆕 Create Test Database")
    db_name = f"test_db_{int(time.time())}"
    try:
        db_info = client.create_database(db_name)
        print(f"✅ Created database: {db_info['name']}")
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return
    
    # 4. Generate sample data
    print("\n4. 📊 Generate Sample Data")
    sample_data = generate_sample_data(50, 128)
    print(f"✅ Generated {len(sample_data)} sample records")
    print(f"   Vector dimension: {len(sample_data[0]['vector'])}")
    
    # 5. Create table with data
    print("\n5. 📋 Create Table with Data")
    table_name = "vectors"
    try:
        table_info = client.create_table(db_name, table_name, sample_data)
        print(f"✅ Created table: {table_info['name']}")
        print(f"   Rows: {table_info['row_count']}")
        print(f"   Schema: {len(table_info['schema']['fields'])} fields")
    except Exception as e:
        print(f"❌ Failed to create table: {e}")
        return
    
    # 6. Perform vector search
    print("\n6. 🔍 Vector Search Test")
    query_vector = np.random.random(128).tolist()
    try:
        start_time = time.time()
        results = client.search_table(db_name, table_name, query_vector, limit=5)
        search_time = time.time() - start_time
        
        print(f"✅ Search completed in {search_time:.3f} seconds")
        print(f"   Query time: {results['query_time_ms']:.2f} ms")
        print(f"   Results found: {len(results['results'])}")
        
        # Show top results
        for i, result in enumerate(results['results'][:3]):
            print(f"   Result {i+1}: ID={result.get('id')}, Score={result.get('_distance', 'N/A'):.4f}")
    
    except Exception as e:
        print(f"❌ Search failed: {e}")
    
    # 7. Add more data
    print("\n7. ➕ Add More Data")
    additional_data = generate_sample_data(25, 128)
    # Update IDs to avoid conflicts
    for i, item in enumerate(additional_data):
        item['id'] = 1000 + i
    
    try:
        add_result = client.add_data(db_name, table_name, additional_data)
        print(f"✅ Added {add_result['rows_added']} new rows")
        print(f"   Total rows now: {add_result['total_rows']}")
    except Exception as e:
        print(f"❌ Failed to add data: {e}")
    
    # 8. Retrieve data
    print("\n8. 📥 Retrieve Table Data")
    try:
        data_result = client.get_table_data(db_name, table_name, limit=10)
        print(f"✅ Retrieved {data_result['returned_rows']} rows")
        print(f"   Total rows in table: {data_result['total_rows']}")
        
        # Show sample record
        if data_result['data']:
            sample_record = data_result['data'][0]
            print(f"   Sample record: ID={sample_record.get('id')}, Text='{sample_record.get('text')}'")
    
    except Exception as e:
        print(f"❌ Failed to retrieve data: {e}")
    
    # 9. Test different search metrics
    print("\n9. 🎯 Test Different Search Metrics")
    metrics = ["cosine", "l2", "dot"]
    for metric in metrics:
        try:
            results = client.search_table(db_name, table_name, query_vector, limit=3, metric=metric)
            print(f"   {metric.upper()} metric: {results['query_time_ms']:.2f} ms, {len(results['results'])} results")
        except Exception as e:
            print(f"   ❌ {metric.upper()} metric failed: {e}")
    
    # 10. Performance test
    print("\n10. ⚡ Performance Test")
    num_searches = 10
    total_time = 0
    successful_searches = 0
    
    print(f"Running {num_searches} searches...")
    for i in range(num_searches):
        try:
            query_vec = np.random.random(128).tolist()
            start = time.time()
            client.search_table(db_name, table_name, query_vec, limit=10)
            search_time = time.time() - start
            total_time += search_time
            successful_searches += 1
        except Exception as e:
            print(f"   Search {i+1} failed: {e}")
    
    if successful_searches > 0:
        avg_time = total_time / successful_searches
        print(f"✅ Performance Results:")
        print(f"   Average search time: {avg_time:.3f} seconds")
        print(f"   Searches per second: {1/avg_time:.1f}")
        print(f"   Success rate: {successful_searches}/{num_searches}")
    
    print("\n" + "=" * 50)
    print("🎉 Test completed! Check your LanceDB server logs for details.")
    print(f"📊 Database created: {db_name}")
    print(f"📋 Table created: {table_name}")


if __name__ == "__main__":
    main() 