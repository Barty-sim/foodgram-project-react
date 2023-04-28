from django.contrib.admin import ModelAdmin, register
from django.contrib import admin

from fgapp.models import (Recipe, RecipeIngredients, Tag, Ingredient,
                          RecipeTags, FavoriteRecipe, ShoppingCart)
from users.models import User, Subscribe


@register(User)
class UserAdmin(ModelAdmin):
    list_display = (
        'pk', 'username', 'first_name', 'last_name', 'email'
    )
    search_fields = ('username',)
    list_filter = ('email', 'username')


@register(Subscribe)
class SubscribeAdmin(ModelAdmin):
    list_display = ('pk', 'user', 'subscribing')
    search_fields = ('user', 'subscribing',)
    list_filter = ('user', 'subscribing',)


class IngredientsInLine(admin.TabularInline):
    model = RecipeIngredients
    min_num = 1


class TagsInLine(admin.TabularInline):
    model = RecipeTags


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    inlines = [IngredientsInLine, TagsInLine]
    list_display = ('pk', 'author', 'name', 'text', 'pub_date')
    search_fields = ('name',)
    list_filter = ('tags', 'author', 'name')


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('pk', 'name', 'slug')
    search_fields = ('name',)
    list_filter = ('slug',)


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit', 'name')


@register(RecipeIngredients)
class RecipeIngredientsAdmin(ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe', 'ingredient')


@register(RecipeTags)
class RecipeTagsAdmin(ModelAdmin):
    list_display = ('pk', 'recipe', 'tag')
    search_fields = ('recipe', 'tag')


@register(FavoriteRecipe)
class FavoriteRecipeAdmin(ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user', 'recipe')


@register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user', 'recipe')
