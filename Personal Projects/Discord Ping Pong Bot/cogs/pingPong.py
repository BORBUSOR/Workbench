import discord
from discord.ext import commands

# 1. Create a class for your command
class PingPong(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 2. YOUR ORIGINAL CODE GOES HERE
    # Notice the decorator is now @commands.command() 
    # and 'self' is added inside the parentheses
    @commands.command()
    async def ping(self, ctx):
        await ctx.send('Pong! 🏓')

# 3. This is the mandatory "export" function so your main file can read this one
async def setup(bot):
    await bot.add_cog(PingPong(bot))