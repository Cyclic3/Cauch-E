"""Various ways of handling the config file

Please, PLEASE do not just pile every tweakable here; adding new items is easy, renaming/deleting them is **hard**
"""
from typing import TextIO, Optional, Any

import yaml
import inquirer

# XXX: this will *not* be initialised until main() is called
#
# Make sure that everything here will be nicely serialised in both directions (i.e. string/int/dict thereof)
obj: Optional[dict] = None

# Please note that you do not need to put every option here, just the bare minimum needed to work
def update_config():
  """
  A weaving maze of menus to create a basic config file.
  The result will be stored in the variable `config.obj`, so it must be saved separately with save_config
  """
  global obj
  if obj is None:
    obj = {}
    print("Creating new config file.")
  else:
    print("Updating existing config file.")
    print("Existing values will not be modified. Delete them from the config if you want them to configure them here")

  print("An empty answer will choose the default value, or the old value if updating an existing file.")

  print()
  print("Discord settings:")
  obj_discord = obj.setdefault("discord", {})
  if "token" not in obj_discord: obj_discord["token"] = inquirer.password("Discord token")
  if "prefix" not in obj_discord: obj_discord["prefix"] = inquirer.text("Bot prefix")

  print()

def load_config(file: TextIO):
  """
  A weaving maze of menus to create a basic config file
  :param file: The stream to read the config from
  """
  global obj
  obj = yaml.load(file, yaml.SafeLoader)

def save_config(file: TextIO):
  """
  A weaving maze of menus to create a basic config file
  :param file: The stream to dump the config into
  """
  global obj
  yaml.dump(obj, file)