import discord
from discord.ext import commands, tasks
import random
import asyncio
import os
from datetime import datetime, timedelta
import yt_dlp

class Phantom(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Starts the background loop when the bot turns on
        self.haunt_vc.start()

    def cog_unload(self):
        self.haunt_vc.cancel()

    # --- THE SMART TOGGLE COMMAND ---
    @commands.command()
    async def phantom(self, ctx, action: str = "status"):
        action = action.lower()
        
        if action == "status":
            if self.haunt_vc.is_running():
                await ctx.send("👻 **Phantom Status:** 🟢 ONLINE (Actively hunting for victims).")
            else:
                await ctx.send("🛑 **Phantom Status:** 🔴 OFFLINE (The ghost is resting).")
                
        elif action == "on":
            if self.haunt_vc.is_running():
                await ctx.send("👻 Phantom is already **🟢 ONLINE**.")
            else:
                self.haunt_vc.start()
                await ctx.send("👻 **Phantom Mode Enabled.** The haunting has begun...")
                
        elif action == "off":
            if not self.haunt_vc.is_running():
                await ctx.send("🛑 Phantom is already **🔴 OFFLINE**.")
            else:
                self.haunt_vc.cancel()
                await ctx.send("🛑 **Phantom Mode Disabled.** The bot will stop haunting voice channels.")
                
        else:
            await ctx.send("⚠️ **Invalid command!** Try `!phantom on`, `!phantom off`, or `!phantom status`.")

    # --- YOUTUBE PLAYLIST MANAGEMENT ---
    @commands.group(invoke_without_command=True)
    async def vidList(self, ctx):
        await ctx.send("📋 **YouTube Playlist Commands:**\n`!vidList add <link>` - Add a YouTube link to the jumpscare pool\n`!vidList list` - View all loaded YouTube links")

    @vidList.command(name="add")
    async def vidList_add(self, ctx, url: str):
        if not url.startswith("http"):
            await ctx.send("❌ That doesn't look like a valid URL!")
            return
            
        yt_file = os.path.join(os.path.dirname(__file__), '..', 'youtube_urls.txt')
        if not os.path.exists(os.path.dirname(yt_file)):
            yt_file = 'youtube_urls.txt'
        
        # Append the link to the text file automatically
        with open(yt_file, 'a') as f:
            f.write(f"{url}\n")
            
        await ctx.send(f"✅ Successfully added `{url}` to the Phantom's YouTube playlist!")

    @vidList.command(name="list")
    async def vidList_list(self, ctx):
        yt_file = os.path.join(os.path.dirname(__file__), '..', 'youtube_urls.txt')
        if not os.path.exists(yt_file):
            yt_file = 'youtube_urls.txt'

        if not os.path.exists(yt_file):
            await ctx.send("❌ The `youtube_urls.txt` file doesn't exist yet!")
            return
            
        with open(yt_file, 'r') as f:
            links = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
        if not links:
            await ctx.send("📭 The YouTube playlist is currently empty.")
            return
            
        link_list_str = "\n".join([f"{i+1}. {link}" for i, link in enumerate(links)])
        if len(link_list_str) > 1900:
            link_list_str = link_list_str[:1900] + "\n...(list truncated)"
            
        await ctx.send(f"📜 **Current YouTube Jumpscares ({len(links)} total):**\n{link_list_str}")

    # --- THE BACKGROUND TASK (Random 1-5 Minute Intervals) ---
    @tasks.loop(minutes=1)
    async def haunt_vc(self):
        await self.bot.wait_until_ready()

        # 1. Find all active voice channels
        active_channels = []
        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                humans = [member for member in vc.members if not member.bot]
                if len(humans) > 0:
                    active_channels.append(vc)

        # 2. If people are in a VC, roll the dice to haunt
        if active_channels:
            target_channel = random.choice(active_channels)
            # Gather all media options into a single unified pool for a fair, equal chance
            all_media = []

            # Check local sfx folder inside cogs/sfx
            sfx_folder = os.path.join(os.path.dirname(__file__), 'sfx')
            if not os.path.exists(sfx_folder):
                sfx_folder = './sfx'

            if os.path.exists(sfx_folder):
                local_files = [f for f in os.listdir(sfx_folder) if f.endswith('.mp3')]
                for file in local_files:
                    all_media.append(("local", file))

            # Check youtube_urls.txt file in root folder
            yt_file = os.path.join(os.path.dirname(__file__), '..', 'youtube_urls.txt')
            if not os.path.exists(yt_file):
                yt_file = 'youtube_urls.txt'

            if os.path.exists(yt_file):
                with open(yt_file, 'r') as f:
                    yt_links = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                for link in yt_links:
                    all_media.append(("youtube", link))

            if not all_media:
                print("Phantom Error: No media found! Add .mp3 files to 'cogs/sfx' or links using '!vidList add'.")
            else:
                # Pick a completely random item from the combined pool
                chosen_type, chosen_item = random.choice(all_media)

                try:
                    voice_client = discord.utils.get(self.bot.voice_clients, guild=target_channel.guild)
                    if voice_client and voice_client.is_connected():
                        await voice_client.move_to(target_channel)
                    else:
                        voice_client = await target_channel.connect()

                    if voice_client.is_playing():
                        voice_client.stop()

                    if chosen_type == "local":
                        file_path = os.path.join(sfx_folder, chosen_item)
                        
                        # Options include -vn (no video) and -af volume=0.3 (caps audio at 30%)
                        voice_client.play(discord.FFmpegPCMAudio(file_path, options='-vn -af volume=0.3'))
                        print(f"👻 [Phantom] Haunting '{target_channel.name}' with local file '{chosen_item}' (Volume capped, Max 10s)!")

                        # Wait up to 10 seconds max
                        elapsed = 0
                        while voice_client.is_playing() and elapsed < 10:
                            await asyncio.sleep(1)
                            elapsed += 1

                        if voice_client.is_playing():
                            voice_client.stop()

                    elif chosen_type == "youtube":
                        ytdl_opts = {
                            'format': 'bestaudio/best',
                            'noplaylist': True,
                            'quiet': True,
                        }

                        def extract_yt():
                            with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                                return ydl.extract_info(chosen_item, download=False)

                        info = await asyncio.to_thread(extract_yt)
                        audio_url = info['url']
                        title = info.get('title', 'YouTube Audio')
                        duration = info.get('duration', 0)

                        # Calculate a random start time (leaving a buffer so it doesn't seek past the end)
                        start_time = 0
                        if duration and duration > 15:
                            max_start = int(duration) - 15
                            start_time = random.randint(0, max_start)

                        # Configure before_options to jump (-ss) to the random point in the video
                        before_opts = f'-ss {start_time} -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'

                        # Stream directly using FFmpeg seek flags and a volume cap filter
                        voice_client.play(discord.FFmpegPCMAudio(
                            audio_url,
                            before_options=before_opts,
                            options='-vn -af volume=0.3'
                        ))
                        print(f"👻 [Phantom] Haunting '{target_channel.name}' with YouTube stream: '{title}' starting at {start_time}s (Volume capped, Max 10s)!")

                        # Wait up to 10 seconds max for the jumpscare
                        elapsed = 0
                        while voice_client.is_playing() and elapsed < 10:
                            await asyncio.sleep(1)
                            elapsed += 1

                        if voice_client.is_playing():
                            voice_client.stop()

                    await voice_client.disconnect()

                except Exception as e:
                    print(f"Phantom audio failed: {e}")
                    if 'voice_client' in locals() and voice_client and voice_client.is_connected():
                        await voice_client.disconnect()
        else:
            print("👻 [Phantom] Checked voice channels, but everyone is hiding (no humans found in VCs).")

        # 3. Randomize the next check between 1 and 5 minutes (60 to 300 seconds)
        next_wait = random.randint(60, 300)
        self.haunt_vc.change_interval(seconds=next_wait)

        next_time = datetime.now() + timedelta(seconds=next_wait)
        formatted_time = next_time.strftime("%I:%M:%S %p")
        minutes_part = next_wait // 60
        seconds_part = next_wait % 60
        print(f"⏳ [Phantom] Next check scheduled in {minutes_part}m {seconds_part}s (at {formatted_time}).")

    @haunt_vc.before_loop
    async def before_haunt_vc(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Phantom(bot))