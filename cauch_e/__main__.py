import sys
from typing import TextIO

import discord
import argparse

from cauch_e import config, bot, db

def main() -> int:
  parser = argparse.ArgumentParser(
    prog = "cauch-e",
    description = "A Discord bot for the University of Liverpool Maths Society",
    epilog = "Good luck!"
  )
  # Default the config argument to a nice value, that we include in the gitignore to stop funny token leak
  parser.add_argument("config", default="config.yaml", nargs='?', help="The YAML configuration file")
  parser.add_argument("--update-config", action="store_true", help="(Re)generates the configuration file")
  parser.add_argument("--sync", action="store_true", help="Synchronises the commands for the bot. Dev feature.")

  args = parser.parse_args()

  if args.update_config:
    # We try to create the file first, so the user doesn't need to start again if file IO fails

    try:
      # Atomically creates the file if it does not exist, throws an exception if it does
      #
      # This stops us having a (very unlikely) race condition
      file: TextIO
      with open(args.config, "x") as file:
        config.update_config()
        config.save_config(file)
    except FileExistsError:
      # If it exists, we try to load the existing configuration
      try:
        with open(args.config, "r+") as file:
          config.load_config(file)
          config.update_config()
          # Now that we're done, nuke the file...
          file.seek(0)
          file.truncate()
          # ... and save the new config
          config.save_config(file)
      except OSError:
        print(f"Failed to overwrite '{args.config}'. Maybe missing filesystem permissions?")
    # We need a separate case to handle the non-truncating case failing
    except OSError:
      print(f"Failed to create '{args.config}'. Maybe missing filesystem permissions?")

    # Now we have created the config, terminate so that the user can tinker with it
    print("Config file created successfully")
    return 0

  # If we get here, we are running the bot as normal
  try:
    with open(args.config, "r") as file:
      config.load_config(file)
  except FileNotFoundError:
    print(f"The config file '{args.config}' was not found. Try using --update-config to create a new config file.")
    return 1

  db.load_db()

  client = bot.Client(do_sync=args.sync)
  client.start_bot()

  return 0
if __name__ == "__main__":
  sys.exit(main())