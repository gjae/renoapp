import json
from .payload import InstallAppPayload
from django.conf import settings
from .appman import Appman
from pathlib import Path


class BaseAppFinder:
    def __init__(self):
        pass

    def find(self, path: str):
        """
        Search for the app in the filesystem or in the web (future)
        """
        pass


class MockAppFinder(BaseAppFinder):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = kwargs.get("app", "mock_app")
        self.dependencies = kwargs.get("apps", [])
        self.tasks = kwargs.get("tasks", [])
        self.path = kwargs.get("path", "mock_app")


    def find(self, path: str):
        """
        Mock implementation for testing purposes
        """
        return InstallAppPayload(
            app=self.app,
            dependencies=self.dependencies,
            tasks=self.tasks,
            path=path
        )

class LocalAppFinder(BaseAppFinder):
    def find(self, path: str):
        """
        Mock implementation for testing purposes
        """
        with open(path, "r") as f:
            metadata = json.load(f)
            # path is like /ruta/B/__app__.json, we need the base dir (/ruta)
            metadata['path'] = str(Path(path).parent.parent)
            return InstallAppPayload.from_dict(metadata)

class Resolver:
    def __init__(self, payload: InstallAppPayload, finder: BaseAppFinder = None, app_mode = "url", metadatafile = "__app__.json"):
        self.payload = payload
        self.dependencies = set()
        self.finder = finder
        self.install_dependency_stack = []
        self.app_mode = app_mode
        self.metadatafile = metadatafile

    def check_dependencies(self):
        """
        Finds missing dependencies by checking against the current APP_GRAPH.
        Populates the `self.dependencies` set with apps that are not yet installed.
        """
        # Fallback to an empty dict if APP_GRAPH is not defined (e.g., during testing)
        app_graph = getattr(settings, 'APP_GRAPH', {})
        for dependency in self.payload.dependencies:
            if dependency not in app_graph:
                self.dependencies.add(dependency)


    def resolve_dependencies(self, visited_path=None):
        """
        Recursively resolves missing dependencies using DFS post-order.
        
        Args:
            visited_path (set, optional): Tracks the current resolution chain to prevent circular dependencies.
        """
        from pathlib import Path
        
        if visited_path is None:
            visited_path = set()
            
        if self.payload.app in visited_path:
            path_str = " -> ".join(list(visited_path) + [self.payload.app])
            raise ValueError(f"Circular dependency detected: {path_str}")
            
        # Mark the current app as visited in this resolution chain
        visited_path.add(self.payload.app)
        
        for dep in self.dependencies:
            dep_payload = self.finder.find((Path(self.payload.path) / dep / self.metadatafile))
            if not dep_payload:
                raise ValueError(f"Dependency '{dep}' could not be found by the AppFinder.")
                
            sub_resolver = Resolver(dep_payload, self.finder, self.app_mode, self.metadatafile)
            
            # Pass visited_path by copy to prevent conflicts across parallel branches
            sub_stack = sub_resolver.resolve(visited_path=visited_path.copy())
            
            # Prevent duplicate dependencies if multiple apps depend on the same underlying app
            for item in sub_stack:
                if not any(x.app == item.app for x in self.install_dependency_stack):
                    self.install_dependency_stack.append(item)


    def resolve(self, visited_path=None):
        """
        Resolves the full dependency tree and returns the ordered stack of payloads.
        
        Returns:
            list: An ordered list of InstallAppPayload objects (leaves first, root last).
        """
        self.check_dependencies()
        self.resolve_dependencies(visited_path=visited_path)
        
        # Append the current app at the end of the stack (Leaves first, Root last)
        if not any(x.app == self.payload.app for x in self.install_dependency_stack):
            self.install_dependency_stack.append(self.payload)
            
        return self.install_dependency_stack

    def get_downloader_mode(self, payload):
        from appman.utils import LocalPathDownloader, UrlDownloader, MemoryDownloader
        from pathlib import Path

        path_str = str(payload.path)
        path = payload.path if self.metadatafile not in path_str else Path("/".join(path_str.split("/")[:-2]))
        
        payload.path = path
        if self.app_mode == "local":
            return LocalPathDownloader(payload, self.metadatafile)
        elif self.app_mode == "url":
            return UrlDownloader(payload, self.metadatafile)
        elif self.app_mode == "memory":
            return MemoryDownloader(payload, self.metadatafile)
        else:
            raise ValueError("Invalid mode")

    def walk(self):
        """
        Executes all tasks in the resolved order.
        """
        for payload in self.install_dependency_stack:
            yield Appman(payload, self.get_downloader_mode(payload))