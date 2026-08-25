import discord
from discord.ext import commands
import os
import datetime
import plaid
from plaid.api import plaid_api
from plaid.model.transactions_recurring_get_request import TransactionsRecurringGetRequest
from utils.database import get_plaid_tokens

class Subscriptions(commands.Cog):
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

    @commands.command(name="subscriptions", help="Scans your linked accounts for recurring bills and subscriptions via Plaid.")
    async def subscriptions(self, ctx):
        guild_name = ctx.guild.name if ctx.guild else "DirectMessage"
        user_name = ctx.author.name
        
        tokens = get_plaid_tokens(guild_name, user_name)
        if not tokens:
            await ctx.send(f"❌ **{user_name}**, you haven't linked any bank accounts yet! Use `!claimtoken` first.")
            return

        loading_msg = await ctx.send(f"🔄 *Scanning your bank accounts for active recurring bills and subscriptions...*")

        sub_items = []
        total_monthly_cost = 0.0

        for token in tokens:
            try:
                request = TransactionsRecurringGetRequest(access_token=token)
                response = self.plaid_client.transactions_recurring_get(request)
                
                # Plaid returns outbound recurring streams (outflow streams)
                outflows = response.get('outflow_streams', [])
                for stream in outflows:
                    description = stream.get('description', 'Unknown Subscription')
                    last_amount = stream.get('last_amount', {}).get('amount', 0.0)
                    frequency = stream.get('frequency', 'UNKNOWN')
                    
                    # Estimate monthly cost based on frequency
                    monthly_cost = last_amount
                    if frequency == 'WEEKLY':
                        monthly_cost = last_amount * 4.33
                    elif frequency == 'BIWEEKLY':
                        monthly_cost = last_amount * 2.17
                    elif frequency == 'ANNUALLY':
                        monthly_cost = last_amount / 12.0
                        
                    total_monthly_cost += monthly_cost
                    sub_items.append(f"• **{description}**: `${last_amount:,.2f}` ({frequency.lower()}) ~ *Est. ${monthly_cost:,.2f}/mo*")
                            
            except plaid.ApiException as e:
                print(f"Plaid API error fetching recurring streams: {e}")

        embed = discord.Embed(
            title=f"📺 {user_name}'s Active Subscriptions & Bills",
            description="Auto-detected recurring outflow streams from your linked bank accounts:",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.now()
        )

        if sub_items:
            embed.add_field(name="Detected Recurring Streams", value="\n".join(sub_items), inline=False)
            embed.add_field(name="Estimated Total Monthly Burden", value=f"**${total_monthly_cost:,.2f} / month**", inline=False)
        else:
            embed.add_field(name="No Subscriptions Found", value="No recurring outflow streams were detected by Plaid across your connected banks.", inline=False)

        await loading_msg.delete()
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Subscriptions(bot))