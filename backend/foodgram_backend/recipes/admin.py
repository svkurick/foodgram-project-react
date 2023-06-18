from django.contrib import admin

from .models import (
    Tags,
    Ingredients,
    Recipes,
    RecipeIngredient,
    Favorite,
    WishList
)


class RecipesAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorites_count')
    list_filter = ('author', 'name', 'tags')

    def favorites_count(self, obj):
        if Favorite.objects.filter(recipe=obj).exists():
            return Favorite.objects.filter(recipe=obj).count()
        return 0


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name', )


admin.site.register(Tags)
admin.site.register(Ingredients, IngredientAdmin)
admin.site.register(Recipes, RecipesAdmin)
admin.site.register(RecipeIngredient)
admin.site.register(Favorite)
admin.site.register(WishList)
