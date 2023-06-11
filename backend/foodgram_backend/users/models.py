from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission


class User(AbstractUser):
    email = models.EmailField(
        verbose_name='email',
        unique=True,
        blank=True
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
        related_name='auth_user',  # Добавьте эту строку
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.',
        related_query_name='user',
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='auth_user',  # Добавьте эту строку
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.',
        related_query_name='user',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-id']

    # @property
    # def is_admin(self):
    #     return self.role == self.ADMIN or self.is_superuser or self.is_staff
    #
    # @property
    # def is_moderator(self):
    #     return self.role == self.MODERATOR
