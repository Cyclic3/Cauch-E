"""
- subject
- size == ~4
- age: new people shouldn't join established groups, but should prioritise old unfilled groups

maybe wait 24hours before creating new one or smth? Select members you wish to join with, so that things works
"""

import discord
from discord.ext import commands

class GroupCommands(commands.GroupCog, name="group"):
  @discord.app_commands.command(name="request", description="Requests to join a new study group")
  @discord.app_commands.describe(module="The module code")
  async def request(self, int: discord.Interaction, module: str) -> None:
    # Normalise the module name
    module = module.upper()
    # TODO: do group allocation
    # TODO: maybe confirm with user if they are ok with group before committing?
    # TODO: ping members of the group
    await int.response.send_message(f"Lol no maths for you {module}")