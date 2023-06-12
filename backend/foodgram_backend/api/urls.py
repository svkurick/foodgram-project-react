from django.urls import path, include
from rest_framework.routers import DefaultRouter
from djoser.views import TokenCreateView, TokenDestroyView


from .views import user_me, UserViewSet, GetTokenAPIView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('users/me/', user_me),
    # path('users/<id>/', user_id),
    # path('users/', RegistrationAPIView.as_view()),
    path('auth/token/login/', GetTokenAPIView.as_view()),
    path('', include(router.urls))
]
# urlpatterns = api_urlpatterns + router.urls
