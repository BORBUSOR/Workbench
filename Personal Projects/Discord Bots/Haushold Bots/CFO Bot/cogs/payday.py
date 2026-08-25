import discord
from discord.ext import commands, tasks
import os
import datetime
from datetime import timedelta
import plaid
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from utils.database import get_all_plaid_tokens

# Plaid primary categories considered "Essential Living Costs"
ESSENTIAL_CATEGORIES = {
    "FOOD_AND_DRINK",
    "TRANSPORTATION",
    "RENT_AND_UTILITIES",
    "MEDICAL",
    "GENERAL_SERVICES"
}

class Payday(commands.Cog):
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
        
        self.saturday_sweep.start()

    def cog_unload(self):
        self.saturday_sweep.cancel()

    @tasks.loop(hours=24)
    async def saturday_sweep(self):
        now = datetime.datetime.now()
        
        # Only run on Saturdays (weekday 5)
        if now.weekday() != 5:
            return
            
        channel_id = os.getenv('CFO_CHANNEL_ID')
        if not channel_id:
            return
            
        channel = self.bot.get_channel(int(channel_id))
        if not channel:
            return

        guild_name = channel.guild.name
        tokens = get_all_plaid_tokens(guild_name)
        
        if not tokens:
            return

        # 30-day lookback for historical forecasting, 7-day lookback for fresh income
        history_start_date = (now - timedelta(days=30)).date()
        income_start_date = (now - timedelta(days=7)).date()
        end_date = now.date()
        
        total_income = 0.0
        essential_spending_last_week = 0.0
        income_sources = []
        essential_breakdown = {}
        
        # Dictionary to hold weekly essential buckets for historical forecasting (Week 0 to Week 4)
        weekly_essential_buckets = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0}
        
        for token in tokens:
            try:
                request = TransactionsGetRequest(
                    access_token=token,
                    start_date=history_start_date,
                    end_date=end_date,
                )
                response = self.plaid_client.transactions_get(request)
                
                for tx in response['transactions']:
                    amount = tx['amount']
                    tx_date = datetime.datetime.strptime(tx['date'], "%Y-%m-%d").date()
                    
                    # 1. Capture Income: Only look at the fresh pay period (Last 7 days)
                    if amount < 0 and tx_date >= income_start_date:
                        abs_amount = abs(amount)
                        merchant = tx['name'].upper()
                        if any(kw in merchant for kw in ["UNIVERSAL", "DISNEY", "TYPHOON", "ALEXANDRA", "JAIME"]):
                            total_income += abs_amount
                            income_sources.append(f"• **${abs_amount:,.2f}** from {tx['name']}")
                            
                    # 2. Capture Essential Spending: Look across the full 30 days for forecasting
                    elif amount > 0:
                        pf_cat = getattr(tx, 'personal_finance_category', None)
                        primary_cat = pf_cat.primary if pf_cat else "GENERAL_DETAILED"
                        
                        if primary_cat in ESSENTIAL_CATEGORIES:
                            # Assign transaction to a weekly bucket (0 = current week, 1 = last week, etc.)
                            days_ago = (end_date - tx_date).days
                            bucket_idx = min(days_ago // 7, 3)
                            weekly_essential_buckets[bucket_idx] += amount
                            
                            # Track strictly last week for the immediate breakdown report
                            if tx_date >= income_start_date:
                                essential_spending_last_week += amount
                                readable_cat = primary_cat.replace('_', ' ').title()
                                essential_breakdown[readable_cat] = essential_breakdown.get(readable_cat, 0.0) + amount

            except Exception as e:
                print(f"Error analyzing historical transactions: {e}")

        if total_income == 0:
            return

        # ==========================================
        # 📊 DYNAMIC HISTORICAL FORECASTING ENGINE
        # ==========================================
        weekly_totals = list(weekly_essential_buckets.values())
        avg_weekly_essentials = sum(weekly_totals) / len(weekly_totals) if weekly_totals else 0.0
        peak_weekly_essentials = max(weekly_totals) if weekly_totals else 0.0
        
        # Dynamic Volatility Buffer: Measures how much spending fluctuates above average historically
        historical_volatility_buffer = max(0.0, peak_weekly_essentials - avg_weekly_essentials)
        
        # Forecasted Target: Average baseline + adaptive historical spike protection
        forecasted_protected_amount = avg_weekly_essentials + historical_volatility_buffer
        net_surplus = total_income - forecasted_protected_amount

        embed = discord.Embed(
            title="🌊 Saturday Dynamic Waterfall & Forecast Sweep",
            description="Your weekly income has cleared. Essential expenses are protected using a rolling 30-day historical forecast:",
            color=discord.Color.brand_green(),
            timestamp=now
        )
        
        embed.add_field(name="💵 Total Weekly Income", value=f"**${total_income:,.2f}**", inline=True)
        embed.add_field(name="🛒 Last Week's Actual Spend", value=f"**${essential_spending_last_week:,.2f}**", inline=True)
        embed.add_field(name="📈 30-Day Forecasted Buffer", value=f"**-${forecasted_protected_amount:,.2f}**", inline=True)
        
        # Show breakdown of what was spent on essentials last week
        if essential_breakdown:
            breakdown_text = "\n".join([f"• **{cat}:** ${amt:,.2f}" for cat, amt in essential_breakdown.items()])
            embed.add_field(name="📋 Last Week's Essential Breakdown", value=breakdown_text, inline=False)

        # Step 2: Route the remaining surplus based on the dynamic forecast
        if net_surplus > 0:
            extra_debt_payoff = net_surplus * 0.70  # 70% of forecast-protected surplus to debt
            savings_buffer = net_surplus * 0.30     # 30% of forecast-protected surplus to savings
            
            embed.add_field(name="📈 Forecasted Surplus", value=f"**${net_surplus:,.2f}**", inline=False)
            embed.add_field(name="💳 Targeted Debt Relief", value=f"Safe to transfer **${extra_debt_payoff:,.2f}** to credit cards.", inline=False)
            embed.add_field(name="🎯 Savings Allocation", value=f"Safe to transfer **${savings_buffer:,.2f}** to goals.", inline=False)
        else:
            deficit = abs(net_surplus)
            embed.add_field(
                name="⚠️ High Historical Volatility Warning", 
                value=f"Forecasted essential needs exceeded income by **${deficit:,.2f}** based on recent spending spikes. **Hold off on extra debt transfers** until cash flow stabilizes!", 
                inline=False
            )
        
        await channel.send("📢 **Weekly Financial Forecast & Waterfall Analysis Ready:**", embed=embed)

    @saturday_sweep.before_loop
    async def before_saturday_sweep(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Payday(bot))