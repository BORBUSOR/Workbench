import discord
from discord.ext import commands

py_version = "custom"

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Remove the default help command so we can override it cleanly
        self.bot.remove_command('help')

    @commands.command(name="help", help="Shows all categories or details for a specific category.")
    async def help(self, ctx, *, category_name: str = None):
        prefix = "!"
        
        # 1. If a specific category/cog is requested
        if category_name:
            matched_cog = None
            for cog_name, cog in self.bot.cogs.items():
                if cog_name.lower() == category_name.lower():
                    matched_cog = cog
                    break
            
            if not matched_cog:
                await ctx.send(f"❌ Category **'{category_name}'** not found. Type `{prefix}help` to see all categories.")
                return

            embed = discord.Embed(
                title=f"📁 Category: {matched_cog.__qualified_name__}",
                description=f"Commands available under this category:",
                color=discord.Color.blue()
            )

            for command in matched_cog.get_commands():
                if not command.hidden:
                    help_text = command.help or "No description provided."
                    embed.add_field(
                        name=f"{prefix}{command.name}",
                        value=help_text,
                        inline=False
                    )
            
            embed.set_footer(text=f"Use {prefix}help for the main menu.")
            await ctx.send(embed=embed)
            return

        # 2. Main Help Menu (Lists all categories neatly)
        embed = discord.Embed(
            title="🏛️ Household CFO Bot - Command Directory",
            description=f"Type `{prefix}help [Category Name]` (e.g., `{prefix}help DebtTracker`) to view detailed commands for that section.",
            color=discord.Color.dark_embed()
        )

        for cog_name, cog in sorted(self.bot.cogs.items()):
            commands_list = [f"`{prefix}{cmd.name}`" for cmd in cog.get_commands() if not cmd.hidden]
            if commands_list:
                embed.add_field(
                    name=f"📂 {cog_name}",
                    value=", ".join(commands_list),
                    inline=False
                )

        embed.set_footer(text="All systems operational and synced with Plaid.")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))