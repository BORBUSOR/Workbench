import discord
from discord.ext import commands
import asyncio
import os

class Knock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def knock(self, ctx):
        # 1. Check if the person who typed the command is actually in a Voice Channel
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("🚪 You need to be in a voice channel so I can knock on your door!")
            return

        # 2. Get the specific channel they are sitting in
        target_channel = ctx.author.voice.channel

        # Check if knock.mp3 exists inside the cogs/sfx folder
        sfx_folder = os.path.join(os.path.dirname(__file__), 'sfx')
        sfx_path = os.path.join(sfx_folder, 'knock.mp3')
        
        if not os.path.exists(sfx_path):
            await ctx.send("❌ Error: `knock.mp3` could not be found inside the `cogs/sfx` folder!")
            return

        try:
            # 3. Check if the bot is already in a channel, and connect/move
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if vc and vc.is_connected():
                await vc.move_to(target_channel)
            else:
                vc = await target_channel.connect()

            # Stop any audio if the bot was already playing something
            if vc.is_playing():
                vc.stop()

            # 4. Play the audio file from the sfx folder with a volume cap
            vc.play(discord.FFmpegPCMAudio(sfx_path, options='-vn -af volume=0.3'))
            
            await ctx.send("🚪 *Knock knock...*")

            # 5. Wait patiently for the audio clip to finish
            while vc.is_playing():
                await asyncio.sleep(1)
                
            # 6. Cleanly disconnect
            await vc.disconnect()

        except Exception as e:
            # If anything breaks, it will tell you exactly why
            await ctx.send(f"⚠️ **Audio failed to play!** Error: `{e}`")
            if 'vc' in locals() and vc and vc.is_connected():
                await vc.disconnect()

async def setup(bot):
    await bot.add_cog(Knock(bot))