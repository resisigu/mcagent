import json,time,urllib.request
BASE="http://127.0.0.1:18765"
def request(path,method="GET",payload=None):
 data=None if payload is None else json.dumps(payload).encode()
 req=urllib.request.Request(BASE+path,data=data,method=method,headers={"Content-Type":"application/json"})
 with urllib.request.urlopen(req,timeout=1) as r:return json.loads(r.read().decode())
def main():
 print("MineAgent training mode: automatic control is OFF.")
 print("Play Minecraft yourself. Movement, aim, attack, target distance and nearby mobs are recorded.")
 while True:
  try:request("/health");break
  except Exception:time.sleep(1)
 request("/mode","POST",{"mode":"learning"})
 print("Training started. Press Ctrl+C to stop.")
 try:
  while True:
   state=request("/state")
   p=state.get("player") or {}
   mobs=p.get("mobs") or []
   if mobs:
    nearest=min(mobs,key=lambda m:m.get("distance",999))
    print(f"mob={nearest.get('type')} distance={nearest.get('distance',0):.2f} attack={'yes' if nearest.get('distance',999)<=3.2 else 'no'}   ",end="\r",flush=True)
   time.sleep(.1)
 except KeyboardInterrupt:
  print("\nTraining stopped.")
 finally:
  try:request("/mode","POST",{"mode":"off"})
  except Exception:pass
if __name__=="__main__":main()
