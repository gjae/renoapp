from dataclasses import dataclass
from typing import List

@dataclass
class Task:
    name: str
    command: str
    

@dataclass
class InstallAppPayload:
    """
    A dataclass that contains the payload for installing an app.
    This payload can be searched in app repository via requests 
    or injected as mock for testing
    """
    app: str
    dependencies: List[str]
    tasks: List[Task]
    path: str
    