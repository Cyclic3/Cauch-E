import urllib.parse

import discord
from discord.ext import commands

from cauch_e import config
from cauch_e.cmd import groups, modules
import cauch_e.error


# _start_callbacks = []
#
# def on_bot_start(f: Callable[[discord.Client], Any]):
#   _start_callbacks.append(f)
#
# def start_bot():
#

class OpenCommands(commands.Cog):
  @discord.app_commands.command(name="ping", description="Spooky command")
  async def ping(self, interaction: discord.Interaction) -> None:
    await interaction.response.send_message("Pong")

  @discord.app_commands.command(name="latex", description="Renders a LaTeX equation using codecogs API")
  async def latex(self, interaction: discord.Interaction, latex: str) -> None:
    # TODO: fix for light mode
    latex = urllib.parse.quote(latex)
    await interaction.response.send_message(f'https://latex.codecogs.com/png.latex?\\dpi{{200}}\\color{{white}}{latex}')


  @discord.app_commands.command(name="fail", description="Spookier command")
  async def fail(self, interaction: discord.Interaction, arg: str):
    await cauch_e.error.report_error(bot=self.bot, interaction=interaction, message="Manually failed")

  def __init__(self, bot: commands.Bot):
    self.bot = bot
    super().__init__()

class Client(commands.Bot):
  do_sync: bool
  # def command(self, *args, **kwargs):
  #   def inner(func):
  #
  #   return inner
  # async def on_ready(self):
  #   for cog in [TestCog()]:
  #     await self.add_cog(cog)
  #   await discord.app_commands.CommandTree(self).sync()
  #   print("Ready")
  async def error_handler(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    # It's not a problem if it's just a command check
    if isinstance(error, discord.app_commands.CheckFailure):
      return
    await cauch_e.error.report_error(bot=self, interaction=interaction, message=f"Uncaught error: {error}", exn=error.__context__)

  def start_bot(self):
    self.run(config.obj["discord"]["token"])

  async def setup_hook(self):
    await self.add_cog(OpenCommands(self))
    await self.add_cog(groups.GroupCommands(self),)
    # TODO: decide if we want this
    # await self.add_cog(modules.ModuleCommands(self))
    print("Added cogs")

  async def on_ready(self):
    if self.do_sync:
      # Weird shuffle needed for app commands
      print("Syncing")
      await self.tree.sync()
      for guild in self.guilds:
        print(f"Syncing {guild}")
        await self.tree.sync(guild=guild)
    self.tree.on_error = lambda *args, **kwargs: self.error_handler(*args, **kwargs)
    print("Ready")

  def __init__(self, do_sync = False):
    self.do_sync = do_sync
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    super().__init__(command_prefix=config.obj["discord"]["prefix"], intents=intents)
