import asyncio
import dataclasses
import datetime
import time
from typing import Optional, Dict, List, Tuple, Awaitable

import discord
from discord.ext import commands

import cauch_e.db
import cauch_e.error
import cauch_e.config
from .common import admin_only_params, normalise_module_code, is_in_server, is_admin


class GroupCommands(commands.GroupCog, name="group"):
  # Throughout this class, ephemeral=True is set, meaning that only the invoking user can see the command + responses.
  # This is because some of the group stuff could be socially difficult, so loudly announcing someone is leaving a group
  # is suboptimal. These also work in DMs, but OOB stuff is usually bad UX.


  @discord.app_commands.command(name="leave", description="Leaves a study group for a module")
  @discord.app_commands.describe(module="The module code for the study group")
  @discord.app_commands.describe(admin_only_target="The target user to update. Admin only!")
  @discord.app_commands.check(is_in_server)
  async def leave(self, interaction: discord.Interaction, module: str, admin_only_target: Optional[discord.Member]):
    await admin_only_params(interaction, admin_only_target)
    module = normalise_module_code(module)
    target_id = admin_only_target.id if admin_only_target is not None else interaction.user.id

    def check_crit() -> Awaitable:
      # This is a critical section: any awaiting could cause mild db inconsistencies
      #
      # Putting it in a function explicitly bars awaits

      # Get all the groups for this module
      groups = cauch_e.db.driver.list_study_groups(module)
      # Filter out the ids for groups that our user is in
      our_groups = [group_id for group_id, group_info in groups.items() if target_id in group_info.members]
      # If they aren't in any modules, whinge
      if len(our_groups) == 0:
        return interaction.response.send_message("You are not in any groups for that module.", ephemeral=True)

      ret: Optional[Awaitable] = None
      # If they have somehow joined multiple groups, the DB is inconsistent, which is bad.
      #
      # We continue after this error, which is why we can't just deref `groups` earlier: we want to repair this inconsistency
      if len(our_groups) > 1:
        ret = cauch_e.error.report_error(bot=self.bot, interaction=interaction,
                                         message=f"User {target_id} is in multiple study groups: {our_groups}")

      for group_id in our_groups:
        cauch_e.db.driver.remove_from_study_group(module_code=module, member=target_id, group_id=group_id)
        # If this was the last member, clear up the study group
        if len(groups[group_id].members) <= 1:
          cauch_e.db.driver.delete_study_group(module_code=module, group_id=group_id)

      async def final():
        await interaction.response.send_message("Done.", ephemeral=True)
        if ret: await ret
      return final()

    await check_crit()


  @discord.app_commands.command(name="invite", description="Leaves a study group for a module")
  @discord.app_commands.describe(module="The module code for the study group")
  @discord.app_commands.describe(invitee="The user you want to invite")
  @discord.app_commands.describe(admin_only_group_id="The target user to update. Admin only!")
  @discord.app_commands.check(is_in_server)
  # @discord.app_commands.checks.cooldown(rate=10, per=60 * 10) # 10 invites in 10 mins should be more than enough
  @discord.app_commands.checks.cooldown(rate=1, per=10)  # TODO: remove debug
  async def invite(self, interaction: discord.Interaction, module: str, invitee: discord.Member, admin_only_group_id: Optional[str]):
    await admin_only_params(interaction, admin_only_group_id)
    module = normalise_module_code(module)

    # See if we can skip using the lookup
    group_id = admin_only_group_id
    if group_id is None:
      # Get all the groups for this module
      groups = cauch_e.db.driver.list_study_groups(module)
      # Filter out the ids for groups that our user is in
      groups = [group_id for group_id, group_info in groups.items() if interaction.user.id in group_info.members]
      # If they aren't in any modules, whinge
      if len(groups) == 0:
        await interaction.response.send_message("You are not in any groups for that module.", ephemeral=True)
        return
      if len(groups) > 1:
        # If in multiple groups, we cannot just continue, as the DB is inconsistent and we wouldn't know which group to invite to anyway
        await cauch_e.error.report_error(bot=self.bot, interaction=interaction,
                                         message=f"User {interaction.user.id} is in multiple study groups: {groups}")
        return
      group_id = groups[0]

    invite_msg = await invitee.send(f"You have been invited to join a study group for {module} by {interaction.user.mention}. React with a :+1: to accept.\n\nIf you don't get a response when you accept, you should ask for another invite.")
    await invite_msg.add_reaction("👍")
    await interaction.response.send_message("Invite sent", ephemeral=True)
    def check_reaction(reaction: discord.Reaction, reactor: discord.Member):
      return reaction.message == invite_msg and reactor == invitee and reaction.emoji == "👍"
    await self.bot.wait_for("reaction_add", check=check_reaction)

    # idk how the caching works, let's not let it interfere with the critical section
    invitee_id = invitee.id
    def check_crit() -> bool:
      # This is a critical section: any awaiting could cause mild db inconsistencies
      #
      # Putting it in a function explicitly bars awaits

      groups = cauch_e.db.driver.list_study_groups(module_code=module)
      for group in groups.values():
        if invitee_id in group.members:
          return False
      cauch_e.db.driver.add_to_study_group(module_code=module, group_id=group_id, member=invitee_id)
      # Clean up if they were looking for another group
      cauch_e.db.driver.unqueue_from_study_group(module_code=module, member_id=invitee_id)
      return True

    if not check_crit():
      await invite_msg.reply(content="You are already in a group for that module.")

    await interaction.user.send(content=f"Your invite for {module} was accepted by {interaction.user.mention}")

  # def join
  # def create_private
  # def invite
  # def join

  @discord.app_commands.command(name="create-invite-only",
                                description="Create a group for your friends. Allow others to join with /group invite-only True")
  @discord.app_commands.describe(module="The module code")
  async def create_invite_only(self, interaction: discord.Interaction, module: str):
    user_id = interaction.user.id
    def crit():
      for group in groups.values():
        if user_id in group.members:
          return interaction.response.send_message("You are already in a group for that module.", ephemeral=True)

    groups = cauch_e.db.driver.list_study_groups(module)
    if interaction.user in (i for i in groups.items()):
      pass

  @discord.app_commands.command(name="invite-only",
                                description="Controls whether your group is invite-only, or if others can be assigned to it")
  @discord.app_commands.describe(module="The module code")
  @discord.app_commands.describe(on="Whether invite-only mode should be on")
  async def invite_only(self, interaction: discord.Interaction, module: str, on: bool):
    groups = cauch_e.db.driver.list_study_groups(module)
    groups = [group_id for group_id, group_info in groups.items() if interaction.user.id in group_info.members]
    if len(groups) == 0:
      await interaction.response.send_message("You are not in any groups for that module.", ephemeral=True)
      return
    if len(groups) > 1:
      # If in multiple groups, we cannot just continue, as the DB is inconsistent and we wouldn't know which group to invite to anyway
      await cauch_e.error.report_error(bot=self.bot, interaction=interaction,
                                       message=f"User {interaction.user.id} is in multiple study groups: {groups}")
      return
    cauch_e.db.driver.modify_study_group(module_code=module, group_id=groups[0], invite_only=on)

    await interaction.response.send_message("Group modified.", ephemeral=True)

  @discord.app_commands.command(name="find", description="Finds you a study group for a module")
  @discord.app_commands.describe(module="The module code")
  @discord.app_commands.check(is_in_server)
  @discord.app_commands.checks.cooldown(rate=8, per=60*30) # This can trigger stir_groups, which is pretty heavy, so let's restrict this
  async def find(self, interaction: discord.Interaction, module: str) -> None:
    module = normalise_module_code(module)

    # Expand out the user ids
    user_id = interaction.user.id
    def crit() -> Tuple[bool, Awaitable]:
      # This is a critical section: any awaiting could cause mild db inconsistencies
      #
      # Putting it in a function explicitly bars awaits

      study_groups = cauch_e.db.driver.list_study_groups(module)
      # Check to see if the user is already in a study group
      for group in study_groups.values():
        if user_id in group.members:
          return False, interaction.response.send_message("You are already in a study group for this module.", ephemeral=True)

      if not cauch_e.db.driver.queue_for_study_group(module_code=module, member_id=user_id):
        return False, interaction.response.send_message("You are already searching for a study group for this module.", ephemeral=True)

      return True, interaction.response.send_message(f"Searching for study group. This may take up to {cauch_e.config.obj['study_group']['max_time']} hours, but if it takes longer, please contact the committee for manual group allocation.", ephemeral=True)

    should_stir, cont = crit()
    await cont
    if should_stir:
      await self.stir_groups(module)

  @discord.app_commands.command(name="stir", description="Stirs all the groups. Admin only.")
  @discord.app_commands.check(is_in_server)
  @discord.app_commands.check(is_admin)
  async def stir(self, interaction: discord.Interaction) -> None:
    start = datetime.datetime.now()
    await self.stir_groups()
    await interaction.response.send_message(f"Stirred all groups in {datetime.datetime.now() - start}", ephemeral=True)

  async def stir_groups(self, *modules: str) -> None:
    """Tries to create groups.

    While adding new users can of course create new groups, so can the passage of time,
    so this should be run periodically.

    :param modules: The modules to update. Defaults to all.
    :return: A list of all the updated groups
    """
    # Report that we're stirring
    print("Stirring")
    start = datetime.datetime.now()

    time_bound = start - datetime.timedelta(hours=cauch_e.config.obj['study_group']['max_time'])
    lower_bound = cauch_e.config.obj['study_group']['lower_bound']
    upper_bound = cauch_e.config.obj['study_group']['upper_bound']
    target_size = cauch_e.config.obj['study_group']['target_size']

    @dataclasses.dataclass
    class ReportInfo:
      module_code: str
      members_ids: List[int]

    # We keep track of all the modified groups so that we can tell the members who's in it.
    updated_groups: List[cauch_e.db.StudyGroupInfo] = []

    # Literal cringers decided to have literally no way of doing nested flow control in loops, because there is only 1 dimension
    #
    # smh
    def grumble_pep3136(module_code: str):
      # This function needs to not have someone jump in the DB and mess everything up, so it is not async.

      groups = list(cauch_e.db.driver.list_study_groups(module).values())
      # Sort the groups from oldest to newest
      groups.sort(key=lambda group: group.date_created)

      # FIXME: while pop is convenient, it does mean than spooky exceptions will unqueue people randomly

      # Check for undersized groups, prioritising older groups who have had to suffer for longer
      #
      # FIXME: this means groups that people keep leaving will get priority, maybe bias against this?
      for group in groups:
        if len(group.members) >= target_size:
          continue

        if (member := cauch_e.db.driver.pop_queue_for_study_group(module_code)) is None:
          return
        cauch_e.db.driver.add_to_study_group(module_code, group.id, member.member_id)
        group.members.add(member.member_id)
        updated_groups.append(group)

      # Try to create a new group
      while len(new_group := cauch_e.db.driver.peek_queue_for_study_group(module_code)) == target_size:
        group_id = cauch_e.db.driver.create_study_group(module_code, invite_only=False)
        for i in new_group:
          cauch_e.db.driver.add_to_study_group(module_code, group_id, i.member_id)
        # TODO: maybe be less lazy? I want to keep this resilient against updates of this struct tho...
        updated_groups.append(cauch_e.db.driver.get_study_group(module_code, group_id))
        # Do this separately, so we don't accidentally kick people off the queue because of an exception
        for i in new_group:
          cauch_e.db.driver.unqueue_from_study_group(module_code, i.member_id)

      # We've done all we can for queued users below max_time now.

      # Try to pad groups, prioritising newer groups so that people aren't third wheeling
      for group in reversed(groups):
        # We don't make groups larger than upper_bound
        if len(group.members) >= upper_bound:
          continue
        if (member := cauch_e.db.driver.pop_queue_for_study_group(module_code, time_bound)) is None:
          return
        cauch_e.db.driver.add_to_study_group(module_code, group.id, member.member_id)
        group.members.add(member.member_id)
        updated_groups.append(group)

      # Last ditch effort: create undersized group
      new_group = [i for i in cauch_e.db.driver.peek_queue_for_study_group(module_code, target_size) if i.time <= time_bound]
      if len(new_group) >= lower_bound:
        group_id = cauch_e.db.driver.create_study_group(module_code, invite_only=False)
        for i in new_group:
          cauch_e.db.driver.add_to_study_group(module_code, group_id, i.member_id)
        # TODO: maybe be less lazy? I want to keep this resilient against updates of this struct tho...
        updated_groups.append(cauch_e.db.driver.get_study_group(module_code, group_id))
        # Do this separately, so we don't accidentally kick people off the queue because of an exception
        for i in new_group:
          cauch_e.db.driver.unqueue_from_study_group(module_code, i.member_id)

    if len(modules) == 0:
      modules = cauch_e.db.driver.list_modules().keys()

    for module in modules:
      grumble_pep3136(module)

    for group in updated_groups:
      members = await asyncio.gather(*[self.bot.fetch_user(member_id) for member_id in group.members])
      tag_str = ", ".join(member.mention for member in members)
      await asyncio.gather(*[member.send(f"Your group for {group.module_code} is now {tag_str}") for member in members])
    print(f"Stirring took {datetime.datetime.now() - start}")

  async def stir_loop(self):
    await asyncio.sleep(60) # Do first stir 60 seconds after start
    while True:
      await self.stir_groups()
      await asyncio.sleep(60 * 60)

  def __init__(self, bot: commands.Bot):
    asyncio.run_coroutine_threadsafe(self.stir_loop(), asyncio.get_running_loop())
    self.bot = bot
    super().__init__()