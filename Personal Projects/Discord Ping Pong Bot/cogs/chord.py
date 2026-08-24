import discord
from discord.ext import commands
import random

class Chord(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # The decorator changes and 'self' is added
    @commands.command()
    async def chord(self, ctx):
        chords = [
            "C Major 7 (Cmaj7)", 
            "D minor 9 (Dm9)", 
            "G dominant 7 flat 9 (G7b9)", 
            "F sharp half-diminished (F#m7b5)"
        ]
        daily_practice = random.choice(chords)
        
        await ctx.send(f'🎷 Your practice chord for right now is: **{daily_practice}**')

# The mandatory export function
async def setup(bot):
    await bot.add_cog(Chord(bot))