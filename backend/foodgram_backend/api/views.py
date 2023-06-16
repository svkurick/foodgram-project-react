from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import viewsets, permissions, filters, status
from rest_framework_simplejwt.tokens import Token
from rest_framework_simplejwt.tokens import UntypedToken
import base64

from .permissions import IsAuthorOrAdminOrReadOnly
from .filters import IngredientsFilter
from .pagination import CustomPagination
from recipes.models import (
    Tags,
    Ingredients,
    Recipes,
    RecipeIngredient,
    Favorite
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
    ShowSubscriptionsSerializer
)

User = get_user_model()


class GetTokenAPIView(APIView):
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
    token = RefreshToken(request.data.get('access'))
    token.blacklist()
    return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('id',)

    def get_permissions(self):
        if self.action == 'create' or self.action == 'list':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
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
    me = get_object_or_404(User, username=request.user)
    serializer = UserSerializer(me, many=False)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
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
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    permission_classes = (AllowAny,)
    lookup_field = 'id'
    filter_backends = (filters.SearchFilter,)


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny, ]
    pagination_class = None
    serializer_class = IngredientsSerializer
    queryset = Ingredients.objects.all()
    filter_backends = [IngredientsFilter, ]
    search_fields = ['^name', ]


class RecipesViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    pagination_class = CustomPagination
    queryset = Recipes.objects.select_related('author').all()
    serializer_class = RecipesSerializer
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipesSerializer
        return CreateRecipesSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context


class FavoriteView(APIView):
    """ Добавление/удаление рецепта из избранного. """

    permission_classes = [IsAuthenticated, ]
    pagination_class = CustomPagination

    def post(self, request, id):
        data = {
            'user': request.user.id,
            'recipe': id
        }
        if not Favorite.objects.filter(
           user=request.user, recipe__id=id).exists():
            serializer = FavoriteSerializer(
                data=data, context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        recipe = get_object_or_404(Recipes, id=id)
        if Favorite.objects.filter(
           user=request.user, recipe=recipe).exists():
            Favorite.objects.filter(user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class SubscribeView(APIView):
    """ Операция подписки/отписки. """

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
           user=request.user, author=author).exists():
            subscription = get_object_or_404(
                Subscription, user=request.user, author=author
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ShowSubscriptionsView(ListAPIView):
    """ Отображение подписок. """

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
