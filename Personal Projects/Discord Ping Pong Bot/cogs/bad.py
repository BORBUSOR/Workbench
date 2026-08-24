import discord
from discord.ext import commands
import random
import asyncio
import os

class Bad(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="bad")
    async def bad_command(self, ctx):
        # 1. Check if the user is in a voice channel
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ You must be in a voice channel to use the `!bad` command!")
            return

        target_channel = ctx.author.voice.channel

        # Define the four sound files
        four_files = [
            "izerocooii.mp3",
            "bad-to-the-bone-skeleton.mp3",
            "bad-to-the-bone.mp3",
            "bad-to-the-bone-meme.mp3"
        ]

        # Pick one of the four files randomly
        chosen_file = random.choice(four_files)
        
        # Point directly to the sfx folder inside the cogs directory
        sfx_folder = os.path.join(os.path.dirname(__file__), 'sfx')
        sfx_path = os.path.join(sfx_folder, chosen_file)

        # 2. Check if the file exists
        if not os.path.exists(sfx_path):
            await ctx.send(f"❌ Error: `{chosen_file}` could not be found inside the `cogs/sfx` folder!")
            return

        try:
            # 3. Connect or move to the user's voice channel
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            
            if vc and vc.is_connected():
                await vc.move_to(target_channel)
            else:
                vc = await target_channel.connect()

            if vc.is_playing():
                vc.stop()

            # 4. Play the randomly selected audio file
            vc.play(discord.FFmpegPCMAudio(sfx_path, options='-vn -af volume=0.5'))
            await ctx.send(f"🔊 Playing SFX: **{chosen_file}** 🎸")

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
    await bot.add_cog(Bad(bot))