from dataclasses import dataclass
from typing import List

@dataclass
class Task:
    name: str
    command: str
    

@dataclass
class InstallAppPayload:
    app: str
    dependencies: List[str]
    tasks: List[Task]
    path: str
    