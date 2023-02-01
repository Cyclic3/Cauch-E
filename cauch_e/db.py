import abc
import dataclasses
import datetime
import sqlite3
import time
from contextlib import closing
from typing import Optional, List, Set, Dict

import cauch_e.config

@dataclasses.dataclass
class ModuleInfo:
  module_code: str
  """The code (i.e. MATH101) of the module. Must be in all caps."""

  module_name: str
  """The full human-readable name of the module."""

  # role_id: int
  """The id of the corresponding Discord role"""

  # channel_id: int
  """The id of the corresponding Discord channel"""

@dataclasses.dataclass
class StudyGroupInfo:
  id: int
  """The unique ID of the study group."""

  module_code: str
  """The code of the module the study group is for."""

  date_created: datetime.datetime
  """The unix time this group was created."""

  # If you change the datatype of this, PLEASE make sure that we can safely split by commas
  members: Set[int]
  """A list of the members in this study group."""

  invite_only: bool
  """Whether or not anyone can join this group"""

@dataclasses.dataclass
class QueuedStudyGroupInfo:
  module_code: str
  """The code of the module the user wants a study group for."""

  member_id: int
  """The discord id of the user"""

  time: datetime.datetime
  """When the user requested to join the study group."""

class DatabaseDriver(abc.ABC):
  @abc.abstractmethod
  def add_module(self, module: ModuleInfo, overwrite: bool = False) -> bool:
    """
    Creates a module in the database.
    :param module: The description of the module to add.
    :param overwrite: Whether or not the info should be overwritten if it exists.
    :returns: True if a new module was created, False if a module with that name already exists
    """
    pass

  @abc.abstractmethod
  def get_module(self, module_code: str) -> Optional[ModuleInfo]:
    """
    Creates a module in the database.
    :param module_code: The code (i.e. MATH101) of the module. Case insensitive.
    :returns Information about the module if successful, None otherwise.
    """
    pass

  @abc.abstractmethod
  def list_modules(self) -> Dict[str, ModuleInfo]:
    """
    Lists modules in the database.
    :returns All of the modules in the database, indexed by code.
    """
    pass

  @abc.abstractmethod
  def delete_module(self, module_code: str) -> None:
    """
    Deletes a module from the database.
    :param module_code: The code of the module to be deleted.
    """
    pass

  @abc.abstractmethod
  def create_study_group(self, module_code: str, invite_only: bool) -> int:
    """
    Creates a study group entry in the database.
    :param module_code: The module that the group is for.
    :param invite_only: Whether or not the group should be invite only.
    :return: The id of the created group
    """
    pass

  @abc.abstractmethod
  def get_study_group(self, module_code: str, group_id: int) -> Optional[StudyGroupInfo]:
    """
    Lists the study groups for a module.
    :param module_code: The module that the group is for.
    :param group_id: The id of the group inside that module.
    :return: Information about the study group if successful, None otherwise.
    """
    pass

  @abc.abstractmethod
  def list_study_groups(self, module_code: str) -> Dict[int, StudyGroupInfo]:
    """
    Lists the study groups for a module.
    :param module_code: The module that the group is for.
    :return: All of the study groups for module_code in the database, indexed by id.
    """
    pass

  @abc.abstractmethod
  def delete_study_group(self, module_code: str, group_id: int) -> None:
    """
    Deletes a study groups from the database.
    :param module_code: The module that the group is for.
    :param group_id: The id of the group inside that module to delete.
    """
    pass

  @abc.abstractmethod
  def delete_all_study_groups(self, module_code: str) -> None:
    """
    Deletes all study groups for a module from the database.
    :param module_code: The module that the group is for.
    :param group_id: The id of the group inside that module to delete.
    """
    pass

  @abc.abstractmethod
  def add_to_study_group(self, module_code: str, group_id: int, member: int) -> None:
    """
    Atomically adds a member of a study group
    :param module_code: The module that the group is for.
    :param group_id: The id of the group to modify.
    :param member: the new member.
    """
    pass

  @abc.abstractmethod
  def remove_from_study_group(self, module_code: str, group_id: int, member: int) -> None:
    """
    Atomically removes a member from a study group
    :param module_code: The module that the group is for.
    :param group_id: The id of the group to modify.
    :param member: the member to delete
    """
    pass

  @abc.abstractmethod
  def modify_study_group(self, module_code: str, group_id: int, invite_only: Optional[bool] = None) -> None:
    """
    Atomically modifies properties of a study group
    :param module_code: The module that the group is for.
    :param group_id: The id of the group to modify.
    :param invite_only: Whether or not the group is invite_only.
    """
    pass

  @abc.abstractmethod
  def queue_for_study_group(self, module_code: str, member_id: int) -> bool:
    """
    Attempts to queue a user for a module
    :param module_code: The module that the user wants to join.
    :param member_id: The discord id of the user.
    :return: Whether or not the queuing was successful.
    """

  @abc.abstractmethod
  def unqueue_from_study_group(self, module_code: str, member_id: int) -> None:
    """
    Removes a user from the queue for a module
    :param module_code: The module that the user no longer wants to join.
    :param member_id: The discord id of the user.
    """

  @abc.abstractmethod
  def peek_queue_for_study_group(self, module_code: str, limit: int = 1) -> List[QueuedStudyGroupInfo]:
    """
    Gets the longest-waiting users for a module, but does not unqueue them.
    :param module_code: The module to get users for.
    :param limit: The maximum number of users to get.
    :return: The longest-waiting user for the given module. If less than `limit` values are returned, you can assume that those are the last.
    """

  def pop_queue_for_study_group(self, module_code: str, time_bound: Optional[datetime.datetime] = None) -> Optional[QueuedStudyGroupInfo]:
    """
    Gets the longest-waiting user for a module, and removes them from the queue.
    :param module_code: The module to get users for.
    :param time_bound: If this is set, then users that joined after `time_bound` will be ignored
    :return: The longest-waiting user for the given module
    """
    users = self.peek_queue_for_study_group(module_code, 1)
    if len(users) == 1:
      if time_bound is not None and users[0].time > time_bound:
        return None
      self.unqueue_from_study_group(module_code, users[0].member_id)
      return users[0]
    else:
      return None

class SqliteDatabaseDriver(DatabaseDriver):
  db : sqlite3.Connection

  @staticmethod
  def serialise_members(members: Set[int]) -> str:
    return ','.join(str(i) for i in members)

  @staticmethod
  def deserialise_members(members: str) -> Set[int]:
    return {int(i) for i in filter(None, members.split(','))}

  def add_module(self, module: ModuleInfo, overwrite: bool = False) -> bool:
    cur: sqlite3.Cursor

    # MAKE SURE THAT THIS IS A STATIC STRING!!! WE DO NOT WANT SQLi
    overwrite_sql = " ON CONFLICT(code) DO UPDATE SET name=excluded.name" if overwrite else "" # role_id=excluded.role_id, channel_id=excluded.

    with closing(self.db.cursor()) as cur:
      try:
        cur.execute("INSERT INTO modules(code, name) VALUES (?, ?)" + overwrite_sql,# , role_id, channel_id
                    (module.module_code, module.module_name)) # , module.role_id, module.channel_id
        self.db.commit()
        return True
      except sqlite3.Error as exn:
        if exn.sqlite_errorcode != sqlite3.SQLITE_CONSTRAINT_UNIQUE:
          raise
        return False

  def get_module(self, module_code: str) -> Optional[ModuleInfo]:
    cur: sqlite3.Cursor
    with closing(self.db.cursor()) as cur:
      cur.execute("SELECT code, name FROM modules WHERE code=? LIMIT 1", (module_code,)) # , role_id, channel_id
      res = cur.fetchone()
    if res is None:
      return None
    else:
      return ModuleInfo(module_code=res[0], module_name=res[1]) # , role_id=res[2], channel_id=res[3]

  def list_modules(self) -> Dict[str, ModuleInfo]:
    cur: sqlite3.Cursor
    with closing(self.db.cursor()) as cur:
      cur.execute("SELECT code, name FROM modules") # , role_id, channel_id
      res = cur.fetchall()
    return {i[0]: ModuleInfo(module_code=i[0], module_name=i[1]) for i in res} # , role_id=i[2], channel_id=i[3]

  def delete_module(self, module_code: str) -> None:
    with closing(self.db.cursor()) as cur:
      cur.execute("DELETE FROM modules WHERE code=? LIMIT 1", (module_code,))
      self.db.commit()

  def create_study_group(self, module_code: str, invite_only: bool) -> int:
    cur: sqlite3.Cursor
    with closing(self.db.cursor()) as cur:
      cur.execute("INSERT INTO study_groups(module_code, date_created, members, invite_only) VALUES (?, ?, ?, ?) RETURNING id",
                  (module_code, int(time.time()), "", invite_only))
      res = cur.fetchone()[0]
      self.db.commit()
      return res

  def get_study_group(self, module_code: str, group_id: int) -> Optional[StudyGroupInfo]:
    cur: sqlite3.Cursor
    with closing(self.db.cursor()) as cur:
      cur.execute("SELECT id, module_code, date_created, members, invite_only FROM study_groups WHERE module_code=? AND id=? LIMIT 1",
                  (module_code, group_id))
      res = cur.fetchone()
    if res is None:
      return None
    else:
      return StudyGroupInfo(id = res[0], module_code=res[1], date_created=datetime.datetime.utcfromtimestamp(res[2]), members=self.deserialise_members(res[3]), invite_only=res[4])

  def list_study_groups(self, module_code: str) -> Dict[int, StudyGroupInfo]:
    cur: sqlite3.Cursor
    with closing(self.db.cursor()) as cur:
      cur.execute("SELECT id, module_code, date_created, members, invite_only FROM study_groups WHERE module_code=?",
                  (module_code,))
      res = cur.fetchall()
    return {i[0]: StudyGroupInfo(id = i[0], module_code=i[1], date_created=datetime.datetime.utcfromtimestamp(i[2]), members=self.deserialise_members(i[3]), invite_only=i[4]) for i in res}

  def delete_study_group(self, module_code: str, group_id: int) -> None:
    with closing(self.db.cursor()) as cur:
      cur.execute("DELETE FROM study_groups WHERE module_code=? AND group_id=? LIMIT 1", (module_code, group_id))
      self.db.commit()

  def delete_all_study_groups(self, module_code: str) -> None:
    with closing(self.db.cursor()) as cur:
      cur.execute("DELETE FROM study_groups WHERE module_code=?", (module_code,))
      self.db.commit()

  def add_to_study_group(self, module_code: str, group_id: int, member: int) -> None:
    cur: sqlite3.Cursor
    with closing(self.db.cursor()) as cur:
      # This needs to be atomic, so we lock the entire db because sqlite doesn't have per-row/per-table locks
      cur.execute("BEGIN EXCLUSIVE")
      cur.execute("SELECT members FROM study_groups WHERE module_code=? AND id=? LIMIT 1", (module_code, group_id))
      res = cur.fetchone()
      if res is not None:
        members = self.deserialise_members(res[0])
        members.add(member)
        cur.execute("UPDATE study_groups SET members=? WHERE module_code=? AND id=? LIMIT 1", (self.serialise_members(members), module_code, group_id))
      cur.execute("COMMIT")

  def remove_from_study_group(self, module_code: str, group_id: int, member: int) -> None:
    cur: sqlite3.Cursor
    with closing(self.db.cursor()) as cur:
      # This needs to be atomic, so we lock the entire db because sqlite doesn't have per-row/per-table locks
      cur.execute("BEGIN EXCLUSIVE")
      cur.execute("SELECT members FROM study_groups WHERE module_code=? AND id=? LIMIT 1", (module_code, group_id))
      res = cur.fetchone()
      if res is not None:
        members = self.deserialise_members(res[0])
        members.remove(member)
        cur.execute("UPDATE study_groups SET members=? WHERE module_code=? AND id=? LIMIT 1", (self.serialise_members(members), module_code, group_id))
      cur.execute("COMMIT")


  def modify_study_group(self, module_code: str, group_id: int, invite_only: Optional[bool] = None) -> None:
    ur: sqlite3.Cursor
    with closing(self.db.cursor()) as cur:
      # This needs to be atomic, so we lock the entire db because sqlite doesn't have per-row/per-table locks
      cur.execute("BEGIN EXCLUSIVE")
      if invite_only is not None:
        cur.execute("UPDATE invite_only SET members=? WHERE module_code=? AND id=? LIMIT 1",
                    (invite_only, module_code, group_id))

      cur.execute("COMMIT")

  def queue_for_study_group(self, module_code: str, member_id: int) -> bool:
    cur: sqlite3.Cursor
    try:
      with closing(self.db.cursor()) as cur:
        cur.execute("INSERT INTO study_group_queue(module_code, member_id, time) VALUES (?, ?, ?)", (module_code, member_id, time.time()))
        self.db.commit()
      return True
    except sqlite3.Error as exn:
      if exn.sqlite_errorcode != sqlite3.SQLITE_CONSTRAINT_UNIQUE:
        raise
      return False

  def unqueue_from_study_group(self, module_code: str, member_id: int) -> None:
    cur: sqlite3.Cursor
    with closing(self.db.cursor()) as cur:
      cur.execute("DELETE FROM study_group_queue WHERE module_code=? AND member_id=? LIMIT 1", (module_code, member_id))
      self.db.commit()

  def peek_queue_for_study_group(self, module_code: str, limit: int = 1) -> List[QueuedStudyGroupInfo]:
    cur: sqlite3.Cursor
    with closing(self.db.cursor()) as cur:
      cur.execute("SELECT module_code, member_id, time FROM study_group_queue WHERE module_code=? LIMIT ?", (module_code, limit))
      return [QueuedStudyGroupInfo(module_code = res[0], member_id=res[1], time=datetime.datetime.utcfromtimestamp(res[2])) for res in cur.fetchall()]

  def init_db(self):
    cur: sqlite3.Cursor
    with closing(self.db.cursor()) as cur:
      cur.execute("CREATE TABLE IF NOT EXISTS modules ("
                  "code TEXT NOT NULL PRIMARY KEY UNIQUE,"
                  "name TEXT NOT NULL"
                  # "role_id INTEGER NOT NULL UNIQUE,"
                  # "channel_id INTEGER NOT NULL UNIQUE"
                  ")")
      cur.execute("CREATE TABLE IF NOT EXISTS study_groups ("
                  "id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,"
                  "module_code TEXT NOT NULL,"
                  "date_created INTEGER NOT NULL,"
                  "members TEXT NOT NULL,"
                  "invite_only BOOL NOT NULL,"
                  ""
                  "FOREIGN KEY (module_code) REFERENCES modules(code)"
                  ")")
      cur.execute("CREATE TABLE IF NOT EXISTS study_group_queue ("
                  "id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,"
                  "module_code TEXT NOT NULL,"
                  "member_id TEXT NOT NULL UNIQUE,"
                  "time BIGINT NOT NULL,"
                  ""
                  "FOREIGN KEY (module_code) REFERENCES modules(code)"
                  ")")
  def __init__(self, path: str):
    super().__init__()
    self.db = sqlite3.connect(path)


    cur: sqlite3.Cursor
    with closing(self.db.cursor()) as cur:
      cur.execute("PRAGMA foreign_keys = ON")

    # It's easier not to check, and just run the initialisation from scratch
    #
    # XXX: If this function ends up wiping things, then PLEASE DO THE CHECK FIRST
    self.init_db()

driver: DatabaseDriver
def load_db():
  global driver

  driver_type_l = cauch_e.config.obj["db"]
  if len(driver_type_l) != 1:
    print("Invalid config: there must be exactly one database driver specified")

  driver_type = next(iter(driver_type_l))
  db_conf = cauch_e.config.obj["db"][driver_type]

  match driver_type:
    case "sqlite": driver = SqliteDatabaseDriver(db_conf["path"])
    case _:
      raise cauch_e.config.BadConfig(f"Unknown driver type {driver_type}")
