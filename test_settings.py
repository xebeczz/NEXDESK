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
print('Login:', s)
token = r.get('access_token', '')

# Test settings endpoint
s, r = req('GET', '/api/v1/settings', token=token)
print('Settings:', s)
if s == 200:
    print('Settings keys:', list(r.keys()))
    user = r.get('user', {})
    print('User full_name:', user.get('full_name'))
    notif_prefs = r.get('notification_preferences', {})
    print('Notification prefs keys:', list(notif_prefs.keys()))
    security = r.get('security_settings', {})
    print('Security settings:', security)