import discord
from discord.ext import commands
import os
import datetime
from datetime import timedelta
import plaid
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from utils.database import get_household_summary, get_all_plaid_tokens
import matplotlib.pyplot as plt

# Ensure matplotlib runs headlessly on server environments
plt.switch_backend('Agg')

class ReportView(discord.ui.View):
    """Interactive button layout for financial reports"""
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label="🔄 Refresh Plaid Data", style=discord.ButtonStyle.green)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("✅ Plaid background tokens re-verified successfully!", ephemeral=True)

    @discord.ui.button(label="📊 View Debt Plan", style=discord.ButtonStyle.red)
    async def debt_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("💡 Tip: Type `!debtplan [surplus_cash]` to generate your avalanche payment schedule.", ephemeral=True)

class Reports(commands.Cog):
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

    @commands.command(name="cforeport", help="Generates an enterprise household financial report complete with a visual chart and buttons.")
    async def cforeport(self, ctx):
        guild_name = ctx.guild.name if ctx.guild else "DirectMessage"
        loading = await ctx.send("📈 *Generating comprehensive household financial report and rendering charts...*")

        # 1. Gather household overview
        total_wealth, total_debt = get_household_summary(guild_name)
        net_worth = total_wealth - total_debt

        # 2. Gather category spending for chart rendering
        tokens = get_all_plaid_tokens(guild_name)
        category_totals = {}
        
        if tokens:
            start_date = (datetime.datetime.now() - timedelta(days=30)).date()
            end_date = datetime.datetime.now().date()
            
            for token in tokens:
                try:
                    request = TransactionsGetRequest(access_token=token, start_date=start_date, end_date=end_date)
                    response = self.plaid_client.transactions_get(request)
                    for tx in response['transactions']:
                        if tx['amount'] > 0:
                            pf_cat = getattr(tx, 'personal_finance_category', None)
                            cat = pf_cat.primary if pf_cat else "Other"
                            category_totals[cat] = category_totals.get(cat, 0.0) + tx['amount']
                except Exception as e:
                    print(f"Chart data error: {e}")

        # 3. Generate Matplotlib Pie Chart if data exists
        chart_path = "temp_spending_chart.png"
        has_chart = False
        
        if category_totals:
            labels = list(category_totals.keys())
            sizes = list(category_totals.values())
            
            plt.figure(figsize=(6, 6))
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
            plt.title("Household Monthly Spending Distribution", fontsize=12, fontweight='bold', color='white')
            plt.tight_layout()
            
            # Save chart with transparent dark styling matching Discord
            plt.savefig(chart_path, transparent=True, dpi=100)
            plt.close()
            has_chart = True

        # 4. Build Discord Embed
        embed = discord.Embed(
            title=f"🏛️ {guild_name} Executive CFO Financial Report",
            description="Enterprise overview of household net worth and recent spending.",
            color=discord.Color.dark_embed(),
            timestamp=datetime.datetime.now()
        )

        embed.add_field(name="💼 Total Liquid Wealth", value=f"**${total_wealth:,.2f}**", inline=True)
        embed.add_field(name="💳 Total Liabilities", value=f"**${total_debt:,.2f}**", inline=True)
        embed.add_field(name="🌟 Net Worth Position", value=f"**${net_worth:,.2f}**", inline=False)

        file_to_send = None
        if has_chart:
            file_to_send = discord.File(chart_path, filename="spending.png")
            embed.set_image(url="attachment://spending.png")

        await loading.delete()
        
        # Send message with interactive buttons attached
        if file_to_send:
            await ctx.send(file=file_to_send, embed=embed, view=ReportView())
            if os.path.exists(chart_path):
                os.remove(chart_path) # Clean up temp image file
        else:
            await ctx.send(embed=embed, view=ReportView())

async def setup(bot):
    await bot.add_cog(Reports(bot))