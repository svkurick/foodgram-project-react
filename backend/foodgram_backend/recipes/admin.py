from django.contrib import admin

from .models import (
    Tags,
    Ingredients,
    Recipes,
    RecipeIngredient,
    Favorite,
    WishList
    )


admin.site.register(Tags)
admin.site.register(Ingredients)
admin.site.register(Recipes)
admin.site.register(RecipeIngredient)
admin.site.register(Favorite)
admin.site.register(WishList)
