import urllib.request, json, http.cookiejar
BASE="http://127.0.0.1:8000"
cj=http.cookiejar.CookieJar()
def req(m,p,data=None,tok=None):
    h={"Content-Type":"application/json"}
    if tok: h["Authorization"]=f"Bearer {tok}"
    b=json.dumps(data).encode() if data is not None else None
    r=urllib.request.Request(BASE+p,data=b,headers=h,method=m)
    cj.add_cookie_header(r)
    try:
        resp=urllib.request.urlopen(r,timeout=10); return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e: return e.code, e.read().decode()
st,body=req("POST","/api/v1/auth/login",{"identifier":"admin@itdesk.io","password":"Admin@12345"})
tok=json.loads(body)["access_token"]
tid="14a48033-3929-423f-8abc-61b333a1459b"
st,body=req("GET",f"/api/v1/tickets/{tid}",tok=tok)
d=json.loads(body)
print("assigned_to_id:", repr(d.get("assigned_to_id")))
print("assigned_to:", d.get("assigned_to"))
