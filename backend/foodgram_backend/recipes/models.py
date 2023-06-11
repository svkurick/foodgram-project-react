from django.db import models

from .utils import slugify
from users.models import User


class Tags(models.Model):
    """Модель с тегами для рецептов"""
    slug = models.SlugField(
        verbose_name='Slug',
        unique=True,
        max_length=50,
        blank=True,
        help_text='Если оставить пустым, то заполнится автоматически.'
    )
    name = models.CharField(
        verbose_name='Тэг',
        max_length=256,
    )
    color = models.CharField(max_length=16)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name[:50])
        super().save(*args, **kwargs)


class Ingredients(models.Model):
    """Модель с ингредиентами для рецептов"""
    name = models.CharField(
        verbose_name='Ингредиент',
        max_length=256,
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=256,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipes(models.Model):
    """Модель рецепта"""
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
    )
    tag = models.ManyToManyField(
        Tags,
        verbose_name='Тэг',
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        null=True,
        default=None
    )
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=256,
    )
    text = models.TextField(
        verbose_name='Описание рецепта',

    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в минутах'
    )
    ingredient = models.ManyToManyField(
        Ingredients,
        verbose_name='Ингредиент',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-id']

    def __str__(self):
        return self.name
