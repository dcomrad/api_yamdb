from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.auth.validators import UnicodeUsernameValidator
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from reviews.models import Category, Comment, Genre, Review, Title, User


class BaseUserValidation:
    @staticmethod
    def validate_username(username):
        if username == 'me':
            raise serializers.ValidationError(
                'Недопустимое имя пользователя'
            )
        return username


class UserSerializer(BaseUserValidation, serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'bio',
                  'role')

    def get_fields(self):
        fields = super().get_fields()
        user = self.context['request'].user
        if not user.is_admin:
            fields['role'].read_only = True
        return fields


class RegistrationUserSerializer(BaseUserValidation, serializers.Serializer):
    username_validator = UnicodeUsernameValidator()

    username = serializers.CharField(max_length=150,
                                     validators=[username_validator])
    email = serializers.EmailField()

    def create(self, validated_data):
        return User.objects.create(**validated_data)

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')

        if not User.objects.filter(username=username, email=email).exists():
            field = ''
            if User.objects.filter(username=username).exists():
                field = 'username'
            if User.objects.filter(email=email).exists():
                field = 'email'
            if field:
                error = {field: 'Пользователь уже существует'}
                raise serializers.ValidationError(error)
        return attrs


class ObtainTokenSerializer(serializers.Serializer):
    username = serializers.CharField()
    confirmation_code = serializers.CharField()

    @staticmethod
    def validate_username(value):
        if not User.objects.filter(username=value).exists():
            raise NotFound('Такого пользователя не существует')
        return value

    def validate(self, attrs):
        authenticate_kwargs = {
            'username': attrs.get('username'),
            'confirmation_code': attrs.get('confirmation_code'),
        }

        user = authenticate(**authenticate_kwargs)
        if not user:
            raise serializers.ValidationError(
                'Неверный код подтверждения или его срок истёк'
            )

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, user)

        return {"token": str(RefreshToken.for_user(user).access_token)}


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        exclude = ('id',)
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        exclude = ('id',)
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }


class TitleSerializer(serializers.ModelSerializer):
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        slug_field='slug',
        many=True
    )
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug'
    )

    class Meta:
        model = Title
        fields = '__all__'


class ReadOnlyTitleSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField(
        source='reviews__score__avg',
        read_only=True
    )
    genre = GenreSerializer(
        many=True
    )
    category = CategorySerializer()

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'genre', 'category'
        )


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
        read_only=True
    )

    def validate(self, data):
        request = self.context['request']
        author = request.user
        title_id = self.context['view'].kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        if request.method == 'POST':
            if Review.objects.filter(title=title, author=author).exists():
                raise ValidationError('Нельзя оставлять больше одного отзыва')
        return data

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'pub_date', 'score')


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
