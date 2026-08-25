import discord
from discord.ext import commands
import datetime

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping", help="Checks the bot's live response latency.")
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Bot latency is currently at `{latency}ms`.",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )
        await ctx.send(embed=embed)

    @commands.command(name="about", help="Displays information about the Household CFO Bot and its active systems.")
    async def about(self, ctx):
        embed = discord.Embed(
            title="🏛️ Household CFO & Financial Assistant",
            description="Your automated financial command center powered by Plaid, SQLite, and Discord.",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(
            name="🤖 Active Automated Systems", 
            value=(
                "• **Multi-Bank Plaid Sync:** Live balances & liabilities\n"
                "• **Saturday Waterfall Engine:** Dynamic income & essential spending protection\n"
                "• **Volatility Forecasting:** Adaptive safety buffers based on 30-day history\n"
                "• **Debt Avalanche Optimizer:** Automated high-interest debt payoff schedules\n"
                "• **Shared Goals & Budgets:** Real-time progress tracking and category alerts"
            ), 
            inline=False
        )
        
        embed.set_footer(text="Type `!help` to see a full list of available commands.")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))