import datetime
import json
import sys
import traceback
from typing import Optional, Any

import discord
import cauch_e.config
import discord.ext.commands

async def report_error(bot: discord.ext.commands.Bot, interaction: discord.Interaction, message: Optional[str] = "", exn: Optional[Exception] = None):
  """
    This should *only* be used to report *very* bad things happening, such as DB inconsistency,
    not things like "module couldn't be found".

    If you don't follow this rule, people will ignore all error messages, and that will be bad.

    :param bot The bot object, used for the various fallback reporting methods
    :param interaction The interaction that caused this error.
    :param message A human-readable description of what went wrong.
    :param exn An exception that we grab the stack from instead of the call site
  """

  # Please don't print exceptions, as if we get to that point, we should rely on static text of known length,
  # as opposed to arbitrarily long program exceptions.

  try:
    stack: traceback.StackSummary
    if exn is None:
      stack = traceback.extract_stack()
    else:
      stack = traceback.TracebackException.from_exception(exn).stack

    # Before we do anything, print the error out
    print('-' * 80)
    print(f"Encountered critical error at {datetime.datetime.now()}")
    traceback.print_list(stack)
    print(message)
    print(f"{interaction.data}")
    # Do this last, as this may fail (because python), and we want to make sure that something gets posted.
    print(interaction.user)
    print('-' * 80)

    try:
      channel_id = cauch_e.config.obj["discord"]["report_channel"]
      channel = interaction.guild.get_channel(channel_id)
      admin_role_id = cauch_e.config.obj["discord"]["admin_role"]
      admin_role = interaction.guild.get_role(admin_role_id)
      if channel is None or admin_role is None or not channel.permissions_for(interaction.guild.me).send_messages:
        raise Exception("Cannot message report channel")

      try:
        embed = discord.Embed(color=discord.Color.red(), title="Critical Cauch-E error!", type="image",
                              description=f"{admin_role.mention} Something *really* bad has happened, and you need to get someone who knows what they're doing to fix it.")
        embed.add_field(name="Message", value=message, inline=True)
        embed.add_field(name="User", value=interaction.user, inline=True)
        embed.add_field(name="Backtrace", value=''.join(traceback.format_list(stack)[-4:-1]), inline=True)
        embed.add_field(name="Interaction", value=interaction.data, inline=True)

        await channel.send(embed=embed)

      except:
        # If we cannot report it properly, just spam everyone, including the channel and the user who triggered it
        await channel.send(f"FATAL Cauch-E error! Something went so badly wrong the bot literally cannot describe it.")
        raise

    except:
      traceback.print_exc()
      # If we can't even report the error, we are in deeeeep trouble
      await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.playing, name="BOT FAILURE! SPAM THE COMMITTEE TO FIX IT!"))
      # Try begging the user for help. Do this last, because it will probably fail at this point.
      if interaction is not None:
        # Making it ephemeral means we don't accidentally leak confidential information, and may need less perms idk
        msg = "You must immediately contact the committee, as a severe fault has been detected in the bot!"
        try:
          await interaction.response.send_message(msg, ephemeral=True)
        # Handle the case where we already responded to it
        except discord.InteractionResponded:
          await interaction.followup.send(msg, ephemeral=True)
      return
  except:
    traceback.print_exc()
    # If we screw up *this* badly, we almost certainly cannot do anything. Something is deeply screwed at the logic level.
    # In addition, the only way to get attention is to exit, which we will do after complaining.
    print("Bot assumed contradictory axioms, and is therefore screwed.")
    sys.exit(1)