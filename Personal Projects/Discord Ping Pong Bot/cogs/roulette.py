import discord
from discord.ext import commands
import random
import asyncio

class Roulette(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Keeps track of guilds currently running a roulette game
        self.active_roulettes = set()

    @commands.command()
    async def roulette(self, ctx):
        # Prevent overlapping games in the same server
        if ctx.guild.id in self.active_roulettes:
            await ctx.send("⚠️ A roulette game is already in progress in this server! Wait for it to finish.")
            return

        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ You need to be in a voice channel to play VC roulette!")
            return

        vc = ctx.author.voice.channel
        humans = [member for member in vc.members if not member.bot]

        if not humans:
            await ctx.send("There is no one here to play with!")
            return

        # Pick a random victim
        victim = random.choice(humans)
        self.active_roulettes.add(ctx.guild.id)

        try:
            # Apply the server mute
            await victim.edit(mute=True)
            await ctx.send(f"🎯 **BANG!** {victim.mention} just got randomly server-muted for 10 seconds!")
            
            # Pause this specific command for 10 seconds
            await asyncio.sleep(10)
            
            # Check if they are still connected to a voice channel!
            if victim.voice:
                await victim.edit(mute=False)
                await ctx.send(f"🔊 10 seconds are up! {victim.mention} has been auto-unmuted.")
                
        except discord.Forbidden:
            await ctx.send(f"🎯 I tried to shoot {victim.mention}, but my permissions bounced off them!")
            
        finally:
            # Always remove the lock when finished
            self.active_roulettes.discard(ctx.guild.id)

# The mandatory export function
async def setup(bot):
    await bot.add_cog(Roulette(bot))