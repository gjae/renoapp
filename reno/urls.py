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
import importlib
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from pathlib import Path
import logging
import importlib
from reno.router import api

logger = logging.getLogger('django.server')

urlpatterns = [
    path('admin/', admin.site.urls),
]

app_path = Path(settings.BASE_DIR / "apps")

for app in app_path.iterdir():
    if not app.is_dir():
        continue
    
    app_dir = Path(app)
    if app_dir.is_dir() and (app_dir / "__app__.json").exists():
        try:
            # Inject the app prefix into the global API before importing the views
            # This allows @api.get() inside the app to be automatically prefixed!
            api.set_prefix(f"/{app_dir.name}")
            views_module = importlib.import_module(f"apps.{app_dir.name}.views")
            
            # Dynamically attach the app's router under the /api/<app_name>/ prefix
            if hasattr(views_module, 'router'):
                api.add_router(f"/{app_dir.name}", views_module.router)
                
            if hasattr(views_module, "controllers") and len(getattr(views_module, "controllers")) > 0:
                for controller in views_module.controllers:
                    api.register_controllers(controller)
        except ImportError:
            pass

# Mount the centralized Ninja API ONCE after all routers and controllers have been added
urlpatterns += [
    path('api/', api.urls),
]