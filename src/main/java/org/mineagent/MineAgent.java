package org.mineagent;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.fml.common.Mod;
@Mod(value=MineAgent.MOD_ID,dist=Dist.CLIENT)
public final class MineAgent {
 public static final String MOD_ID="mineagent";
 public MineAgent(){MineAgentClient.init();}
}
