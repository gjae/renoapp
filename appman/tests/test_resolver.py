import pytest
from appman.resolver import BaseAppFinder, Resolver
from appman.payload import InstallAppPayload
from appman.appman import Appman

class DictAppFinder(BaseAppFinder):
    """
    A simple finder that resolves apps from a pre-defined dictionary 
    where keys are app names and values are lists of dependencies.
    """
    def __init__(self, apps_dict):
        super().__init__()
        self.apps_dict = apps_dict
        
    def find(self, path):
        import pathlib
        if isinstance(path, pathlib.Path):
            app_name = path.parent.name
        else:
            app_name = str(path)
            
        if app_name in self.apps_dict:
            deps = self.apps_dict[app_name]
            return InstallAppPayload(
                app=app_name,
                dependencies=deps,
                tasks=[],
                path=app_name
            )
        return None

def test_linear_graph():
    """
    Tests a linear dependency graph: A -> B -> C.
    Expected installation order: C, B, A.
    """
    apps = {
        "A": ["B"],
        "B": ["C"],
        "C": []
    }
    finder = DictAppFinder(apps)
    resolver = Resolver(finder.find("A"), finder)
    
    stack = resolver.resolve()
    order = [item.app for item in stack]
    
    assert order == ["C", "B", "A"]


def test_diamond_graph_deduplication():
    """
    Tests deduplication in a diamond graph:
    A depends on B and C. Both B and C depend on D.
    Expected: D appears only once, before B and C. A is last.
    """
    apps = {
        "A": ["B", "C"],
        "B": ["D"],
        "C": ["D"],
        "D": []
    }
    finder = DictAppFinder(apps)
    resolver = Resolver(finder.find("A"), finder)
    
    stack = resolver.resolve()
    order = [item.app for item in stack]
    
    assert "D" in order
    assert order.count("D") == 1
    assert order.index("D") < order.index("B")
    assert order.index("D") < order.index("C")
    assert order[-1] == "A"


def test_circular_dependency():
    """
    Tests that a circular dependency raises a ValueError.
    Graph: A -> B -> C -> A
    """
    apps = {
        "A": ["B"],
        "B": ["C"],
        "C": ["A"]
    }
    finder = DictAppFinder(apps)
    resolver = Resolver(finder.find("A"), finder)
    
    with pytest.raises(ValueError, match="Circular dependency detected"):
        resolver.resolve()


def test_walk_generator():
    """
    Tests that the walk() generator correctly yields Appman instances 
    for each resolved payload in order.
    """
    apps = {
        "A": ["B"],
        "B": []
    }
    finder = DictAppFinder(apps)
    resolver = Resolver(finder.find("A"), finder)
    resolver.resolve()
    
    appman_instances = list(resolver.walk())
    
    assert len(appman_instances) == 2
    assert isinstance(appman_instances[0], Appman)
    assert appman_instances[0].payload.app == "B"
    assert appman_instances[1].payload.app == "A"
