import base64

from rest_framework import serializers, validators
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator, MaxValueValidator

from recipes.models import (
    Tags,
    Ingredients,
    Recipes,
    RecipeIngredient,
    Favorite,
    WishList
)
from users.models import Subscription
from .validators import (
    validate_username,
    validate_email,
    validate_user_password,
    validate_color
)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Сериализатор кодирования изображений в Base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор модели пользователя."""

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
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            "email",
            'first_name',
            'last_name',
            'is_subscribed',
            'password'
        )

    def get_is_subscribed(self, obj):
        """Метод указывает подписан ли юзер, делающий запрос, на автора."""

        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()


class ChangePasswordSerializer(UserSerializer):
    """Сериализатор смены пароля пользователя."""

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
        model = User
        fields = ('current_password', 'new_password')

    def validate_current_password(self, current_password):
        return validate_user_password(current_password, self.instance)


class GetTokenSerializer(serializers.Serializer):
    """Сериалилзатор получения токена."""

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
    """Сериализатор тэгов."""
    color = serializers.CharField(
        max_length=7,
        required=True,
        validators=[validate_color]
    )

    class Meta:
        model = Tags
        fields = (
            'id',
            'name',
            'color',
            'slug'
        )


class IngredientAmountSerializer(serializers.ModelSerializer):
    """ Сериализатор модели, связывающей рецепт с ингредиентами."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'amount', 'measurement_unit')


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredients
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class RecipesSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов."""

    author = UserSerializer(read_only=True, many=False)
    ingredients = serializers.SerializerMethodField(required=False)
    image = serializers.ImageField(required=True)
    tags = TagsSerializer(read_only=True, many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipes
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return IngredientAmountSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return WishList.objects.filter(
            user=request.user, recipe=obj
        ).exists()


class AddIngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор добавления ингредиента в рецепт."""

    id = serializers.IntegerField()
    ingredient = serializers.CharField(read_only=True)
    amount = serializers.IntegerField(
        validators=[MaxValueValidator(5000), MinValueValidator(1)]
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'ingredient', 'amount')


class CreateRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор создания и обновления рецепта."""

    author = UserSerializer(read_only=True)
    ingredients = AddIngredientRecipeSerializer(
        many=True,
        required=True
    )
    image = Base64ImageField(
        required=True,
        allow_null=False)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tags.objects.all(),
        many=True,
    )

    class Meta:
        model = Recipes
        fields = (
            'id',
            'author',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        lst = []
        for ingr in ingredients:
            amount = ingr['amount']
            if int(amount) < 1:
                raise serializers.ValidationError({
                    'amount': 'Количество ингредиента должно быть больше 0!'
                })
            if ingr['id'] in lst:
                raise serializers.ValidationError({
                    'ingredient': 'Ингредиенты должны быть уникальными!'
                })
            lst.append(ingr['id'])
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
        ingredients = validated_data.pop('ingredients')
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
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
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )
        instance.tags.set(validated_data.get('tags', instance.tags))
        old_ingredients = RecipeIngredient.objects.filter(recipe=instance)
        old_ingredients.delete()
        ingredients = validated_data.pop('ingredients')
        if len(ingredients) < 1:
            raise serializers.ValidationError({
                'ingredients': 'Количество ингредиента должно быть больше 0!'
            })
        for ingredient_id in ingredients:
            ingredient = Ingredients.objects.get(id=ingredient_id['id'])
            instance.ingredients.add(ingredient)
        self.create_ingredients(ingredients, instance)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipesSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data


class ShowFavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор отображения избранных рецептов."""

    class Meta:
        model = Recipes
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    """ Сериализатор избранных рецептов."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        return ShowFavoriteSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShowSubscriptionsSerializer(serializers.ModelSerializer):
    """ Сериализатор отображения подписок пользователя на авторов рецептов."""

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        recipes = Recipes.objects.filter(author=obj)
        limit = request.query_params.get('recipes_limit')
        if limit:
            recipes = recipes[:int(limit)]
        return ShowFavoriteSerializer(
            recipes, many=True, context={'request': request}).data

    def get_recipes_count(self, obj):
        return Recipes.objects.filter(author=obj).count()


class SubscriptionSerializer(serializers.ModelSerializer):
    """ Сериализатор подписок польщователя на авторов рецептов."""

    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['user', 'author'],
            )
        ]

    def to_representation(self, instance):
        return ShowSubscriptionsSerializer(
            instance.author,
            context={'request': self.context.get('request')}
        ).data


class WishListSerializer(serializers.ModelSerializer):
    """Сериализатор списка покупок."""

    class Meta:
        model = WishList
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        return ShowFavoriteSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
