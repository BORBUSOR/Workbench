import discord
from discord.ext import commands
import os
import datetime
from datetime import timedelta
import plaid
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from utils.database import get_plaid_tokens

class Income(commands.Cog):
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

    @commands.command(name="income", help="Pulls recent income and paycheck deposits from your linked banks via Plaid.")
    async def income(self, ctx, days: int = 14):
        guild_name = ctx.guild.name if ctx.guild else "DirectMessage"
        user_name = ctx.author.name
        
        tokens = get_plaid_tokens(guild_name, user_name)
        if not tokens:
            await ctx.send(f"❌ **{user_name}**, you haven't linked any bank accounts yet! Use `!claimtoken` first.")
            return

        loading_msg = await ctx.send(f"🔄 *Scanning your bank accounts for recent income over the last {days} days...*")

        end_date = datetime.datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        total_income = 0.0
        income_items = []

        for token in tokens:
            try:
                request = TransactionsGetRequest(
                    access_token=token,
                    start_date=start_date,
                    end_date=end_date,
                )
                response = self.plaid_client.transactions_get(request)
                
                for tx in response['transactions']:
                    # Plaid inflows are negative amounts
                    if tx['amount'] < 0:
                        amount = abs(tx['amount'])
                        merchant = tx['name'].upper()
                        
                        # Filter for common income keywords and your specific income sources
                        if any(kw in merchant for kw in ["UNIVERSAL", "DISNEY", "TYPHOON", "ALEXANDRA", "JAIME", "PAYROLL", "DIRECT DEP", "DEPOSIT"]):
                            total_income += amount
                            income_items.append(f"• **${amount:,.2f}** from **{tx['name']}** on `{tx['date']}`")
                            
            except plaid.ApiException as e:
                print(f"Plaid API error fetching income: {e}")

        embed = discord.Embed(
            title=f"💵 {user_name}'s Income Report",
            description=f"Showing detected paycheck and income deposits over the last {days} days:",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )

        if income_items:
            embed.add_field(name="Detected Deposits", value="\n".join(income_items), inline=False)
            embed.add_field(name="Total Income", value=f"**${total_income:,.2f}**", inline=False)
        else:
            embed.add_field(name="No Income Found", value=f"No matching paycheck or deposit transactions were found in the last {days} days.", inline=False)

        await loading_msg.delete()
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Income(bot))