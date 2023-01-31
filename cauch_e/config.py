"""Various ways of handling the config file

Please, PLEASE do not just pile every tweakable here; adding new items is easy, renaming/deleting them is **hard**
"""
import re
from typing import TextIO, Optional, Any

import yaml
import inquirer

# XXX: this will *not* be initialised until main() is called
#
# Make sure that everything here will be nicely serialised in both directions (i.e. string/int/dict thereof)
obj: Optional[dict] = None

class BadConfig(Exception):
  pass

# Please note that you do not need to put every option here, just the bare minimum needed to work
def update_config() -> None:
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
  print("Study group settings:")
  obj_study_group = obj.setdefault("study_group", {})
  if "lower_bound" not in obj_study_group:
    obj_study_group["lower_bound"] = int(inquirer.text("Size lower bound", default=3, validate=lambda _, j: re.match(r"\d+", j)))
  if "target_size" not in obj_study_group:
    obj_study_group["target_size"] = int(inquirer.text("Size target", default=4, validate=lambda _, j: re.match(r"\d+", j)))
  if "upper_bound" not in obj_study_group:
    obj_study_group["upper_bound"] = int(inquirer.text("Size upper bound", default=6, validate=lambda _, j: re.match(r"\d+", j)))
  if "max_time" not in obj_study_group:
    obj_study_group["max_time"] = int(inquirer.text("Maximum time to wait (hours)", default=24, validate=lambda _, j: re.match(r"\d+", j)))

  print()
  print("Discord settings:")
  obj_discord = obj.setdefault("discord", {})
  if "token" not in obj_discord: obj_discord["token"] = inquirer.password("Discord token")
  if "prefix" not in obj_discord: obj_discord["prefix"] = inquirer.text("Bot prefix")
  if "admin_role" not in obj_discord: obj_discord["admin_role"] = int(inquirer.text("Admin role ID", validate=lambda _, j: re.match(r"\d+", j)))
  if "report_channel" not in obj_discord: obj_discord["report_channel"] = int(inquirer.text("Critical error report channel ID", validate=lambda _, j: re.match(r"\d+", j)))

  print()

  print("Database settings:")
  obj_db: dict = obj.setdefault("db", {})
  driver_name: str
  obj_db_driver: dict
  if len(obj_db) == 1:
    # This gets the first (and only) key of the dict
    driver_name = next(iter(obj_db))
  else:
    driver_name = inquirer.list_input("Database driver", choices=["sqlite"], default="sqlite")

  obj_db_driver = obj_db.setdefault(driver_name, {})

  match driver_name:
    case "sqlite":
      if "path" not in obj_db_driver: obj_db_driver["path"] = inquirer.text("Path to database", default="cauch-e.db")
    case _:
      raise NotImplementedError(f"Unknown driver {obj_db_driver}")

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