from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
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
    # if username == 'me':
    #     raise serializers.ValidationError('Недопустимый username!')
    if not re.match(r'^[\w.@+-]+\Z', username):
        raise serializers.ValidationError(
            'Недопустимые символы')
    return username



