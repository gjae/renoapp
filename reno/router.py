from ninja import NinjaAPI, Router, Schema
from ninja_extra import NinjaExtraAPI, api_controller, ControllerBase, permissions, route

class RenoAPI(NinjaExtraAPI):
    prefix = ""
    
    def set_prefix(self, prefix):
        self.prefix = prefix

    def format_route_path(self, path: str) -> str:
        prefix = getattr(self, "prefix", "")
        if path.startswith("/"):
            path = path[1:]
        return f"{prefix}/{path}"

    def get(self, path, **kw):
        return super().get(self.format_route_path(path), **kw)

    def post(self, path, **kw):
        return super().post(self.format_route_path(path), **kw)

    def put(self, path, **kw):
        return super().put(self.format_route_path(path), **kw)

    def delete(self, path, **kw):
        return super().delete(self.format_route_path(path), **kw)

api = RenoAPI(title="RenoApp Core API", description="Centralized API for all modules")

__all__ = [
    "api", "Router", "Schema", "NinjaExtraAPI", 
    "NinjaAPI", "api_controller", "ControllerBase", "permissions", "route"
]
