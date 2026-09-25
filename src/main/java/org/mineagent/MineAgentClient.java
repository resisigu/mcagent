package org.mineagent;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.phys.Vec3;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import java.io.*;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.concurrent.Executors;
@EventBusSubscriber(modid=MineAgent.MOD_ID,value=Dist.CLIENT,bus=EventBusSubscriber.Bus.GAME)
public final class MineAgentClient {
 private static final int PORT=18765;
 private static volatile String mode="off";
 private static volatile Control control=Control.empty();
 private static int attackCooldown=0;
 private static volatile HttpServer server;
 private static Path datasetFile;
 private MineAgentClient(){}
 public static void init(){if(server!=null)return;try{server=HttpServer.create(new InetSocketAddress("127.0.0.1",PORT),0);server.createContext("/health",MineAgentClient::health);server.createContext("/state",MineAgentClient::state);server.createContext("/mode",MineAgentClient::setMode);server.createContext("/control",MineAgentClient::setControl);server.setExecutor(Executors.newCachedThreadPool());server.start();Path dir=Minecraft.getInstance().gameDirectory.toPath().resolve("mineagent").resolve("datasets");Files.createDirectories(dir);datasetFile=dir.resolve("combat.jsonl");}catch(IOException e){server=null;}}
 @SubscribeEvent public static void onClientTick(ClientTickEvent.Post event){Minecraft mc=Minecraft.getInstance();LocalPlayer p=mc.player;if(p==null)return;if("play".equals(mode))applyControl(mc);
 if(attackCooldown>0)attackCooldown--;if("learning".equals(mode))recordLearning(mc,p);}
 private static void applyControl(Minecraft mc){Control c=control;mc.options.keyUp.setDown(c.forward>.1);mc.options.keyDown.setDown(c.forward<-.1);mc.options.keyLeft.setDown(c.strafe<-.1);mc.options.keyRight.setDown(c.strafe>.1);mc.options.keyJump.setDown(c.jump);mc.options.keySprint.setDown(c.sprint);mc.options.keyAttack.setDown(false);
 if(c.eat()&&mc.player!=null){selectFood(mc.player);}
 if(c.attack&&attackCooldown<=0&&c.targetId()!=null){Entity target=mc.level.getEntity(c.targetId());if(target instanceof LivingEntity le&&le.isAlive()&&mc.gameMode!=null&&mc.player.distanceToSqr(le)<16.0){mc.gameMode.attack(mc.player,le);mc.player.swing(net.minecraft.world.InteractionHand.MAIN_HAND);attackCooldown=2;}}mc.options.keyUse.setDown(c.use||c.eat());LocalPlayer p=mc.player;if(p!=null){if(Float.isFinite(c.yaw))p.setYRot(c.yaw);if(Float.isFinite(c.pitch))p.setXRot(Math.max(-90f,Math.min(90f,c.pitch)));p.setSprinting(c.sprint);}}
 private static boolean hasFood(LocalPlayer p){for(int i=0;i<9;i++){var stack=p.getInventory().getItem(i);if(!stack.isEmpty()&&stack.getFoodProperties(p) != null)return true;}return false;}
 private static void selectFood(LocalPlayer p){for(int i=0;i<9;i++){var stack=p.getInventory().getItem(i);if(!stack.isEmpty()&&stack.isEdible()){p.getInventory().selected=i;return;}}}
 private static void releaseControls(Minecraft mc){mc.options.keyUp.setDown(false);mc.options.keyDown.setDown(false);mc.options.keyLeft.setDown(false);mc.options.keyRight.setDown(false);mc.options.keyJump.setDown(false);mc.options.keySprint.setDown(false);mc.options.keyAttack.setDown(false);mc.options.keyUse.setDown(false);}

 private static void recordLearning(Minecraft mc,LocalPlayer p){if(datasetFile==null)return;JsonObject o=baseState(mc,p);o.addProperty("forward",mc.options.keyUp.isDown()?1:(mc.options.keyDown.isDown()?-1:0));o.addProperty("strafe",mc.options.keyRight.isDown()?1:(mc.options.keyLeft.isDown()?-1:0));o.addProperty("jump",mc.options.keyJump.isDown());o.addProperty("sprint",mc.options.keySprint.isDown());o.addProperty("attack",mc.options.keyAttack.isDown());o.addProperty("use",mc.options.keyUse.isDown());o.addProperty("eat",false);try{Files.writeString(datasetFile,o+System.lineSeparator(),StandardCharsets.UTF_8,StandardOpenOption.CREATE,StandardOpenOption.APPEND);}catch(IOException ignored){}}
 private static JsonArray nearbyProjectiles(LocalPlayer p,double radius){JsonArray a=new JsonArray();for(Entity e:p.level().getEntities(p,p.getBoundingBox().inflate(radius),e->e instanceof Projectile && e.isAlive())){Vec3 d=e.position().subtract(p.position());Vec3 v=e.getDeltaMovement();JsonObject q=new JsonObject();q.addProperty("id",e.getId());q.addProperty("type",BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).toString());q.addProperty("x",d.x);q.addProperty("y",d.y);q.addProperty("z",d.z);q.addProperty("vx",v.x);q.addProperty("vy",v.y);q.addProperty("vz",v.z);q.addProperty("distance",Math.sqrt(d.x*d.x+d.y*d.y+d.z*d.z));a.add(q);}return a;}
 private static JsonObject baseState(Minecraft mc,LocalPlayer p){JsonObject o=new JsonObject();o.addProperty("time",System.currentTimeMillis());o.addProperty("x",p.getX());o.addProperty("y",p.getY());o.addProperty("z",p.getZ());o.addProperty("vx",p.getDeltaMovement().x);o.addProperty("vy",p.getDeltaMovement().y);o.addProperty("vz",p.getDeltaMovement().z);o.addProperty("yaw",p.getYRot());o.addProperty("pitch",p.getXRot());o.addProperty("onGround",p.onGround());o.addProperty("fallDistance",p.fallDistance);o.addProperty("health",p.getHealth());o.addProperty("maxHealth",p.getMaxHealth());o.addProperty("foodLevel",p.getFoodData().getFoodLevel());o.addProperty("saturation",p.getFoodData().getSaturationLevel());o.addProperty("hasFood",hasFood(p));o.addProperty("heldItem",BuiltInRegistries.ITEM.getKey(p.getMainHandItem().getItem()).toString());o.addProperty("attackStrength",p.getAttackStrengthScale(0.0F));o.add("mobs",nearbyMobs(p,12));o.add("projectiles",nearbyProjectiles(p,20));o.add("nearby",nearbyBlocks(p));return o;}
 private static JsonArray nearbyMobs(LocalPlayer p,double radius){JsonArray a=new JsonArray();for(Entity e:p.level().getEntities(p,p.getBoundingBox().inflate(radius),e->e instanceof Monster && e.isAlive())){Vec3 d=e.position().subtract(p.position());JsonObject m=new JsonObject();m.addProperty("id",e.getId());m.addProperty("type",BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).toString());m.addProperty("x",d.x);m.addProperty("y",d.y);m.addProperty("z",d.z);m.addProperty("distance",Math.sqrt(d.x*d.x+d.y*d.y+d.z*d.z));m.addProperty("health",e instanceof LivingEntity le ? le.getHealth() : 0);m.addProperty("maxHealth",e instanceof LivingEntity le ? le.getMaxHealth() : 0);m.addProperty("vx",e.getDeltaMovement().x);m.addProperty("vy",e.getDeltaMovement().y);m.addProperty("vz",e.getDeltaMovement().z);m.addProperty("hurtTime",e instanceof LivingEntity le ? le.hurtTime : 0);a.add(m);}return a;}
 private static JsonArray nearbyBlocks(LocalPlayer p){JsonArray a=new JsonArray();BlockPos c=p.blockPosition();for(int x=-4;x<=4;x++)for(int y=-2;y<=4;y++)for(int z=-4;z<=4;z++){BlockPos pos=c.offset(x,y,z);var state=p.level().getBlockState(pos);if(!state.isAir()){JsonObject b=new JsonObject();b.addProperty("x",x);b.addProperty("y",y);b.addProperty("z",z);b.addProperty("solid",state.isSolid());a.add(b);}}return a;}
 private static void health(HttpExchange e)throws IOException{respond(e,200,"{\"ok\":true,\"mode\":\""+mode+"\"}");}
 private static void state(HttpExchange e)throws IOException{if(!"GET".equalsIgnoreCase(e.getRequestMethod())){respond(e,405,"{\"error\":\"method\"}");return;}LocalPlayer p=Minecraft.getInstance().player;if(p==null){respond(e,200,"{\"player\":null,\"mode\":\""+mode+"\"}");return;}JsonObject o=baseState(Minecraft.getInstance(),p);o.addProperty("mode",mode);JsonObject pl=new JsonObject();for(String k:new String[]{"x","y","z","vx","vy","vz","yaw","pitch","onGround","health","maxHealth","foodLevel","saturation","hasFood","fallDistance","heldItem","attackStrength"})if(o.has(k))pl.add(k,o.get(k));pl.add("mobs",o.get("mobs"));pl.add("nearby",o.get("nearby"));JsonObject out=new JsonObject();out.addProperty("mode",mode);out.add("player",pl);out.add("projectiles",o.get("projectiles"));respond(e,200,out.toString());}
 private static void setMode(HttpExchange e)throws IOException{if(!"POST".equalsIgnoreCase(e.getRequestMethod())){respond(e,405,"{\"error\":\"method\"}");return;}try{String m=JsonParser.parseString(readBody(e)).getAsJsonObject().get("mode").getAsString().toLowerCase();if(!m.equals("off")&&!m.equals("learning")&&!m.equals("play"))throw new IllegalArgumentException();mode=m;if(m.equals("off"))releaseControls(Minecraft.getInstance());respond(e,200,"{\"ok\":true,\"mode\":\""+mode+"\"}");}catch(Exception ex){respond(e,400,"{\"error\":\"invalid mode\"}");}}
 private static void setControl(HttpExchange e)throws IOException{if(!"POST".equalsIgnoreCase(e.getRequestMethod())){respond(e,405,"{\"error\":\"method\"}");return;}try{JsonObject o=JsonParser.parseString(readBody(e)).getAsJsonObject();LocalPlayer p=Minecraft.getInstance().player;float yaw=(float)(o.has("yaw")?o.get("yaw").getAsDouble():(p==null?0:p.getYRot()));float pitch=(float)(o.has("pitch")?o.get("pitch").getAsDouble():(p==null?0:p.getXRot()));control=new Control(o.has("forward")?o.get("forward").getAsDouble():0,o.has("strafe")?o.get("strafe").getAsDouble():0,o.has("jump")&&o.get("jump").getAsBoolean(),o.has("sprint")&&o.get("sprint").getAsBoolean(),o.has("attack")&&o.get("attack").getAsBoolean(),o.has("use")&&o.get("use").getAsBoolean(),o.has("eat")&&o.get("eat").getAsBoolean(),yaw,pitch,o.has("targetId")&&!o.get("targetId").isJsonNull()?o.get("targetId").getAsInt():null);respond(e,200,"{\"ok\":true}");}catch(Exception ex){respond(e,400,"{\"error\":\"invalid control\"}");}}
 private static String readBody(HttpExchange e)throws IOException{try(InputStream in=e.getRequestBody()){return new String(in.readAllBytes(),StandardCharsets.UTF_8);}}
 private static void respond(HttpExchange e,int status,String body)throws IOException{byte[] b=body.getBytes(StandardCharsets.UTF_8);e.getResponseHeaders().set("Content-Type","application/json; charset=utf-8");e.getResponseHeaders().set("Access-Control-Allow-Origin","*");e.sendResponseHeaders(status,b.length);try(OutputStream out=e.getResponseBody()){out.write(b);}}
 private record Control(double forward,double strafe,boolean jump,boolean sprint,boolean attack,boolean use,boolean eat,float yaw,float pitch,Integer targetId){static Control empty(){return new Control(0,0,false,false,false,false,false,Float.NaN,Float.NaN,null);}}
}
