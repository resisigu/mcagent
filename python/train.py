import json,time,urllib.request,os,statistics
BASE="http://127.0.0.1:18765"
DATA=os.path.join(os.path.dirname(__file__),"..","mineagent","datasets","combat.jsonl")
OUT=os.path.join(os.path.dirname(__file__),"learned_combat.json")
def request(path,method="GET",payload=None):
 data=None if payload is None else json.dumps(payload).encode()
 req=urllib.request.Request(BASE+path,data=data,method=method,headers={"Content-Type":"application/json"})
 with urllib.request.urlopen(req,timeout=1) as r:return json.loads(r.read().decode())
def learn():
 if not os.path.exists(DATA):return
 sword=[];bow=[]
 with open(DATA,encoding="utf-8") as f:
  for line in f:
   try:
    d=json.loads(line);p=d
    mobs=p.get("mobs") or []
    if not mobs:continue
    m=min(mobs,key=lambda x:x.get("distance",999));dist=float(m.get("distance",999));item=str(p.get("heldItem",""))
    if p.get("attack"):sword.append(dist)
    if p.get("use") and ("bow" in item or "crossbow" in item):bow.append(dist)
   except Exception:pass
 result={"attack_distance":round(statistics.median(sword),2) if sword else 3.0,"bow_distance":round(statistics.median(bow),2) if bow else 12.0,"sword_samples":len(sword),"bow_samples":len(bow)}
 with open(OUT,"w",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2)
 print("\nLearned:",result)
def main():
 print("MineAgent training mode: automatic control is OFF.")
 print("Play Minecraft yourself. Movement, aim, attack/use, target distance and nearby mobs are recorded.")
 while True:
  try:request("/health");break
  except Exception:time.sleep(1)
 request("/mode","POST",{"mode":"learning"})
 print("Training started. Press Ctrl+C to stop.")
 try:
  while True:
   state=request("/state");p=state.get("player") or {};mobs=p.get("mobs") or []
   if mobs:
    m=min(mobs,key=lambda x:x.get("distance",999))
    print(f"mob={m.get('type')} distance={m.get('distance',0):.2f} item={p.get('heldItem','')}   ",end="\r",flush=True)
   time.sleep(.1)
 except KeyboardInterrupt:print("\nTraining stopped.")
 finally:
  try:request("/mode","POST",{"mode":"off"})
  except Exception:pass
  learn()
if __name__=="__main__":main()
