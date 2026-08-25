import discord
from discord.ext import commands
import datetime
from utils.database import set_goal, add_to_goal, get_all_goals

class Goals(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="goals", help="Displays progress bars for all active household savings goals.")
    async def goals(self, ctx):
        guild_name = ctx.guild.name if ctx.guild else "DirectMessage"
        
        goal_rows = get_all_goals(guild_name)
        
        embed = discord.Embed(
            title="🎯 Household Savings Goals",
            description="Live progress tracking for shared goals:",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )

        if not goal_rows:
            embed.add_field(name="No Goals Found", value="Use `!setgoal [name] [target]` to create one!")
        else:
            for goal_name, target, current in goal_rows:
                percentage = min(100.0, (current / target) * 100) if target > 0 else 0
                
                # Build a visual progress bar (10 blocks long)
                filled_blocks = int(percentage // 10)
                bar = "█" * filled_blocks + "░" * (10 - filled_blocks)
                
                embed.add_field(
                    name=f"🏆 {goal_name}",
                    value=f"`{bar}` **{percentage:.1f}%**\n💰 `${current:,.2f}` / `${target:,.2f}`",
                    inline=False
                )

        await ctx.send(embed=embed)

    @commands.command(name="setgoal", help="Creates or updates a shared savings goal. Usage: !setgoal EmergencyFund 2000")
    async def setgoal(self, ctx, goal_name: str, target_amount: float):
        guild_name = ctx.guild.name if ctx.guild else "DirectMessage"
        
        set_goal(guild_name, goal_name, target_amount)
        await ctx.message.delete()
        await ctx.send(f"✅ Shared goal **{goal_name}** set with a target of **${target_amount:,.2f}**!")

    @commands.command(name="addgoal", help="Adds funds to a shared goal. Usage: !addgoal EmergencyFund 150")
    async def addgoal(self, ctx, goal_name: str, amount: float):
        guild_name = ctx.guild.name if ctx.guild else "DirectMessage"
        
        success = add_to_goal(guild_name, goal_name, amount)
        if success:
            await ctx.send(f"🎉 Successfully added **${amount:,.2f}** to **{goal_name}**!")
        else:
            await ctx.send(f"❌ Could not find a goal named **{goal_name}**.")

async def setup(bot):
    await bot.add_cog(Goals(bot))