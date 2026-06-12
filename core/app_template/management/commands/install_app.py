import os
import subprocess
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path


class Command(BaseCommand):
    help = 'Instala una nueva aplicación en Reno'

    def handle(self, *args, **options):
        pass