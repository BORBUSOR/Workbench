import discord
from discord.ext import commands
import os
import datetime
import plaid
from plaid.api import plaid_api
from plaid.model.liabilities_get_request import LiabilitiesGetRequest
from utils.database import get_plaid_tokens, set_debt, pay_debt, get_all_debts

class DebtTracker(commands.Cog):
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

    @commands.command(name="debts", help="Pulls live Plaid debts and combines them with manual cards.")
    async def debts(self, ctx):
        guild_name = ctx.guild.name if ctx.guild else "DirectMessage"
        user_name = ctx.author.name
        
        loading_msg = await ctx.send(f"🔄 *Gathering live Plaid liabilities and checking manual accounts...*")

        debt_items = []
        total_debt = 0.0

        # 1. Fetch Plaid Debts
        tokens = get_plaid_tokens(guild_name, user_name)
        if tokens:
            for token in tokens:
                try:
                    request = LiabilitiesGetRequest(access_token=token)
                    response = self.plaid_client.liabilities_get(request)
                    
                    liabilities = response.get('liabilities', {})
                    credit_liabilities = liabilities.get('credit', [])
                    accounts = {acc['account_id']: acc['name'] for acc in response.get('accounts', [])}

                    for cred in credit_liabilities:
                        account_id = cred.get('account_id')
                        card_name = accounts.get(account_id, 'Credit Card')
                        
                        aprs = cred.get('aprs', [])
                        apr_percentage = 0.0
                        for apr in aprs:
                            if apr.get('apr_type') == 'purchase_apr':
                                apr_percentage = apr.get('apr_percentage', 0.0)
                                break
                        
                        matched_acc = next((acc for acc in response.get('accounts', []) if acc['account_id'] == account_id), {})
                        current_balance = matched_acc.get('balances', {}).get('current', 0.0)
                        
                        if current_balance > 0:
                            total_debt += current_balance
                            debt_items.append(f"• **{card_name}** (Plaid): `${current_balance:,.2f}` | APR: `{apr_percentage:.2f}%`")
                except Exception as e:
                    print(f"Plaid liability skip: {e}")

        # 2. Fetch Manual Debts (now with custom APRs)
        manual_debts = get_all_debts(guild_name, user_name)
        for card_name, balance, apr in manual_debts:
            if balance > 0:
                total_debt += balance
                debt_items.append(f"• **{card_name}** (Manual): `${balance:,.2f}` | APR: `{apr:.2f}%`")

        embed = discord.Embed(
            title=f"💳 {user_name}'s Unified Debt Overview",
            description="Combined live Plaid sync and manual non-Plaid accounts:",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now()
        )

        if debt_items:
            embed.add_field(name="All Outstanding Balances", value="\n".join(debt_items), inline=False)
            embed.add_field(name="Total Combined Debt", value=f"**${total_debt:,.2f}**", inline=False)
        else:
            embed.add_field(name="No Debt Found", value="No active debts found from Plaid or your manual database.", inline=False)

        await loading_msg.delete()
        await ctx.send(embed=embed)

    @commands.command(name="debtplan", help="Generates an optimized Debt Avalanche payoff plan. Usage: !debtplan 300")
    async def debtplan(self, ctx, extra_cash_available: float):
        guild_name = ctx.guild.name if ctx.guild else "DirectMessage"
        user_name = ctx.author.name
        
        loading_msg = await ctx.send(f"🧮 *Running Debt Avalanche optimization engine for **${extra_cash_available:,.2f}** surplus...*")

        master_debts = []

        # Pull Plaid debts
        tokens = get_plaid_tokens(guild_name, user_name)
        if tokens:
            for token in tokens:
                try:
                    request = LiabilitiesGetRequest(access_token=token)
                    response = self.plaid_client.liabilities_get(request)
                    
                    liabilities = response.get('liabilities', {})
                    credit_liabilities = liabilities.get('credit', [])
                    accounts = {acc['account_id']: acc['name'] for acc in response.get('accounts', [])}

                    for cred in credit_liabilities:
                        account_id = cred.get('account_id')
                        card_name = accounts.get(account_id, 'Credit Card')
                        
                        aprs = cred.get('aprs', [])
                        apr_percentage = 0.0
                        for apr in aprs:
                            if apr.get('apr_type') == 'purchase_apr':
                                apr_percentage = apr.get('apr_percentage', 0.0)
                                break
                        
                        min_payment = cred.get('minimum_payment_amount') or 25.0
                        matched_acc = next((acc for acc in response.get('accounts', []) if acc['account_id'] == account_id), {})
                        current_balance = matched_acc.get('balances', {}).get('current', 0.0)
                        
                        if current_balance > 0:
                            master_debts.append({
                                'name': card_name,
                                'balance': current_balance,
                                'apr': apr_percentage,
                                'min_pay': min_payment
                            })
                except Exception as e:
                    print(f"Plaid plan skip: {e}")

        # Pull manual debts with their custom APRs
        manual_debts = get_all_debts(guild_name, user_name)
        for card_name, balance, apr in manual_debts:
            if balance > 0:
                if not any(d['name'].lower() == card_name.lower() for d in master_debts):
                    master_debts.append({
                        'name': f"{card_name} (Manual)",
                        'balance': balance,
                        'apr': apr,
                        'min_pay': 25.0
                    })

        if not master_debts:
            await loading_msg.delete()
            await ctx.send(f"❌ **{user_name}**, no debts found to optimize!")
            return

        # Sort by APR descending (Debt Avalanche Strategy)
        master_debts.sort(key=lambda x: x['apr'], reverse=True)
        
        plan_lines = []
        remaining_extra = extra_cash_available

        plan_lines.append(f"🎯 **Strategy:** Debt Avalanche (Highest APR First)\n")

        for debt in master_debts:
            allocation = debt['min_pay']
            note = f"Min Pay: ${debt['min_pay']:,.2f}"
            
            if remaining_extra > 0 and debt == master_debts[0]:
                extra_boost = remaining_extra
                allocation += extra_boost
                remaining_extra = 0.0
                note = f"🔥 **TARGET CARD** (Min Pay + **${extra_boost:,.2f}** extra surplus)"

            plan_lines.append(f"• **{debt['name']}** (APR: `{debt['apr']:.2f}%` | Bal: `${debt['balance']:,.2f}`)\n  ↳ Pay: **${allocation:,.2f}** ({note})")

        embed = discord.Embed(
            title=f"📊 {user_name}'s Optimized Debt Payoff Plan",
            description=f"Using your **${extra_cash_available:,.2f}** weekly surplus:",
            color=discord.Color.gold(),
            timestamp=datetime.datetime.now()
        )

        embed.add_field(name="Step-by-Step Payment Schedule", value="\n".join(plan_lines), inline=False)
        
        if remaining_extra > 0:
            embed.set_footer(text=f"🎉 All minimums met, target card fully cleared, with ${remaining_extra:,.2f} remaining surplus!")
        else:
            embed.set_footer(text="💡 Tip: Target card absorbs 100% of your available surplus until paid off.")

        await loading_msg.delete()
        await ctx.send(embed=embed)

    @commands.command(name="adddebt", help="Manually log a card with balance and APR. Usage: !adddebt Synchrony 450.00 29.99")
    async def adddebt(self, ctx, card_name: str, amount: float, apr: float = 24.99):
        guild_name = ctx.guild.name if ctx.guild else "DirectMessage"
        user_name = ctx.author.name
        
        set_debt(guild_name, user_name, card_name, amount, apr)
        await ctx.message.delete()
        await ctx.send(f"✅ **{user_name}**, manually logged **{card_name}** at **${amount:,.2f}** with an APR of **{apr:.2f}%**.")

    @commands.command(name="paydebt", help="Subtract a payment from a manual card. Usage: !paydebt Synchrony 50.00")
    async def paydebt(self, ctx, card_name: str, amount: float):
        guild_name = ctx.guild.name if ctx.guild else "DirectMessage"
        user_name = ctx.author.name
        
        success = pay_debt(guild_name, user_name, card_name, amount)
        if success:
            await ctx.send(f"✅ **{user_name}**, applied a **${amount:,.2f}** payment to **{card_name}**.")
        else:
            await ctx.send(f"❌ Could not find a manual card named **{card_name}**.")

async def setup(bot):
    await bot.add_cog(DebtTracker(bot))