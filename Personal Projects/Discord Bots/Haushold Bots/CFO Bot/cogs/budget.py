import discord
from discord.ext import commands
import os
import datetime
from datetime import timedelta
import plaid
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from utils.database import get_plaid_tokens, set_category_budget, get_category_budgets

class Budget(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        configuration = plaid.Configuration(
            host=plaid.Environment.Production,
            api_key={
                'clientId': os.getenv('PLAID_CLIENT_ID'),
                'secret': os.getenv('PLAID_SECRET'),
            }
        )
        api_client = plaid.ApiClient(configuration)
        self.plaid_client = plaid_api.PlaidApi(api_client)

    @commands.command(name="setbudget", help="Sets a monthly spending limit for a category. Usage: !setbudget FOOD_AND_DRINK 400")
    async def setbudget(self, ctx, category: str, limit_amount: float):
        guild_name = ctx.guild.name if ctx.guild else "DirectMessage"
        user_name = ctx.author.name
        
        set_category_budget(guild_name, user_name, category, limit_amount)
        await ctx.message.delete()
        await ctx.send(f"✅ Monthly budget for **{category.upper()}** set to **${limit_amount:,.2f}**.")

    @commands.command(name="budgets", help="Compares your actual monthly spending against your set budget limits.")
    async def budgets(self, ctx):
        guild_name = ctx.guild.name if ctx.guild else "DirectMessage"
        user_name = ctx.author.name
        
        budgets_map = get_category_budgets(guild_name, user_name)
        if not budgets_map:
            await ctx.send(f"❌ **{user_name}**, you haven't set any budgets yet! Use `!setbudget [category] [limit]`.")
            return

        tokens = get_plaid_tokens(guild_name, user_name)
        if not tokens:
            await ctx.send(f"❌ No Plaid tokens found for **{user_name}**.")
            return

        loading = await ctx.send("🔄 *Analyzing monthly spending against your budget limits...*")

        # Look back 30 days for current month spending
        end_date = datetime.datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        spending_totals = {}

        for token in tokens:
            try:
                request = TransactionsGetRequest(access_token=token, start_date=start_date, end_date=end_date)
                response = self.plaid_client.transactions_get(request)
                
                for tx in response['transactions']:
                    if tx['amount'] > 0: # Outflow
                        pf_cat = getattr(tx, 'personal_finance_category', None)
                        primary_cat = pf_cat.primary if pf_cat else "GENERAL_DETAILED"
                        spending_totals[primary_cat] = spending_totals.get(primary_cat, 0.0) + tx['amount']
            except Exception as e:
                print(f"Budget scan error: {e}")

        embed = discord.Embed(
            title=f"📊 {user_name}'s Monthly Budget Monitor",
            description="Tracking actual expenses vs. your set spending limits:",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )

        for cat, limit in budgets_map.items():
            spent = spending_totals.get(cat, 0.0)
            pct = (spent / limit) * 100 if limit > 0 else 0
            
            status = "🟢 On Track"
            if pct >= 100:
                status = "🚨 OVER BUDGET"
            elif pct >= 80:
                status = "⚠️ Nearing Limit"

            embed.add_field(
                name=f"{cat} ({status})",
                value=f"Spent: **${spent:,.2f}** / Limit: **${limit:,.2f}** (`{pct:.1f}%`)",
                inline=False
            )

        await loading.delete()
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Budget(bot))