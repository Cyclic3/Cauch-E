from typing import Any, Optional

import discord
import cauch_e.config

def normalise_module_code(module_code: str):
  return module_code.upper().replace(" ", "")

def is_admin(interaction: discord.Interaction):
  return cauch_e.config.obj["discord"]["admin_role"] in interaction.user.roles

def is_in_server(interaction: discord.Interaction):
  return interaction.guild is not None

async def admin_only_params(interaction: discord.Interaction, *params: Optional[Any]):
  # This way round is faster, because we don't need to query the remote roles
  if any(param is not None for param in params) and (role := cauch_e.config.obj["discord"]["admin_role"]) not in (i.id for i in interaction.user.roles):
    await interaction.response.send_message("You tried to use an admin command. Don't do that :)", ephemeral=True)
    raise discord.app_commands.MissingRole(role)

