import urllib.request, json

# Test backend health
r = urllib.request.urlopen('http://localhost:8000/health', timeout=5)
print('Backend health:', r.read().decode())

# Test login
data = json.dumps({'identifier': 'user@itdesk.io', 'password': 'User@12345'}).encode()
req = urllib.request.Request('http://localhost:8000/api/v1/auth/login', data=data, headers={'Content-Type': 'application/json'}, method='POST')
r = urllib.request.urlopen(req, timeout=5)
result = json.loads(r.read().decode())
print('User login:', 'OK' if result.get('access_token') else 'FAIL')
token = result.get('access_token', '')

# Test AI chat
data = json.dumps({'message': 'Hi'}).encode()
req = urllib.request.Request('http://localhost:8000/api/v1/chat/sessions', data=data, headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token}, method='POST')
r = urllib.request.urlopen(req, timeout=5)
session = json.loads(r.read().decode())
print('Chat session:', session.get('id', 'FAIL'))
session_id = session.get('id')

data = json.dumps({'message': 'My laptop Wi-Fi is not working.'}).encode()
req = urllib.request.Request('http://localhost:8000/api/v1/chat/sessions/' + session_id + '/messages', data=data, headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token}, method='POST')
r = urllib.request.urlopen(req, timeout=30)
content = r.read().decode()
print('AI streaming response (first 300 chars):')
print(content[:300])