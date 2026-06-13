from dataclasses import dataclass, field
from typing import List, TypeAlias

@dataclass
class Task:
    name: str
    command: str
    

TaskList: TypeAlias = List[Task]
InstallScript: TypeAlias = list


@dataclass
class InstallAppPayload:
    """
    A dataclass that contains the payload for installing an app.
    This payload can be searched in app repository via requests 
    or injected as mock for testing
    """
    app: str
    path: str
    dependencies: List[str] = field(default_factory=list)
    tasks: TaskList = field(default_factory=list)
    post_install_tasks: InstallScript = field(default_factory=list)
    
    