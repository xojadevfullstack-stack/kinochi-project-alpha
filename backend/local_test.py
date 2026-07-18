from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_admin

app.dependency_overrides[get_current_admin] = lambda: {"sub": "1", "role": "superadmin"}

client = TestClient(app)
response = client.post("/api/v1/movies", json={
    "title": "Test Movie",
    "category_ids": [],
    "page_ids": []
})
print("STATUS:", response.status_code)
print("BODY:", response.text)
