import os
from pathlib import Path
from django.core.management.base import BaseCommand
# pyrefly: ignore [missing-import]
from appman.resolver import Resolver, LocalAppFinder
from appman.payload import InstallAppPayload
from appman.utils import LocalFetcher
from rich.console import Console


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
        path_obj = Path(path)
        console = Console()

        os.environ.setdefault("mode", mode)
        os.environ.setdefault("path", path)

        if mode.lower() in ["local", "l"] and path == "":
            raise ValueError("Path is required for local mode")

        if mode.lower() not in ["local", "l"] and mode.lower() not in ["url", "u"] and mode.lower() not in ["memory", "m"]:
            raise ValueError("Invalid mode")
        
        
        console.rule(f"[bold blue]RenoApp Installer ({mode.upper()})[/bold blue]")

        with console.status(f"[bold green]Resolving dependencies for {app_code}...", spinner="dots"):
            app = InstallAppPayload(app_code, path)
            if mode.lower() in ["local", "l"]:
                app = (LocalFetcher(app, metadata_path=(path_obj / app_code / metadata_file) )).get_metadata()
            finder = LocalAppFinder()
            resolver = Resolver(app, finder=finder, app_mode = mode, metadatafile=metadata_file)
    
            resolver.resolve()
            
        console.print("[green]✔[/green] Dependencies resolved successfully")

        for installer in resolver.walk():
            current_app = installer.payload.app
            with console.status(f"[bold cyan]Installing {current_app}...", spinner="bouncingBar"):
                installer.execute()
            console.print(f"[green]✔[/green] App [bold]{current_app}[/bold] installed successfully.")
            
        console.rule("[bold green]Installation Complete[/bold green]")

        
        

