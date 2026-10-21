import discord
from discord import app_commands
import os

class Wildflower(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"Wildflower online: {self.user}")

bot = Wildflower()

@bot.tree.command(name="hello", description="Say hello")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Wildflower is online! 🌻")

bot.run(os.getenv("DISCORD_TOKEN"))