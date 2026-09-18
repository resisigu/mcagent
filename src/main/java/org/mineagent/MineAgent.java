package org.mineagent;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.loading.FMLEnvironment;
import net.neoforged.fml.DistExecutor;
import net.neoforged.api.distmarker.Dist;
@Mod(MineAgent.MOD_ID)
public final class MineAgent {
 public static final String MOD_ID="mineagent";
 public MineAgent(ModContainer container){if(FMLEnvironment.dist==Dist.CLIENT)DistExecutor.unsafeRunWhenOn(Dist.CLIENT,()->MineAgentClient::init);}
}
