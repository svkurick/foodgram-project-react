from django.contrib import admin

from .models import Tags, Ingredients, Recipes


admin.site.register(Tags)
admin.site.register(Ingredients)
admin.site.register(Recipes)
