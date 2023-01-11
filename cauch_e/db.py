import abc
import dataclasses
import datetime
from typing import Optional, List

import cauch_e.config

@dataclasses.dataclass
class ModuleInfo:
  module_code: str
  """The code (i.e. MATH101) of the module. Must be in all caps."""

  module_name: str
  """The full human-readable name of the module."""

@dataclasses.dataclass
class StudyGroupInfo:
  module_code: str
  """The code of the module the study group is for."""

  date_created: datetime.datetime
  """The time this group was created."""

  members: List[int]
  """A list of the members in this study group."""

class DatabaseDriver(abc.ABC):
  @abc.abstractmethod
  def add_module(self, module: ModuleInfo) -> None:
    """
    Creates a module in the database.
    :param module: The description of the module to add.
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
  def list_module(self) -> List[ModuleInfo]:
    """
    Creates a module in the database.
    :returns All of the modules in the database.
    """
    pass

  @abc.abstractmethod
  def delete_module(self, module_code: str) -> bool:
    """
    Deletes a module from the database.
    :param module_code: The code of the module to be deleted.
    :returns Whether the deletion was successful.
    """
    pass

  @abc.abstractmethod
  def create_study_group(self, module_code: str) -> int:
    """
    Creates a study group entry in the database.
    :param module_code: The module that the group is for.
    :return: The id of the created group
    """
    pass

  @abc.abstractmethod
  def get_study_group(self, module_code: str, group_id: int) -> Optional[StudyGroupInfo]:
    """
    Lists the study groups for a module
    :param module_code: The module that the group is for.
    :param group_id: The id of the group inside that module.
    :return: Information about the study group if successful, None otherwise.
    """
    pass

  @abc.abstractmethod
  def list_study_group(self, module_code: str) -> List[StudyGroupInfo]:
    """
    Lists the study groups for a module
    :param module_code: The module that the group is for.
    :return: All of the study groups for module_code in the database.
    """
    pass

  @abc.abstractmethod
  def delete_study_group(self, module_code: str, group_id: int) -> bool:
    """
    Lists the study groups for a module
    :param module_code: The module that the group is for.
    :param group_id: The id of the group inside that module to delete.
    :returns Whetherthe deletion was successful.
    """
    pass