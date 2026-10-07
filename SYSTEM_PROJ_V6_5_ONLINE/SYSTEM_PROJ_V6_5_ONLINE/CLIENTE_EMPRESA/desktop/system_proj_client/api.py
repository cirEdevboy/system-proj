from __future__ import annotations
import json, os, platform
from pathlib import Path
import httpx

APP_DIR=Path(os.getenv("APPDATA",Path.home()))/"SYSTEM_PROJ"; APP_DIR.mkdir(parents=True,exist_ok=True); CONFIG=APP_DIR/"config.json"

def load_config():
    if CONFIG.exists():
        try:return json.loads(CONFIG.read_text(encoding="utf-8"))
        except:pass
    return {"server_url":"http://localhost:8000"}

def save_config(data): CONFIG.write_text(json.dumps(data,indent=2),encoding="utf-8")

class ApiClient:
    def __init__(self):
        self.config=load_config(); self.base=self.config["server_url"].rstrip("/")+"/api/v1"; self.access=None; self.refresh=None; self.user=None; self.http=httpx.Client(timeout=30)
    def set_server(self,url): self.config["server_url"]=url.rstrip("/");save_config(self.config);self.base=self.config["server_url"]+"/api/v1"
    def _headers(self): return {"Authorization":f"Bearer {self.access}"} if self.access else {}
    def _request(self,method,path,**kwargs):
        kwargs.setdefault("headers",{});kwargs["headers"].update(self._headers());r=self.http.request(method,self.base+path,**kwargs)
        if r.status_code==401 and self.refresh:
            rr=self.http.post(self.base+"/auth/refresh",json={"refresh_token":self.refresh})
            if rr.is_success:self.access=rr.json()["access_token"];kwargs["headers"].update(self._headers());r=self.http.request(method,self.base+path,**kwargs)
        if not r.is_success:
            try:detail=r.json().get("detail",r.text)
            except:detail=r.text
            raise RuntimeError(detail)
        return r
    def get(self,path,**kw):return self._request("GET",path,**kw).json()
    def post(self,path,json=None,**kw):return self._request("POST",path,json=json,**kw).json()
    def put(self,path,json=None,**kw):return self._request("PUT",path,json=json,**kw).json()
    def login(self,login,password):
        d=self.post("/auth/login",json={"login":login,"password":password,"device_name":f"Desktop {platform.node()}"});self.access=d["access_token"];self.refresh=d["refresh_token"];self.user=d["user"];return d
    def register(self,data):return self.post("/auth/register",json=data)
    def claim_migrated(self,data):return self.post("/auth/claim-migrated",json=data)
    def download(self,path):return self._request("GET",path).content
    @property
    def websocket_url(self):
        url=self.config["server_url"].rstrip("/");scheme="wss" if url.startswith("https") else "ws";host=url.split("://",1)[1];return f"{scheme}://{host}/api/v1/ws?token={self.access}"
