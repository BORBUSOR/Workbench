import discord
from discord.ext import commands
import os
import plaid
from plaid.api import plaid_api
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from utils.database import add_plaid_token, get_plaid_tokens

class Bank(commands.Cog):
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
        self.client = plaid_api.PlaidApi(api_client)

    @commands.command(name="claimtoken", help="Claims a batch of Plaid tokens using a secure PIN.")
    async def claimtoken(self, ctx, pin: str):
        guild_name = ctx.guild.name if ctx.guild else "DirectMessage"
        user_name = ctx.author.name
        
        if not os.path.exists("latest_token.txt"):
            await ctx.send(f"❌ **{user_name}**, no temporary token file found! Run `plaid_server.py` first.")
            return
            
        with open("latest_token.txt", "r") as f:
            lines = f.read().splitlines()
            
        if len(lines) < 2:
            await ctx.send("❌ Error: No banks were linked during that session.")
            return
            
        saved_pin = lines[0]
        tokens = lines[1:] # Grab everything after the first line
        
        if pin != saved_pin:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass
            await ctx.send(f"🔒 **{user_name}**, incorrect PIN! Access denied.")
            return
            
        # Loop through and add every token they linked
        for token in tokens:
            add_plaid_token(guild_name, user_name, token)
            
        os.remove("latest_token.txt")
        
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
            
        await ctx.send(f"✅ **{user_name}**, PIN accepted! Successfully claimed {len(tokens)} bank connection(s) into your profile.")

    @commands.command(name="bank", help="Pulls live balances from all your linked bank accounts.")
    async def bank(self, ctx):
        guild_name = ctx.guild.name if ctx.guild else "DirectMessage"
        user_name = ctx.author.name
        
        # Get the LIST of tokens now
        tokens = get_plaid_tokens(guild_name, user_name)
        
        if not tokens:
            await ctx.send(f"❌ **{user_name}**, you haven't linked any banks yet! Run the web server to connect.")
            return
            
        loading_msg = await ctx.send(f"🔄 *Contacting {len(tokens)} financial institution(s)...*")
            
        embed = discord.Embed(
            title=f"🏦 {user_name}'s Live Bank Balances",
            color=discord.Color.green()
        )
        
        total_cash = 0
        
        for token in tokens:
            try:
                request = AccountsBalanceGetRequest(access_token=token)
                response = self.client.accounts_balance_get(request)
                
                for account in response['accounts']:
                    name = account['name']
                    balance = account['balances']['available']
                    if balance is None:
                        balance = account['balances']['current']
                        
                    subtype = account['subtype'].value if account['subtype'] else "Account"
                    embed.add_field(name=f"{name} ({subtype.capitalize()})", value=f"${balance:,.2f}", inline=False)
                    
                    if account['type'].value == 'depository':
                        total_cash += balance
                        
            except plaid.ApiException as e:
                embed.add_field(name="⚠️ Connection Error", value="Failed to sync one of your institutions. You may need to re-link it.", inline=False)
                print(f"API Error for one token: {e}")

        embed.set_footer(text=f"Total Liquid Cash: ${total_cash:,.2f}")
        
        await loading_msg.delete()
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Bank(bot))