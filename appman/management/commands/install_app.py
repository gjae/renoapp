import os
from django.core.management.base import BaseCommand
# pyrefly: ignore [missing-import]
from appman.resolver import Resolver, LocalAppFinder
from appman.payload import InstallAppPayload


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--mode', '-m', type=str, help='mode: [URL, LOCAL, MEMORY]', default="local")
        parser.add_argument('--app-code', '-a', type=str, help='app id', default="")
        parser.add_argument('--metadata-file', '-f', type=str, help='metadata file', default="__app__.json")
        parser.add_argument('--path', '-p', type=str, help='app path', default="")
        parser.add_argument('--url', '-u', type=str, help='url', default="")
        parser.add_argument("--tasks", "-t", nargs='+', help="tasks", default=[])

    def handle(self, *args, **options):
        mode = options.get('mode', 'local')
        app_code = options.get('app_code', '')
        metadata_file = options.get('metadata_file', '__app__.json')
        path = options.get('path', '')

        os.environ.setdefault("mode", mode)
        os.environ.setdefault("path", path)


        if mode.lower() in ["local", "l"] and path == "":
            raise ValueError("Path is required for local mode")

        if mode.lower() not in ["local", "l"] and mode.lower() not in ["url", "u"] and mode.lower() not in ["memory", "m"]:
            raise ValueError("Invalid mode")

        app = InstallAppPayload(app_code, path)
        finder = LocalAppFinder()
        resolver = Resolver(app, finder=finder, app_mode = mode, metadatafile=metadata_file)

        resolver.resolve()
        for installer in resolver.walk():
            installer.execute()
        
        

