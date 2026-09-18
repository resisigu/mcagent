import math
class AthleticsAI:
 def step(self,state):
  p=state.get("player") or {};yaw=float(p.get("yaw",0));pitch=float(p.get("pitch",0));target=self.target(p.get("nearby",[]))
  if target is None:return {"forward":1,"strafe":0,"jump":False,"sprint":True,"yaw":yaw,"pitch":pitch}
  tx,_,tz=target;desired=math.degrees(math.atan2(-tx,tz));delta=(desired-yaw+180)%360-180;yaw+=max(-12,min(12,delta));dist=math.hypot(tx,tz)
  return {"forward":1,"strafe":0,"jump":bool(p.get("onGround",False) and dist>2.2),"sprint":True,"yaw":yaw,"pitch":pitch}
 def target(self,nearby):
  c=[]
  for b in nearby:
   if not b.get("solid"):continue
   x,y,z=int(b["x"]),int(b["y"]),int(b["z"]);d=math.hypot(x,z)
   if 1.5<=d<=5.5 and 0<=y<=3:c.append((d,-y,x,y,z))
  if not c:return None
  _,_,x,y,z=min(c);return x+.5,y+1,z+.5
