import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

# Load the hidden variables from your .env file
load_dotenv()

# Set up intents (permissions the bot needs to read messages)
intents = discord.Intents.default()
intents.message_content = True

# Initialize the bot with a prefix (e.g., !paycheck)
bot = commands.Bot(command_prefix='!', intents=intents, help_command=commands.DefaultHelpCommand())

@bot.event
async def on_ready():
    """This triggers once when the bot successfully connects to Discord."""
    print(f'✅ Logged in securely as {bot.user.name}')
    print('💼 The Haushold CFO is online and ready for business!')

async def load_cogs():
    """This function looks inside the /cogs folder and loads every Python file as a module."""
    # This automatically finds the exact folder where main.py lives
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cogs_dir = os.path.join(base_dir, 'cogs')

    if not os.path.exists(cogs_dir):
        os.makedirs(cogs_dir)
        print("Created /cogs directory.")

    # Look through the real cogs folder
    for filename in os.listdir(cogs_dir):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f"Loaded extension: {filename}")
            except Exception as e:
                print(f"Failed to load extension {filename}: {e}")
async def main():
    """The main setup loop."""
    await load_cogs()
    
    token = os.getenv('DISCORD_TOKEN')
    if token is None:
        print("🚨 ERROR: DISCORD_TOKEN not found! Check your .env file.")
        return
        
    await bot.start(token)

if __name__ == '__main__':
    asyncio.run(main())