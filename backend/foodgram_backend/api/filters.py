from django_filters import rest_framework as filter
from rest_framework.filters import SearchFilter

from recipes.models import Recipes, Tags


class IngredientsFilter(SearchFilter):
    search_param = 'name'