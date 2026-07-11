import urllib.request
import urllib.error

req = urllib.request.Request('https://kinochi-project-alpha.onrender.com/api/v1/auth/login', method='POST', data=b'{"email":"admin@kinochi.uz","password":"admin123"}', headers={'Content-Type':'application/json'})
try:
    res = urllib.request.urlopen(req)
    print("Code:", res.getcode())
    print("Headers:", res.headers)
except urllib.error.HTTPError as e:
    print("Code:", e.code)
    print("Headers:", e.headers)
