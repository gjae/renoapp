from django.core.management.base import BaseCommand
from appman.resolver import Resolver


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

        if mode.lower() in ["local", "l"] and path == "":
            raise ValueError("Path is required for local mode")

        if mode.lower() not in ["local", "l"] and mode.lower() not in ["url", "u"]:
            raise ValueError("Invalid mode")

        resolver = Resolver(app_code, mode, metadata_file)

        for installer in resolver.walk():
            installer.execute()
        
        

