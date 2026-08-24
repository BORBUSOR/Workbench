import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['help'])
    async def commands(self, ctx):
        # Create the embed structure
        embed = discord.Embed(
            title="🤖 Bot Command List",
            description="Here is everything I can do:",
            color=discord.Color.blue()
        )

        # Add fields for all server commands
        embed.add_field(
            name="!ping", 
            value="A simple connection test. Replies with 'Pong! 🏓'", 
            inline=False
        )
        
        embed.add_field(
            name="!tag", 
            value="Randomly pings one human in the server.", 
            inline=False
        )
        
        embed.add_field(
            name="!roulette", 
            value="Randomly server-mutes someone in your voice channel for 10 seconds.", 
            inline=False
        )
        
        embed.add_field(
            name="!unmute_me", 
            value="Allows you to manually remove your own server-mute.", 
            inline=False
        )

        embed.add_field(
            name="!bad", 
            value="Plays a random Bad to the Bone sound effect in your voice channel.", 
            inline=False
        )

        embed.add_field(
            name="!boo", 
            value="Plays a spooky boo sound effect in your voice channel.", 
            inline=False
        )

        embed.add_field(
            name="!chord", 
            value="Plays a chord sound effect in your voice channel.", 
            inline=False
        )

        embed.add_field(
            name="!eightball", 
            value="Ask the magic 8-ball a question.", 
            inline=False
        )

        embed.add_field(
            name="!knock", 
            value="Tells a knock-knock joke.", 
            inline=False
        )

        embed.add_field(
            name="!phantom & !vidList", 
            value="Toggles background voice channel haunting and manages the YouTube jumpscare playlist.", 
            inline=False
        )

        embed.add_field(
            name="!roll", 
            value="Rolls a random number or dice.", 
            inline=False
        )

        embed.add_field(
            name="!truthnova", 
            value="Deploys a 5-stage complex academic trivia challenge with an audio explosion penalty.", 
            inline=False
        )

        embed.add_field(
            name="!truthnuke", 
            value="Deploys a tactical trivia nuke challenge with an audio explosion penalty.", 
            inline=False
        )

        embed.add_field(
            name="!vote", 
            value="Starts a community vote or poll.", 
            inline=False
        )

        # Add a nice footer at the bottom
        embed.set_footer(text="Have fun!")

        # Send the embed to the channel
        await ctx.send(embed=embed)

# The mandatory export function
async def setup(bot):
    await bot.add_cog(Help(bot))