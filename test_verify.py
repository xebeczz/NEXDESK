import urllib.request, json, http.cookiejar

BASE = 'http://localhost:8000'
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
        resp = urllib.request.urlopen(r, timeout=10)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

# Login as User
s, r = req('POST', '/api/v1/auth/login', {'identifier': 'user@itdesk.io', 'password': 'User@12345'})
token = r.get('access_token', '')

# Check user tickets
s, r = req('GET', '/api/v1/tickets', token=token)
print('User tickets:', s)
for t in r.get('items', [])[:3]:
    print('  ' + t['ticket_no'] + ': ' + t['title'] + ' - ' + t['status'])

# Login as Admin
s, r = req('POST', '/api/v1/auth/login', {'identifier': 'admin@itdesk.io', 'password': 'Admin@12345'})
admin_token = r.get('access_token', '')

# Check admin tickets
s, r = req('GET', '/api/v1/tickets', token=admin_token)
print()
print('Admin tickets (first 3):')
for t in r.get('items', [])[:3]:
    print('  ' + t['ticket_no'] + ': ' + t['title'] + ' - ' + t['status'])

# Check settings API
s, r = req('GET', '/api/v1/settings', token=token)
print()
print('Settings API:', s)
if s == 200:
    print('Settings keys:', list(r.keys()))