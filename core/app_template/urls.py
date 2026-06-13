import json
from django.urls import path as url_path
from django.conf import settings
from .views import *

app_name = "{{app_name}}"


def get_urls():
    urlpatterns = []
    with open(f"{settings.BASE_DIR / 'apps' / app_name / '__app__.json'}", "r") as f:
        config = json.load(f)
        for path in config.get("paths", []):
            urlpatterns.append(
                url_path(path.get("url", ""), globals()[path.get("view", "")], name=path.get("name", ""))
        )
    return urlpatterns + [url_path("api/", api.urls),  ]


urlpatterns = get_urls()