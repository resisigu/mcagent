import json,time,urllib.request
from ai import AthleticsAI
BASE="http://127.0.0.1:18765"
def request(path,method="GET",payload=None):
 data=None if payload is None else json.dumps(payload).encode();req=urllib.request.Request(BASE+path,data=data,method=method,headers={"Content-Type":"application/json"})
 with urllib.request.urlopen(req,timeout=1) as r:return json.loads(r.read().decode())
def main():
 ai=AthleticsAI()
 while True:
  try:request("/health");break
  except Exception:time.sleep(1)
 request("/mode","POST",{"mode":"play"})
 try:
  while True:request("/control","POST",ai.step(request("/state")));time.sleep(.02)
 except KeyboardInterrupt:pass
 finally:
  try:request("/mode","POST",{"mode":"off"})
  except Exception:pass
if __name__=="__main__":main()
