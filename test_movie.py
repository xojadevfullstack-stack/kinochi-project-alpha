import urllib.request
import json
import urllib.error

url = 'https://kinochi-project-alpha.onrender.com/api/v1/movies'
headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzg0MzkyMjcwLCJ0eXBlIjoiYWNjZXNzIiwiZW1haWwiOiJhZG1pbkBraW5vY2hpLnV6Iiwicm9sZSI6InN1cGVyYWRtaW4ifQ._R4uB0sBnojpWkAKNffVUoZ1qtDnzoJrsGKvKdcgA3s',
    'Content-Type': 'application/json'
}
data = json.dumps({'title': 'Test Movie', 'category_ids': [], 'page_ids': []}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers=headers, method='POST')
try:
    with urllib.request.urlopen(req) as f:
        print(f.status, f.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(e.code, e.read().decode('utf-8'))
