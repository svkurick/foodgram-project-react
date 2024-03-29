from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import viewsets, filters, status
from django.db.models import Sum
from django.http import HttpResponse

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrAdminOrReadOnly
from .pagination import CustomPagination
from recipes.models import (
    Tags,
    Ingredients,
    Recipes,
    RecipeIngredient,
    Favorite,
    WishList
)
from users.models import Subscription
from .serializers import (
    UserSerializer,
    GetTokenSerializer,
    ChangePasswordSerializer,
    TagsSerializer,
    RecipesSerializer,
    IngredientsSerializer,
    CreateRecipesSerializer,
    FavoriteSerializer,
    SubscriptionSerializer,
    ShowSubscriptionsSerializer,
    WishListSerializer
)

User = get_user_model()


class GetTokenAPIView(APIView):
    """Получение токена."""
    permission_classes = (AllowAny,)
    serializer_class = GetTokenSerializer

    def post(self, request):
        user = get_object_or_404(User, email=request.data.get('email'))
        if user:
            serializer = self.serializer_class(user, data=request.data)
            if serializer.is_valid(raise_exception=True):
                refresh = RefreshToken.for_user(user)
                token = str(refresh.access_token)
            return Response({
                'auth_token': token
            }, status=status.HTTP_201_CREATED)
        return Response({
            'details': 'Нет такого пользователя'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def del_token(request):
    """Удаление токена."""
    token = RefreshToken(request.data.get('access'))
    token.blacklist()
    return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет модели пользователя."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('id',)

    def get_permissions(self):
        if self.action == 'create' or self.action == 'list':
            permission_classes = (AllowAny,)
        else:
            permission_classes = (IsAuthenticated,)
        return [permission() for permission in permission_classes]

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User(**serializer.validated_data)
        user.set_password(serializer.validated_data.get('password'))
        user.save()
        user = get_object_or_404(User, username=request.data.get('username'))

        return Response(
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,

            },
            status.HTTP_200_OK
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_me(request):
    """Страница пользователя, отправляющего запрос."""
    me = get_object_or_404(User, username=request.user)
    serializer = UserSerializer(me, many=False)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Смена пароля пользователя."""
    user = get_object_or_404(User, username=request.user)
    serializer = ChangePasswordSerializer(
        user,
        data=request.data
    )
    if serializer.is_valid(raise_exception=True):
        user.set_password(serializer.validated_data.get('new_password'))
        user.save()
    return Response(status=status.HTTP_204_NO_CONTENT)


class TagsViewSet(viewsets.ModelViewSet):
    """Вьюсет тэгов."""
    queryset = Tags.objects.all()
    pagination_class = None
    serializer_class = TagsSerializer
    permission_classes = (AllowAny,)


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет ингредиентов."""
    permission_classes = (AllowAny,)
    pagination_class = None
    serializer_class = IngredientsSerializer
    queryset = Ingredients.objects.all()
    filter_backends = [IngredientFilter, ]
    search_fields = ['^name', ]


class RecipesViewSet(viewsets.ModelViewSet):
    """Вьюсет рецептов."""
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    pagination_class = CustomPagination
    queryset = Recipes.objects.select_related('author').all()
    serializer_class = RecipesSerializer
    filter_backends = [DjangoFilterBackend, ]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipesSerializer
        return CreateRecipesSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context


class FavoriteView(APIView):
    """Добавление рецепта в избранное, удаление рецепта из избранного."""
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def post(self, request, id):
        data = {
            'user': request.user.id,
            'recipe': id
        }
        if not Favorite.objects.filter(
                user=request.user,
                recipe__id=id
        ).exists():
            serializer = FavoriteSerializer(
                data=data, context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        recipe = get_object_or_404(Recipes, id=id)
        if Favorite.objects.filter(
                user=request.user,
                recipe=recipe
        ).exists():
            Favorite.objects.filter(user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class SubscribeView(APIView):
    """Подписка на авторов, отписка от авторов."""
    permission_classes = (IsAuthenticated,)

    def post(self, request, id):
        data = {
            'user': request.user.id,
            'author': id
        }
        serializer = SubscriptionSerializer(
            data=data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        author = get_object_or_404(User, id=id)
        if Subscription.objects.filter(
                user=request.user, author=author
        ).exists():
            subscription = get_object_or_404(
                Subscription, user=request.user, author=author
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ShowSubscriptionsView(ListAPIView):
    """Отображение подписок пользователя."""
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def get(self, request):
        user = request.user
        queryset = User.objects.filter(author__user=user)
        page = self.paginate_queryset(queryset)
        serializer = ShowSubscriptionsSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class WishListView(APIView):
    """Добавление рецепта в список покупок, удаление из списка."""
    permission_classes = (IsAuthenticated,)

    def post(self, request, id):
        data = {
            'user': request.user.id,
            'recipe': id
        }
        recipe = get_object_or_404(Recipes, id=id)
        if not WishList.objects.filter(
                user=request.user, recipe=recipe
        ).exists():
            serializer = WishListSerializer(
                data=data, context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        recipe = get_object_or_404(Recipes, id=id)
        if WishList.objects.filter(
                user=request.user, recipe=recipe
        ).exists():
            WishList.objects.filter(user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def download_shopping_cart(request):
    """Скачать список покупок."""
    download_list = "Cписок покупок:"
    ingredients = RecipeIngredient.objects.filter(
        recipe__shopping_cart__user=request.user
    ).values(
        'ingredient__name', 'ingredient__measurement_unit'
    ).annotate(amount=Sum('amount'))
    for num, i in enumerate(ingredients):
        download_list += (
            f"\n{i['ingredient__name']} - "
            f"{i['amount']} {i['ingredient__measurement_unit']}"
        )
        if num < ingredients.count() - 1:
            download_list += ', '
    file_name = 'shopping_cart'
    response = HttpResponse(download_list, 'Content-Type: application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{file_name}.pdf"'
    return response
