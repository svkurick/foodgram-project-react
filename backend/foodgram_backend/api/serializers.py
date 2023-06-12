from rest_framework import serializers, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.generics import get_object_or_404
from django.contrib.auth.tokens import default_token_generator


from .validators import validate_username, validate_email


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=150,
        required=True,
        validators=[validate_username]
    )
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(
        max_length=254,
        required=True,
        validators=[validate_email]
    )
    password = serializers.CharField(
        max_length=150,
        required=True,
        write_only=True
    )

    class Meta:
        fields = (
            'id',
            'username',
            "email",
            'first_name',
            'last_name',
            'is_subscribed',
            'password'
        )
        model = User


class GetTokenSerializer(serializers.Serializer):
    email = serializers.CharField(
        max_length=150,
        required=True,
    )
    password = serializers.CharField(
        max_length=150,
        required=True,
    )

    def validate_password(self, password):
        email = self.initial_data.get('email')
        if email is None:
            raise serializers.ValidationError('Нельзя оставлять пустым')
        user = get_object_or_404(User, email=email)
        if not user.check_password(password):
            raise serializers.ValidationError('Некорректный пароль')
        return password
