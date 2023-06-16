from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db.models import UniqueConstraint


class User(AbstractUser):
    email = models.EmailField(
        verbose_name='email',
        unique=True,
        blank=False
    )
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=150,
        unique=True,
        blank=False,
        null=False
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150,
        unique=False,
        blank=False,
        null=False
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150,
        unique=False,
        blank=False,
        null=False
    )

    groups = models.ManyToManyField(
        Group,
        related_name='auth_user',
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.',
        related_query_name='user',
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='auth_user',
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.',
        related_query_name='user',
    )
    is_subscribed = models.BooleanField(
        verbose_name='Подписки?',
        default=False
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-id']


class Subscription(models.Model):
    """ Модель подписок. """

    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE,
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        related_name='author',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['user', 'author'],
                name='user_author_unique'
            )
        ]
        verbose_name = 'Подписка на автора'
        verbose_name_plural = 'Подписки на авторов'
        ordering = ['-id']

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
