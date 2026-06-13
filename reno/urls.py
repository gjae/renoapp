"""
URL configuration for reno project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
import logging
import importlib
from reno.router import api

logger = logging.getLogger('django.server')

urlpatterns = [
    path('admin/', admin.site.urls),
]

for app in settings.APP_GRAPH.keys():
    if app == "core":
        continue
    
    app_path = settings.APP_GRAPH[app]['path']
    path_prefix = settings.APP_GRAPH[app].get('app_path_prefix', '')
    logger.warning("App path: %s", app_path)
    logger.warning("Path prefix: %s", path_prefix)
    logger.warning("Full path: %s", path_prefix + app_path)
    logger.warning("Full path: %s", f"{app_path}.urls")

    path_prefix = path_prefix[1:] if path_prefix.startswith("/") else path_prefix
    path_prefix = path_prefix[:-1] if path_prefix.endswith("/") else path_prefix
    path_prefix = f"{path_prefix}/" if path_prefix else ""
    urlpatterns.append(
        path(f"{path_prefix}", include(f"{app_path}.urls"))
    )

    # Auto-discover API routers in views.py
    try:
        views_module = importlib.import_module(f"{app_path}.views")
        if hasattr(views_module, 'router'):
            router_prefix = path_prefix.strip('/')
            router_prefix = f"/{router_prefix}" if router_prefix else f"/{app}"
            api.add_router(router_prefix, views_module.router)
            
        if hasattr(views_module, "controllers"):
            # django-ninja-extra uses register_controllers instead of add_controller
            for controller in views_module.controllers:
                api.register_controllers(controller)
    except ImportError:
        pass

# Expose the central API
urlpatterns.append(path('api/', api.urls))
