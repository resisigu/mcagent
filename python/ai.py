import json,math,os
class CombatAI:
 def __init__(self):
  self.range=3.0
  self.data_file=os.path.join(os.path.dirname(__file__),"learned_combat.json")
  self.learned=self.load()
 def load(self):
  try:
   with open(self.data_file,encoding="utf-8") as f:return json.load(f)
  except Exception:return {"attack_distance":3.0,"bow_distance":12.0,"samples":0}
 def step(self,state):
  p=state.get("player") or {}
  mobs=p.get("mobs") or []
  if not mobs:return self.stop(p)
  target=min(mobs,key=lambda m:float(m.get("distance",999)))
  x=float(target.get("x",0));y=float(target.get("y",0));z=float(target.get("z",0))
  horizontal=math.hypot(x,z)
  yaw=float(p.get("yaw",0));pitch=float(p.get("pitch",0))
  desired_yaw=math.degrees(math.atan2(-x,z))
  dyaw=(desired_yaw-yaw+180)%360-180
  yaw+=max(-25,min(25,dyaw))
  target_eye_y=y+0.9
  eye_height=1.62
  desired_pitch=-math.degrees(math.atan2(target_eye_y-eye_height,max(.001,horizontal)))
  pitch+=max(-20,min(20,desired_pitch-pitch))
  held=str(p.get("heldItem","")).lower()
  bow="bow" in held or "crossbow" in held
  aim_ok=abs(((desired_yaw-yaw+180)%360)-180)<12 and abs(desired_pitch-pitch)<12
  if bow:
   ideal=float(self.learned.get("bow_distance",12.0))
   forward=1 if horizontal>ideal+2 else (-0.35 if horizontal<ideal-3 else 0)
   use=aim_ok and horizontal<=ideal+2
   return {"forward":forward,"strafe":self.strafe(x,z),"jump":False,"sprint":False,"attack":False,"use":use,"yaw":yaw,"pitch":pitch}
  ideal=float(self.learned.get("attack_distance",3.0))
  attack=horizontal<=ideal+0.55 and aim_ok
  if horizontal>ideal+0.65:
   return {"forward":1,"strafe":self.strafe(x,z),"jump":False,"sprint":True,"attack":False,"use":False,"yaw":yaw,"pitch":pitch}
  if horizontal<1.6:
   return {"forward":-0.2,"strafe":self.strafe(x,z),"jump":bool(p.get("onGround",False)),"sprint":False,"attack":attack,"use":False,"yaw":yaw,"pitch":pitch}
  return {"forward":0.05,"strafe":self.strafe(x,z),"jump":False,"sprint":False,"attack":attack,"use":False,"yaw":yaw,"pitch":pitch}
 def stop(self,p):
  return {"forward":0,"strafe":0,"jump":False,"sprint":False,"attack":False,"use":False,"yaw":p.get("yaw",0),"pitch":p.get("pitch",0)}
 def strafe(self,x,z):
  if abs(x)<0.2:return 0
  return -0.65 if x>0 else 0.65
