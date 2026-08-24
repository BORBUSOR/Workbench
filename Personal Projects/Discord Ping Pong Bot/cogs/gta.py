import discord
from discord.ext import commands
import os

# Pointing directly to your actual D: drive game scripts folder
GTA_SCRIPTS_PATH = r"D:\Grand Theft Auto V Legacy\scripts\gta_command.txt"

class GTA(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _send_help(self, ctx):
        """Helper method to send the help embed cleanly."""
        embed = discord.Embed(
            title="🎮 GTA V Mod Control Panel",
            description="Control the chaos in-game straight from Discord!",
            color=discord.Color.blurple()
        )
        embed.add_field(
            name="Available Commands",
            value="`!gta help` - Shows this help menu\n"
                  "`!gta random` - Triggers a random effect\n"
                  "`!gta gravity` - Activates low gravity\n"
                  "`!gta cows` - Spawns a cow stampede\n"
                  "`!gta rpg` - Gives everyone an RPG\n"
                  "`!gta speed` - Flings you across the map\n"
                  "`!gta car` - Spawns a vehicle / transforms yours\n"
                  "`!gta explosion` - Triggers a safe explosion\n"
                  "`!gta drunk` - Triggers drunk & cinematic mode",
            inline=False
        )
        await ctx.send(embed=embed)

    @commands.group(invoke_without_subcommand=True)
    async def gta(self, ctx):
        """Main GTA command group. Usage: !gta <effect>"""
        await self._send_help(ctx)

    @gta.command(name="help")
    async def gta_help(self, ctx):
        """Explicit help subcommand alias."""
        await self._send_help(ctx)

    @gta.command(name="random")
    async def gta_random(self, ctx):
        self._write_command("random")
        await ctx.send("🎲 Triggered a **random** effect in GTA V!")

    @gta.command(name="gravity")
    async def gta_gravity(self, ctx):
        self._write_command("gravity")
        await ctx.send("🪐 Activated **Low Gravity** in GTA V!")

    @gta.command(name="cows")
    async def gta_cows(self, ctx):
        self._write_command("cows")
        await ctx.send("🐄 Deployed a **Cow Stampede** in GTA V!")

    @gta.command(name="rpg")
    async def gta_rpg(self, ctx):
        self._write_command("rpg")
        await ctx.send("🚀 Activated **RPG Madness** in GTA V!")

    @gta.command(name="speed")
    async def gta_speed(self, ctx):
        self._write_command("speed")
        await ctx.send("💨 Applied an **Intense Speed Boost** in GTA V!")

    @gta.command(name="car")
    async def gta_car(self, ctx):
        self._write_command("car")
        await ctx.send("🚗 Spawned / Transformed a **Vehicle** in GTA V!")

    @gta.command(name="explosion")
    async def gta_explosion(self, ctx):
        self._write_command("explosion")
        await ctx.send("💥 Triggered an **Explosion** in GTA V!")

    @gta.command(name="drunk")
    async def gta_drunk(self, ctx):
        self._write_command("drunk")
        await ctx.send("🍸 Activated **Drunk & Cinematic Mode** in GTA V!")

    def _write_command(self, cmd: str):
        try:
            os.makedirs(os.path.dirname(GTA_SCRIPTS_PATH), exist_ok=True)
            with open(GTA_SCRIPTS_PATH, "w") as f:
                f.write(cmd)
        except Exception as e:
            print(f"Error writing GTA command file: {e}")

async def setup(bot):
    await bot.add_cog(GTA(bot))