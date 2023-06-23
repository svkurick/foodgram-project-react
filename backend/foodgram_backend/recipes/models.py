from .utils import slugify

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import (
    MinValueValidator, MaxValueValidator, RegexValidator
)


User = get_user_model()


class Tags(models.Model):
    """Модель тэгов для рецептов."""
    slug = models.SlugField(
        verbose_name='Slug',
        unique=True,
        max_length=50,
        blank=False,
        help_text='Если оставить пустым, то заполнится автоматически.'
    )
    name = models.CharField(
        verbose_name='Тэг',
        max_length=256,
    )
    color = models.CharField(
        max_length=7,
        validators=[
            RegexValidator(
                regex='^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
                message='Недопустимый Hex-код цвета'
            )
        ]
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ['-id']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name[:50])
        else:
            try:
                self.validate_unique()
            except ValueError:
                raise ValueError(
                    'Такой slug уже используется! Придумайте другой'
                )
        super().save(*args, **kwargs)


class Ingredients(models.Model):
    """Модель ингредиентов для рецептов."""
    name = models.CharField(
        verbose_name='Ингредиент',
        max_length=256,
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=256,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='recipe_measurement_unit_unique'
            )
        ]
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipes(models.Model):
    """Модель рецепта."""
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tags,
        verbose_name='Тэг',
        blank=True
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        null=False,
        default=None,
        blank=False
    )
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=256,
    )
    text = models.TextField(
        verbose_name='Описание рецепта',

    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=[
            MinValueValidator(0),
            MaxValueValidator(28800)
        ]
    )
    ingredients = models.ManyToManyField(
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
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """ Модель связи рецепта с ингредиентом."""
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.IntegerField(
        'Количество',
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5000)
        ]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='recipe_ingredient_unique'
            )
        ]
        ordering = ['-id']
        verbose_name = 'Количество ингридиента'
        verbose_name_plural = 'Количество ингридиентов'

    def __str__(self):
        return f'{self.recipe} - {self.ingredient}'


class Favorite(models.Model):
    """ Модель пользователя с избранным рецептом."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorites',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='user_favorite_unique'
            )
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class WishList(models.Model):
    """ Модель списка покупок."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='shopping_cart',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='user_shoppingcart_unique'
            )
        ]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'{self.user} - {self.recipe}'
