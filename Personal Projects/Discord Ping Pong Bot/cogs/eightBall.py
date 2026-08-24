import discord
from discord.ext import commands
import random

class EightBall(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # The decorator changes and 'self' is added
    @commands.command()
    async def eightball(self, ctx, *, question):
        responses = [
            "It is certain.",
            "Without a doubt.",
            "Reply hazy, try again.",
            "Don't count on it.",
            "My sources say no."
        ]
        answer = random.choice(responses)

        await ctx.send(f'**Question:** {question}\n**Answer:** {answer}')

# The mandatory export function
async def setup(bot):
    await bot.add_cog(EightBall(bot))