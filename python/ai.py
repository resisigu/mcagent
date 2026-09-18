import json,math,os
class CombatAI:
 def __init__(self):
  self.range=3.0
  self.data_file=os.path.join(os.path.dirname(__file__),"learned_combat.json")
  self.learned=self.load()
  self.previous_health=None
  self.retreat_ticks=0
  self.jump_attack_ticks=0
  self.last_target_id=None
  self.last_attack_time=0
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
   if self.previous_health is not None and health<self.previous_health-0.01:self.retreat_ticks=max(self.retreat_ticks,32)
   self.previous_health=health
  if not mobs:return self.stop(p)
  target=min(mobs,key=lambda m:float(m.get("distance",999)))
  x=float(target.get("x",0));y=float(target.get("y",0));z=float(target.get("z",0))
  horizontal=math.hypot(x,z)
  yaw=float(p.get("yaw",0));pitch=float(p.get("pitch",0))
  desired_yaw=math.degrees(math.atan2(-x,z))
  dyaw=(desired_yaw-yaw+180)%360-180
  yaw+=max(-30,min(30,dyaw))
  desired_pitch=-math.degrees(math.atan2(y+0.9-1.62,max(.001,horizontal)))
  pitch+=max(-22,min(22,desired_pitch-pitch))
  held=str(p.get("heldItem","")).lower()
  bow="bow" in held or "crossbow" in held
  aim_ok=abs(((desired_yaw-yaw+180)%360)-180)<14 and abs(desired_pitch-pitch)<14
  nearby_count=sum(1 for m in mobs if float(m.get("distance",999))<=3.5)
  if self.retreat_ticks>0:
   self.retreat_ticks-=1
   move=self.best_escape(mobs,True)
   return self.control_for_move(move,True,False,yaw,pitch,p.get("onGround",False))
  if bow:
   ideal=float(self.learned.get("bow_distance",12.0))
   if horizontal<5:
    return self.control_for_move(self.best_escape(mobs,True),True,False,yaw,pitch,p.get("onGround",False))
   return self.control_for_move((1 if horizontal>ideal+2 else (-0.35 if horizontal<ideal-3 else 0),self.strafe(x,z)),False,aim_ok and horizontal<=ideal+2,yaw,pitch,False,use=True)
  ideal=float(self.learned.get("attack_distance",3.0))
  multi=nearby_count>=2
  if multi:
   # Multiple mobs close together: favor a charged sweep hit instead of jumping.
   move=self.best_escape(mobs,False)
   attack=aim_ok and horizontal<=3.1 and self.attack_ready(p)
   return self.control_for_move(move,False,attack,yaw,pitch,p.get("onGround",False))
  if horizontal<2.1 and self.enemy_threatens(target):
   return self.control_for_move(self.best_escape(mobs,True),True,False,yaw,pitch,p.get("onGround",False))
  # Default single-target behavior: jump, then strike while falling for a critical.
  if horizontal<=ideal+0.55 and aim_ok:
   if bool(p.get("onGround",False)) and self.jump_attack_ticks<=0:
    self.jump_attack_ticks=12
    return self.control_for_move((0.15,self.strafe(x,z)),False,False,yaw,pitch,True)
   if self.jump_attack_ticks>0:
    self.jump_attack_ticks-=1
    falling=float(p.get("fallDistance",0))>0.02
    if falling:
     self.jump_attack_ticks=0
     return self.control_for_move((0.05,self.strafe(x,z)),False,self.attack_ready(p),yaw,pitch,False)
    return self.control_for_move((0.08,self.strafe(x,z)),False,False,yaw,pitch,False)
  if horizontal>ideal+0.65:
   return self.control_for_move((1,self.strafe(x,z)),True,False,yaw,pitch,False)
  return self.control_for_move((0.05,self.strafe(x,z)),False,self.attack_ready(p) and aim_ok,yaw,pitch,False)
 def attack_ready(self,p):
  return True
 def enemy_threatens(self,m):
  d=float(m.get("distance",999));vx=float(m.get("vx",0));vz=float(m.get("vz",0));x=float(m.get("x",0));z=float(m.get("z",0))
  speed=math.hypot(vx,vz);closing=x*vx+z*vz
  return d<=3.5 and (int(m.get("hurtTime",0))>0 or (speed>0.08 and closing<-(speed*d*0.35)))
 def best_escape(self,mobs,prefer_back=False):
  best=(0,0);best_score=-1e9
  bx=bz=0
  for m in mobs:
   x=float(m.get("x",0));z=float(m.get("z",0));d=max(.35,math.hypot(x,z));bx-=x/(d*d);bz-=z/(d*d)
  bl=math.hypot(bx,bz)
  if bl:bx/=bl;bz/=bl
  for i in range(24):
   a=2*math.pi*i/24;dx=math.sin(a);dz=math.cos(a);score=0
   if prefer_back:score+=2.5*(dx*bx+dz*bz)
   min_d=999
   for m in mobs:
    x=float(m.get("x",0));z=float(m.get("z",0));d=math.hypot(x,z);min_d=min(min_d,d)
    if d<.01:continue
    score+=2.0*((dx*(-x/d)+dz*(-z/d))/max(1,d))
    closing=x*dx+z*dz
    if closing<0:score+=.7
    if d<3:score+=2.2*(1-d/3)
   score+=min_d*.4
   if score>best_score:best_score=score;best=(dx,dz)
  return best
 def control_for_move(self,move,sprint,attack,yaw,pitch,on_ground,use=False):
  dx,dz=move;l=math.hypot(dx,dz)
  if l>.001:dx/=l;dz/=l
  return {"forward":max(-1,min(1,dz)),"strafe":max(-1,min(1,dx)),"jump":bool(on_ground and sprint),"sprint":sprint,"attack":attack,"use":use,"yaw":yaw,"pitch":pitch}
 def stop(self,p):
  return {"forward":0,"strafe":0,"jump":False,"sprint":False,"attack":False,"use":False,"yaw":p.get("yaw",0),"pitch":p.get("pitch",0)}
 def strafe(self,x,z):
  if abs(x)<.2:return 0
  return -.65 if x>0 else .65
