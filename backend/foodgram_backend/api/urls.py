from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import user_me, UserViewSet, GetTokenAPIView, change_password

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('users/me/', user_me),
    path('auth/token/login/', GetTokenAPIView.as_view()),
    path('users/set_password/', change_password),
    path('', include(router.urls))
]
