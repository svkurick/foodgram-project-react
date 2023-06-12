from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import viewsets, permissions, filters, status

from .serializers import (
    UserSerializer,
    GetTokenSerializer,
    ChangePasswordSerializer
)

User = get_user_model()


class GetTokenAPIView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = GetTokenSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data.get('email')
            user = get_object_or_404(User, email=email)
            refresh = RefreshToken.for_user(user)
            token = str(refresh.access_token)
        return Response({
            'auth_token': token
        }, status=status.HTTP_201_CREATED)


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

