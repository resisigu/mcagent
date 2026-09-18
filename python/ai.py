import json,math,os
class CombatAI:
 def __init__(self):
  self.range=3.0
  self.data_file=os.path.join(os.path.dirname(__file__),"learned_combat.json")
  self.learned=self.load()
  self.previous_health=None
  self.retreat_ticks=0
  self.last_target_id=None
  self.strafe_dir=1
 def load(self):
  try:
   with open(self.data_file,encoding="utf-8") as f:return json.load(f)
  except Exception:return {"attack_distance":3.0,"bow_distance":12.0,"samples":0}
 def step(self,state):
  p=state.get("player") or {}
  mobs=p.get("mobs") or []
  health=p.get("health")
  if health is not None:
   health=float(health)
   if self.previous_health is not None and health<self.previous_health-0.01:
    self.retreat_ticks=max(self.retreat_ticks,32)
   self.previous_health=health
  if not mobs:return self.stop(p)
  target=min(mobs,key=lambda m:float(m.get("distance",999)))
  x=float(target.get("x",0));y=float(target.get("y",0));z=float(target.get("z",0))
  horizontal=math.hypot(x,z)
  yaw=float(p.get("yaw",0));pitch=float(p.get("pitch",0))
  desired_yaw=math.degrees(math.atan2(-x,z))
  dyaw=(desired_yaw-yaw+180)%360-180
  yaw+=max(-30,min(30,dyaw))
  target_eye_y=y+0.9
  desired_pitch=-math.degrees(math.atan2(target_eye_y-1.62,max(.001,horizontal)))
  pitch+=max(-22,min(22,desired_pitch-pitch))
  held=str(p.get("heldItem","")).lower()
  bow="bow" in held or "crossbow" in held
  aim_ok=abs(((desired_yaw-yaw+180)%360)-180)<14 and abs(desired_pitch-pitch)<14
  if self.retreat_ticks>0:
   self.retreat_ticks-=1
   move=self.best_escape(mobs,prefer_back=True)
   return self.control_for_move(move,True,False,yaw,pitch,p.get("onGround",False))
  if bow:
   ideal=float(self.learned.get("bow_distance",12.0))
   if horizontal<5:
    move=self.best_escape(mobs,prefer_back=True)
    return self.control_for_move(move,True,False,yaw,pitch,p.get("onGround",False))
   forward=1 if horizontal>ideal+2 else (-0.35 if horizontal<ideal-3 else 0)
   use=aim_ok and horizontal<=ideal+2
   move=(forward,self.strafe(x,z))
   return self.control_for_move(move,False,use,yaw,pitch,False)
  ideal=float(self.learned.get("attack_distance",3.0))
  danger=horizontal<2.1 or self.enemy_threatens(target)
  if len(mobs)>=2:
   move=self.best_escape(mobs,prefer_back=False)
   if horizontal<=ideal+0.7 and aim_ok:
    move=(move[0]*0.55+(-z/max(.001,horizontal))*0.25,move[1]*0.55+(x/max(.001,horizontal))*0.25)
   return self.control_for_move(move,True,aim_ok,yaw,pitch,p.get("onGround",False))
  if danger:
   move=self.best_escape(mobs,prefer_back=True)
   return self.control_for_move(move,True,aim_ok and horizontal<=ideal+0.65,yaw,pitch,p.get("onGround",False))
  attack=horizontal<=ideal+0.65 and aim_ok
  if horizontal>ideal+0.65:
   return self.control_for_move((1,self.strafe(x,z)),True,False,yaw,pitch,False)
  return self.control_for_move((0.08,self.strafe(x,z)),False,attack,yaw,pitch,False)
 def enemy_threatens(self,m):
  d=float(m.get("distance",999))
  if d>3.5:return False
  vx=float(m.get("vx",0));vz=float(m.get("vz",0))
  x=float(m.get("x",0));z=float(m.get("z",0))
  speed=math.hypot(vx,vz)
  closing=(x*vx+z*vz)
  return int(m.get("hurtTime",0))>0 or (speed>0.08 and closing<-(speed*d*0.35))
 def best_escape(self,mobs,prefer_back=False):
  best=(0,0);best_score=-1e9
  backx=backz=0
  for m in mobs:
   x=float(m.get("x",0));z=float(m.get("z",0));d=max(.35,math.hypot(x,z));backx-=x/(d*d);backz-=z/(d*d)
  bl=math.hypot(backx,backz)
  if bl>0:backx/=bl;backz/=bl
  for i in range(16):
   a=2*math.pi*i/16
   dx=math.sin(a);dz=math.cos(a)
   score=0
   if prefer_back:score+=2.2*(dx*backx+dz*backz)
   min_dist=999
   for m in mobs:
    x=float(m.get("x",0));z=float(m.get("z",0));d=math.hypot(x,z);min_dist=min(min_dist,d)
    if d<0.01:continue
    away=(-x/d,-z/d)
    closing=(x*dx+z*dz)
    score+=1.8*(dx*away[0]+dz*away[1])/max(1,d)
    if closing<0:score+=0.8
    if d<3.0:score+=2.0*(1-d/3.0)
   score+=min_dist*0.35
   if score>best_score:best_score=score;best=(dx,dz)
  return best
 def control_for_move(self,move,sprint,attack,yaw,pitch,on_ground):
  dx,dz=move
  l=math.hypot(dx,dz)
  if l>.001:
   dx/=l;dz/=l
  return {"forward":max(-1,min(1,dz)),"strafe":max(-1,min(1,dx)),"jump":bool(on_ground and sprint),"sprint":sprint,"attack":attack,"use":False,"yaw":yaw,"pitch":pitch}
 def stop(self,p):
  return {"forward":0,"strafe":0,"jump":False,"sprint":False,"attack":False,"use":False,"yaw":p.get("yaw",0),"pitch":p.get("pitch",0)}
 def strafe(self,x,z):
  if abs(x)<0.2:return 0
  return -0.65 if x>0 else 0.65
