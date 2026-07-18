import asyncio
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzg0MzkyMjcwLCJ0eXBlIjoiYWNjZXNzIiwiZW1haWwiOiJhZG1pbkBraW5vY2hpLnV6Iiwicm9sZSI6InN1cGVyYWRtaW4ifQ._R4uB0sBnojpWkAKNffVUoZ1qtDnzoJrsGKvKdcgA3s"
response = client.post("/api/v1/movies", json={
    "title": "Test Movie",
    "category_ids": [],
    "page_ids": []
}, headers={"Authorization": f"Bearer {token}"})

print("STATUS:", response.status_code)
print("BODY:", response.text)
