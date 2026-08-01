import asyncio
import os
from dotenv import load_dotenv

load_dotenv(os.path.abspath('.env'))

from fastapi.testclient import TestClient
from app.main import app

def test_api():
    client = TestClient(app)
    
    # Check /by-source
    resp_source = client.get('/api/v1/movies/by-source?chat_id=-1003941035700&topic_id=405')
    print("Source Status:", resp_source.status_code)
    
    # Check /code/{code}
    resp_code = client.get('/api/v1/movies/code/47KF9F')
    print("Code Status:", resp_code.status_code)
    # print("Code Response:", resp_code.text)

if __name__ == "__main__":
    test_api()
