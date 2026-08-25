import discord
from discord.ext import commands
import os
import glob

class Developer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="resetdb", help="[ADMIN ONLY] Deletes all database files to start fresh.")
    @commands.has_permissions(administrator=True)
    async def resetdb(self, ctx):
        db_dir = 'databases'
        
        # Check if the folder even exists first
        if not os.path.exists(db_dir):
            await ctx.send("⚠️ No databases folder found. Nothing to delete!")
            return

        # Find all .db files inside the databases folder
        db_files = glob.glob(os.path.join(db_dir, '*.db'))
        
        if not db_files:
            await ctx.send("📭 No database files found. It's already empty!")
            return
            
        # Loop through and delete each file
        deleted_count = 0
        for file_path in db_files:
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
                
        # Send a confirmation message
        embed = discord.Embed(
            title="🧹 Databases Wiped!",
            description=f"Successfully deleted {deleted_count} database file(s).\n\nYour next `!paycheck` will start completely from scratch.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Developer(bot))