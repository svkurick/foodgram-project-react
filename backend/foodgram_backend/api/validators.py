from rest_framework import serializers
import re

from users.models import User


def validate_email(email):
    if User.objects.filter(email=email).exists():
        raise serializers.ValidationError(
            'Пользователь с такой почтой уже зарегистрирован')
    return email


def validate_username(username):
    if User.objects.filter(username=username).exists():
        raise serializers.ValidationError(
            'Пользователь с таким псевдонимом уже зарегистрирован')
    if not re.match(r'^[\w.@+-]+\Z', username):
        raise serializers.ValidationError(
            'Недопустимые символы')
    return username


def validate_user_password(password, user):
    if not user.check_password(password):
        raise serializers.ValidationError('Некорректный пароль')
    return password



