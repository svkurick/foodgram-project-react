from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    user_me,
    UserViewSet,
    GetTokenAPIView,
    change_password,
    del_token,
    TagsViewSet,
    RecipesViewSet,
    IngredientsViewSet,
    FavoriteView,
    SubscribeView,
    ShowSubscriptionsView
)

router = DefaultRouter()
router.register(r'ingredients', IngredientsViewSet)
router.register(r'recipes', RecipesViewSet)
router.register(r'tags', TagsViewSet)
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('users/me/', user_me),
    path('auth/token/login/', GetTokenAPIView.as_view()),
    path('auth/token/logout/', del_token),
    path('users/set_password/', change_password),
    path('users/subscriptions/', ShowSubscriptionsView.as_view()),
    path('users/<int:id>/subscribe/', SubscribeView.as_view()),
    path(
        'recipes/<int:id>/favorite/', FavoriteView.as_view(), name='favorite'
    ),
    path('', include(router.urls))
]
