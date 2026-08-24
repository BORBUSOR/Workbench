import discord
from discord.ext import commands
import os
import asyncio

class Boo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="boo")
    async def boo_command(self, ctx):
        # 1. Check if the user is in a voice channel
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ You must be in a voice channel to use the `!boo` command!")
            return

        target_channel = ctx.author.voice.channel

        try:
            # 2. Connect or move to the user's voice channel
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            
            if vc and vc.is_connected():
                await vc.move_to(target_channel)
            else:
                vc = await target_channel.connect()

            if vc.is_playing():
                vc.stop()

            # 3. Check for the audio file inside the cogs/sfx folder
            sfx_folder = os.path.join(os.path.dirname(__file__), 'sfx')
            sfx_path = os.path.join(sfx_folder, 'boo.mp3')

            if not os.path.exists(sfx_path):
                await ctx.send("❌ Error: `boo.mp3` could not be found inside the `cogs/sfx` folder!")
                await vc.disconnect()
                return

            # 4. Play the boo sound effect
            vc.play(discord.FFmpegPCMAudio(sfx_path, options='-vn -af volume=0.5'))
            await ctx.send("👻 **[Boo!]** 📉")

            # Wait until the audio finishes playing
            while vc.is_playing():
                await asyncio.sleep(1)

            # 5. Disconnect after playing
            await vc.disconnect()

        except Exception as e:
            await ctx.send(f"⚠️ **Audio failed to play!** Error: `{e}`")
            if 'vc' in locals() and vc and vc.is_connected():
                await vc.disconnect()

# The mandatory export function
async def setup(bot):
    await bot.add_cog(Boo(bot))