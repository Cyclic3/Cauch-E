from typing import Optional, List, Tuple

import discord
import yaml
from discord.ext import commands

import cauch_e.db
import cauch_e.error
from .common import admin_only_params, normalise_module_code, is_in_server, is_admin


class ModuleCommands(commands.GroupCog, name="module"):
  @discord.app_commands.command(name="create-all", description="Creates modules from a YAML spec, overwriting existing modules. Admin only!")
  @discord.app_commands.describe(spec="The YAML spec")
  @discord.app_commands.check(is_in_server)
  @discord.app_commands.check(is_admin)
  async def create_all(self, interaction: discord.Interaction, spec: discord.Attachment):
    spec = await spec.read()
    obj : dict = yaml.safe_load(spec)
    if type(obj) != dict:
      await interaction.response.send_message("Invalid spec: must be an object", ephemeral=True)
      return
    for code, info in obj.items():
      if type(code) != str:
        await interaction.response.send_message(f"Invalid spec: properties need to be indexed by strings", ephemeral=True)
        return
      if type(info.get("title")) != str:
        await interaction.response.send_message(f"Invalid spec: property {code} has missing or invalid title", ephemeral=True)
        return

    # Now we have validated, any exceptions are our fault
    for code, info in obj.items():
      mod = cauch_e.db.ModuleInfo(module_code=normalise_module_code(code), module_name=info["title"])
      cauch_e.db.driver.add_module(mod, overwrite=True)
    await interaction.response.send_message(f"Now have {len(cauch_e.db.driver.list_modules())} modules", ephemeral=True)

  @discord.app_commands.command(name="create", description="Creates a single module.")
  @discord.app_commands.describe(code="The module code")
  @discord.app_commands.describe(name="The module name")
  @discord.app_commands.describe(overwrite="If set to True, will overwrite the information for this module if it already exists")
  @discord.app_commands.check(is_in_server)
  @discord.app_commands.check(is_admin)
  async def create(self, interaction: discord.Interaction, code: str, name: str, overwrite: bool):
    code = normalise_module_code(code)
    if cauch_e.db.driver.add_module(cauch_e.db.ModuleInfo(module_code=code, module_name=name), overwrite=overwrite):
      await interaction.response.send_message(f"Module created", ephemeral=True)
    else:
      await interaction.response.send_message(f"Module already exists. Use /module update if you really want to do this", ephemeral=True)

  @discord.app_commands.command(name="delete", description="Deletes a single module.")
  @discord.app_commands.describe(code="The module code")
  @discord.app_commands.check(is_in_server)
  @discord.app_commands.check(is_admin)
  async def delete(self, interaction: discord.Interaction, code: str):
    code = normalise_module_code(code)
    cauch_e.db.driver.delete_module(code)
    await interaction.response.send_message(f"Done", ephemeral=True)

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
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    super().__init__()
