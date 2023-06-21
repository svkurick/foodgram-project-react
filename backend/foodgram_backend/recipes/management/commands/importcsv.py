import json

from django.apps import apps
from django.core.management.base import BaseCommand

from recipes.models import Ingredients


class Command(BaseCommand):
    help = 'Import from .csv file to .postgresql'

    def add_arguments(self, parser):
        parser.add_argument("--path", type=str, help="file path")

    def handle(self, *args, **options):
        file_path = options["path"]
        with open(file_path, encoding='utf-8') as f:
            jsondata = json.load(f)
            for line in jsondata:
                if not Ingredients.objects.filter(
                        name=line['name'],
                        measurement_unit=line[
                            'measurement_unit']).exists():
                    Ingredients.objects.create(
                        name=line['name'],
                        measurement_unit=line['measurement_unit']
                    )
