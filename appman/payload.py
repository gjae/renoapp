from dataclasses import asdict
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
    version: str = ""
    description: str = ""
    require_migrate: bool = False
    require_restart: bool = False
    download_url: str = ""
    # Alias of app
    name: str = ""
    app_path_prefix: str = "apps"
    depends_on: List[str] = field(default_factory=list)
    paths: List[str] = field(default_factory=list)
    frontend: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "InstallAppPayload":
        from dataclasses import fields
        
        # Handle aliases
        if "name" in data and "app" not in data:
            data["app"] = data["name"]
        if "depends_on" in data and "dependencies" not in data:
            data["dependencies"] = data["depends_on"]
            
        # Filter only valid fields
        valid_keys = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        
        return cls(**filtered_data)
    
    