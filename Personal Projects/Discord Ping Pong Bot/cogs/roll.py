import discord
from discord.ext import commands
import random

class Roll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # The decorator changes and 'self' is added
    @commands.command()
    async def roll(self, ctx, sides: int):
        # This rolls a random number between 1 and the number of sides
        result = random.randint(1, sides)
        if sides <= 0:
            await ctx.send("❌ Please provide a positive integer for the number of sides.")
            return
        await ctx.send(f'🎲 You rolled a {result}!')

# The mandatory export function
async def setup(bot):
    await bot.add_cog(Roll(bot))