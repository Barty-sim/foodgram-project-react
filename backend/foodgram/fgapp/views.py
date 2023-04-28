from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import status, Http404
from django.db.models import BooleanField, Exists, OuterRef, Value

from fgapp import services
from fgapp.filters import RecipeFilterSet, IngredientSearchFilter
from fgapp.models import (Recipe, Tag, Ingredient, FavoriteRecipe,
                          ShoppingCart)
from fgapp.pagination import CustomPageNumberPagination
from fgapp.permissions import AuthorOrReadOnly, RecipeAuthor, SubscribeOwner
from fgapp.serializers import (RecipeGetSerializer, RecipePostSerializer,
                               TagSerializer, IngredientSerializer,
                               SubscribeSerializer, FavoriteRecipeSerializer,
                               ShoppingCartSerializer)
from users.models import User, Subscribe


class ListModelViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    pass


class CreateDeleteModelViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    pass


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = (AuthorOrReadOnly,)
    pagination_class = CustomPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilterSet

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeGetSerializer
        return RecipePostSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Recipe.objects.all()

        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(FavoriteRecipe.objects.filter(
                    user=user, recipe__pk=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(ShoppingCart.objects.filter(
                    user=user, recipe__pk=OuterRef('pk'))
                )
            )
        else:
            queryset = queryset.annotate(
                is_favorited=Value(False, output_field=BooleanField()),
                is_in_shopping_cart=Value(False, output_field=BooleanField())
            )
        return 

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        response_serializer = RecipeGetSerializer(
            instance=serializer.instance
        )
        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED
        )

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    def partial_update(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = self.get_serializer(instance=recipe, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_serializer = RecipeGetSerializer(
            instance=serializer.instance
        )
        return Response(
            response_serializer.data, status=status.HTTP_200_OK
        )

    @action(detail=False, permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        return services.get_shopping_cart(self.request.user)


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientSearchFilter


class ShoppingCartViewSet(CreateDeleteModelViewSet):
    serializer_class = ShoppingCartSerializer
    permission_classes = (RecipeAuthor,)

    def get_queryset(self):
        return get_object_or_404(
            Recipe, id=self.kwargs.get('recipe_id')
        )

    def delete(self, request, recipe_id, format=None):
        recipe = get_object_or_404(
            Recipe, id=recipe_id
        )
        try:
            cart_item = get_object_or_404(
                ShoppingCart,
                user=self.request.user,
                recipe=recipe
            )
        except Http404:
            msg = f'Рецепт ({recipe.name}) уже отсутствует в списке покупок.'
            return Response(
                {'errors': msg}, status=status.HTTP_400_BAD_REQUEST
            )
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteRecipeViewSet(CreateDeleteModelViewSet):
    serializer_class = FavoriteRecipeSerializer
    permission_classes = (RecipeAuthor,)

    def get_queryset(self):
        return get_object_or_404(
            Recipe, id=self.kwargs.get('recipe_id')
        )

    def delete(self, request, recipe_id, format=None):
        recipe = get_object_or_404(
            Recipe, id=recipe_id
        )
        try:
            favorite = get_object_or_404(
                FavoriteRecipe,
                user=self.request.user,
                recipe=recipe
            )
        except Http404:
            msg = f'Рецепт ({recipe.name}) уже отсутствует в избранном.'
            return Response(
                {'errors': msg}, status=status.HTTP_400_BAD_REQUEST
            )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsViewSet(ListModelViewSet):
    serializer_class = SubscribeSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = (SubscribeOwner,)

    def get_queryset(self):
        subs_query = self.request.user.subscriber.all()
        subs_id_list = subs_query.values_list('subscribing', flat=True)
        return User.objects.filter(id__in=subs_id_list)


class SubscribeViewSet(CreateDeleteModelViewSet):
    serializer_class = SubscribeSerializer
    permission_classes = (SubscribeOwner,)

    def get_queryset(self):
        return get_object_or_404(
            User, id=self.kwargs.get('user_id')
        )

    def delete(self, request, user_id, format=None):
        author_for_unsubs = get_object_or_404(
            User, id=user_id
        )
        try:
            subscribe = get_object_or_404(
                Subscribe,
                user=self.request.user,
                subscribing=author_for_unsubs
            )
        except Http404:
            msg = f'Автор {author_for_unsubs} отсутствут в Ваших подписках.'
            return Response(
                {'errors': msg}, status=status.HTTP_400_BAD_REQUEST
            )
        subscribe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
