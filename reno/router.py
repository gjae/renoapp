from ninja import NinjaAPI, Router, Schema
from ninja_extra import NinjaExtraAPI, api_controller, ControllerBase, permissions, route

api = NinjaExtraAPI(title="RenoApp Core API", description="Centralized API for all modules")

__all__ = [
    "api", "Router", "Schema", "NinjaExtraAPI", 
    "NinjaAPI", "api_controller", "ControllerBase", "permissions", "route"
]
