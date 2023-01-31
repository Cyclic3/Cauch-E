from typing import Optional, List, Tuple

import discord
from discord.ext import commands

import cauch_e.db
import cauch_e.error
from .common import admin_only_params, normalise_module_code

class ModuleCommands(commands.GroupCog, name="module"): pass
  # @discord.app_commands.command(name="join", description="Gives access for some module")
  # @discord.app_commands.describe(module="The module code")
  # @discord.app_commands.describe(admin_only_target="The target user to update. Admin only!")
  # @discord.app_commands.NoPrivateMessage
  # async def join(self, interaction: discord.Interaction, module: str, admin_only_target: Optional[discord.Member]) -> None:
  #   await admin_only_params(interaction, "admin_only_target")
  #   module = normalise_module_code(module)
  #
  #   target = admin_only_target if admin_only_target is not None else interaction.user
  #   module = cauch_e.db.driver.get_module(module)
  #   if module is None:
  #     await interaction.response.send_message("This module could not be found. You should ask the committee for it to be added!", ephemeral=True)
  #     return
  #   role = interaction.guild.get_role(module.role_id)
  #   if module is None:
  #     # If the module's role is gone, that not good at all
  #     await cauch_e.error.report_error(bot=self.bot, interaction=interaction, message=f"Module role for {module} is gone")
  #     return
  #   await target.add_roles(role)
  #   await interaction.response.send_message("Done")
  #
  #
  # @discord.app_commands.command(name="join", description="Removes access for some module")
  # @discord.app_commands.describe(module="The module code")
  # @discord.app_commands.describe(admin_only_target="The target user to update. Admin only!")
  # @discord.app_commands.NoPrivateMessage
  # async def join(self, interaction: discord.Interaction, module: str, admin_only_target: Optional[discord.Member]) -> None:
  #   await admin_only_params(interaction, "admin_only_target")
  #   module = normalise_module_code(module)
  #
  #   target = admin_only_target if admin_only_target is not None else interaction.user
  #   module = cauch_e.db.driver.get_module(module)
  #   if module is None:
  #     await interaction.response.send_message("This module could not be found. You should ask the committee for it to be added!", ephemeral=True)
  #     return
  #   role = interaction.guild.get_role(module.role_id)
  #   if module is None:
  #     # If the module's role is gone, that not good at all
  #     await cauch_e.error.report_error(bot=self.bot, interaction=interaction, message=f"Module role for {module} is gone")
  #     return
  #   await target.remove_roles(role)
  #   await interaction.response.send_message("Done")
  #
  # def __init__(self, bot: commands.Bot):
  #   self.bot = bot
  #   super().__init__()
