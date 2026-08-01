import asyncio
import os
from dotenv import load_dotenv

load_dotenv(os.path.abspath('.env'))

from fastapi.testclient import TestClient
from app.main import app

def test_api():
    client = TestClient(app)
    
    resp = client.get('/api/v1/movies/by-source?chat_id=-1003941035700&topic_id=405')
    print("Status:", resp.status_code)
    print("Response:", resp.text)

if __name__ == "__main__":
    test_api()
