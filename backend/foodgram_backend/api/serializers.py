from rest_framework import serializers, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.generics import get_object_or_404
import base64
from django.core.files.base import ContentFile
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Tags,
    Ingredients,
    Recipes,
    RecipeIngredient
)
from .validators import (
    validate_username,
    validate_email,
    validate_user_password,

)


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=150,
        required=True,
        validators=[validate_username]
    )
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
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


class ChangePasswordSerializer(UserSerializer):
    new_password = serializers.CharField(
        max_length=150,
        required=True,
        write_only=True
    )
    current_password = serializers.CharField(
        max_length=150,
        required=True,
        write_only=True
    )

    class Meta:
        fields = ['current_password', 'new_password']
        model = User

    def validate_current_password(self, current_password):
        return validate_user_password(current_password, self.instance)


class GetTokenSerializer(serializers.Serializer):
    email = serializers.CharField(
        max_length=150,
        required=True,
        allow_blank=False,
    )
    password = serializers.CharField(
        max_length=150,
        required=True,
        allow_blank=False
    )

    def validate_password(self, password):
        return validate_user_password(password, self.instance)


class TagsSerializer(serializers.ModelSerializer):

    class Meta:
        fields = (
            'id',
            'name',
            'color',
            'slug'
        )
        model = Tags
        # lookup_field = 'slug'


class IngredientAmountSerializer(serializers.ModelSerializer):
    """ Сериализатор модели, связывающей ингредиенты и рецепт. """

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'amount', 'measurement_unit']


class IngredientsSerializer(serializers.ModelSerializer):

    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit',
        )
        model = Ingredients


class RecipesSerializer(serializers.ModelSerializer):
    tags = TagsSerializer(read_only=True, many=True, required=False)
    # ingredients = IngredientsSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True, many=False)
    ingredients = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False)

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            # 'is_favorited',
            # 'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )
        model = Recipes
        # lookup_field = 'slug'

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return IngredientAmountSerializer(ingredients, many=True).data


class CustomUserSerializer(UserSerializer):
    """ Сериализатор модели пользователя. """

    # is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            # 'is_subscribed'
        ]


class AddIngredientRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор добавления ингредиента в рецепт. """

    id = serializers.IntegerField()
    amount = serializers.IntegerField()
    ingredient = serializers.CharField(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'ingredient', 'amount']


class CreateRecipesSerializer(serializers.ModelSerializer):
    """ Сериализатор создания/обновления рецепта. """

    author = UserSerializer(read_only=True)
    ingredients = AddIngredientRecipeSerializer(
        many=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tags.objects.all(), many=True
    )
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipes
        fields = [
            'id',
            'author',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        ]

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        lst = []
        for i in ingredients:
            amount = i['amount']
            if int(amount) < 1:
                raise serializers.ValidationError({
                   'amount': 'Количество ингредиента должно быть больше 0!'
                })
            if i['id'] in lst:
                raise serializers.ValidationError({
                   'ingredient': 'Ингредиенты должны быть уникальными!'
                })
            lst.append(i['id'])
        return data

    def create_ingredients(self, ingredients, recipe):
        for ingredient_id in ingredients:
            ingredient = Ingredients.objects.get(id=ingredient_id['id'])
            RecipeIngredient.objects.create(
                ingredient=ingredient,
                recipe=recipe,
                amount=ingredient_id['amount']
            )

    def create(self, validated_data):
        """
        Создание рецепта.
        Доступно только авторизированному пользователю.
        """

        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context.get('request').user
        recipe = Recipes.objects.create(
            author=author,
            **validated_data
        )
        recipe.tags.set(tags)
        for ingredient_id in ingredients:
            ingredient = Ingredients.objects.get(id=ingredient_id['id'])
            recipe.ingredients.add(ingredient)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """
        Изменение рецепта.
        Доступно только автору.
        """
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)
        instance.tags.set(validated_data.get('tags', instance.tags))
        ingredients = validated_data.pop('ingredients')
        for ingredient_id in ingredients:
            ingredient = Ingredients.objects.get(id=ingredient_id['id'])
            instance.ingredients.add(ingredient)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipesSerializer(instance, context={
            'request': self.context.get('request')
        }).data
