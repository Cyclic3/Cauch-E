import urllib.parse
from typing import Callable, Any

import discord
from discord.ext import commands

from cauch_e import config, groups

# _start_callbacks = []
#
# def on_bot_start(f: Callable[[discord.Client], Any]):
#   _start_callbacks.append(f)
#
# def start_bot():
#

class CommonCommands(commands.Cog):
  @discord.app_commands.command(name="ping", description="Spooky command")
  async def ping(self, int: discord.Interaction) -> None:
    await int.response.send_message("Pong")

  @discord.app_commands.command(name="maths", description="Renders a LaTeX equation using codecogs API")
  async def latex(self, int: discord.Interaction, latex: str) -> None:
    # TODO: fix for light mode
    latex = urllib.parse.quote(latex)
    await int.response.send_message(f'https://latex.codecogs.com/png.latex?\\dpi{{200}}\\color{{white}}{latex}')

class Client(commands.Bot):
  # def command(self, *args, **kwargs):
  #   def inner(func):
  #
  #   return inner
  # async def on_ready(self):
  #   for cog in [TestCog()]:
  #     await self.add_cog(cog)
  #   await discord.app_commands.CommandTree(self).sync()
  #   print("Ready")

  def start_bot(self):
    self.run(config.obj["discord"]["token"])

  async def setup_hook(self):
    await self.add_cog(CommonCommands())
    await self.add_cog(groups.GroupCommands())
    print("Added cogs")

  async def on_ready(self):
    # # Weird shuffle needed for app commands
    # print("Syncing")
    # await self.tree.sync()
    # for guild in self.guilds:
    #   print(f"Syncing {guild}")
    #   await self.tree.sync(guild=guild)
    print("Ready")

  def __init__(self):
    intents = discord.Intents.default()
    intents.message_content = True
    super().__init__(command_prefix=config.obj["discord"]["prefix"], intents=intents)