import json,math,os
class CombatAI:
 def __init__(self):
  self.range=float(os.getenv("MINEAGENT_ATTACK_RANGE","3.0"))
  self.last_target=None
  self.data_file=os.path.join(os.path.dirname(__file__),"learned_combat.json")
  self.learned=self.load()
 def load(self):
  try:
   with open(self.data_file,encoding="utf-8") as f:return json.load(f)
  except Exception:return {"attack_distance":3.0,"samples":0}
 def save(self):
  with open(self.data_file,"w",encoding="utf-8") as f:json.dump(self.learned,f,ensure_ascii=False,indent=2)
 def step(self,state):
  p=state.get("player") or {}
  mobs=p.get("mobs") or []
  if not mobs:return {"forward":0,"strafe":0,"jump":False,"sprint":False,"attack":False,"yaw":p.get("yaw",0),"pitch":p.get("pitch",0)}
  target=min(mobs,key=lambda m:self.score(m))
  x=float(target.get("x",0));y=float(target.get("y",0));z=float(target.get("z",0));dist=math.sqrt(x*x+y*y+z*z)
  yaw=float(p.get("yaw",0));pitch=float(p.get("pitch",0))
  desired_yaw=math.degrees(math.atan2(-x,z))
  dyaw=(desired_yaw-yaw+180)%360-180
  yaw+=max(-15,min(15,dyaw))
  horizontal=math.hypot(x,z)
  desired_pitch=-math.degrees(math.atan2(y+0.8,max(0.001,horizontal)))
  pitch+=max(-12,min(12,desired_pitch-pitch))
  safe=self.learned.get("attack_distance",self.range)
  attack=dist<=safe+0.35 and abs(dyaw)<12
  if horizontal>safe+0.5:
   return {"forward":1,"strafe":self.strafe(x,z),"jump":False,"sprint":True,"attack":False,"yaw":yaw,"pitch":pitch}
  if horizontal<1.8:
   side=self.strafe(x,z)
   return {"forward":-0.25,"strafe":side,"jump":bool(p.get("onGround",False)),"sprint":False,"attack":attack,"yaw":yaw,"pitch":pitch}
  side=self.strafe(x,z)
  return {"forward":0.15,"strafe":side,"jump":False,"sprint":False,"attack":attack,"yaw":yaw,"pitch":pitch}
 def score(self,m):
  d=float(m.get("distance",999))
  return d+(0 if m.get("health",1)>0 else 10000)
 def strafe(self,x,z):
  return -0.65 if x>0 else 0.65
