import urllib.request, json, http.cookiejar

BASE = 'http://localhost:8000'

# Create cookie jar for session
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
urllib.request.install_opener(opener)

def req(method, path, data=None, token=None):
    url = BASE + path
    body = json.dumps(data).encode() if data else None
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=30)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

# 1. Login as User
print('=== Login as User ===')
s, r = req('POST', '/api/v1/auth/login', {'identifier': 'user@itdesk.io', 'password': 'User@12345'})
print(f'Status: {s}')
token = r.get('access_token', '')
print(f'Token: {token[:30]}...' if token else 'NO TOKEN')

# 2. Create chat session
print('\n=== Create Chat Session ===')
s, r = req('POST', '/api/v1/chat/sessions', {}, token=token)
print(f'Status: {s}')
session_id = r.get('id', '')
print(f'Session ID: {session_id}')

# 3. Send message "Hi" via the streaming endpoint
print('\n=== Send "Hi" (streaming) ===')
url = f'{BASE}/api/v1/chat/sessions/{session_id}/messages'
body = json.dumps({'message': 'Hi'}).encode()
headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token}
r = urllib.request.Request(url, data=body, headers=headers, method='POST')

print('Streaming response:')
try:
    resp = urllib.request.urlopen(r, timeout=30)
    for line in resp:
        line = line.decode()
        if line.startswith('data:'):
            print('  ', line.strip())
except urllib.error.HTTPError as e:
    print(f'Error: {e.code} - {e.read().decode()}')

# 4. Test "My laptop Wi-Fi is not working."
print('\n=== Send "My laptop Wi-Fi is not working." ===')
body = json.dumps({'message': "My laptop Wi-Fi is not working."}).encode()
r = urllib.request.Request(url, data=body, headers=headers, method='POST')

print('Streaming response:')
try:
    resp = urllib.request.urlopen(r, timeout=30)
    for line in resp:
        line = line.decode()
        if line.startswith('data:'):
            print('  ', line.strip())
except urllib.error.HTTPError as e:
    print(f'Error: {e.code} - {e.read().decode()}')

print('\n=== Test complete ===')