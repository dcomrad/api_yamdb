from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = get_user_model()


class ConfirmationCode(models.Model):
    user = models.OneToOneField(
        to=User,
        primary_key=True,
        on_delete=models.CASCADE,
    )
    code = models.TextField()
    expiration = models.DateTimeField()


class Genre(models.Model):
    name = models.CharField(
        verbose_name='Название жанра',
        max_length=200
    )
    slug = models.SlugField(
        verbose_name='Идентификатор жанра',
        unique=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Жанр'
        ordering = ['name']


class Category(models.Model):
    name = models.CharField(
        verbose_name='Название категории',
        max_length=200
    )
    slug = models.SlugField(
        verbose_name='Идентификатор категории',
        unique=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        ordering = ['name']


class Title(models.Model):
    name = models.CharField(
        max_length=400,
        verbose_name="Название произведения"
    )
    year = models.IntegerField(
        verbose_name="Год создания произведения"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание произведения"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='titles',
        verbose_name="Категория произведения"
    )
    genre = models.ManyToManyField(
        Genre,
        verbose_name="Жанр произведения"
    )
    rating = models.IntegerField(
        null=True,
        default=None,
        verbose_name='Рейтинг'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Произведение'
        ordering = ['name']


class GenreTitle(models.Model):
    title = models.ForeignKey(
        Title,
        verbose_name='Произведение',
        on_delete=models.CASCADE)
    genre = models.ForeignKey(
        Genre,
        verbose_name='Жанр произведения',
        on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.title}, жанр - {self.genre}'

    class Meta:
        verbose_name = 'Произведение и жанр'


class Review(models.Model):
    text = models.TextField(
        verbose_name='Текст',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    title = models.ForeignKey(
        Title,
        verbose_name='Произведение',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    score = models.PositiveSmallIntegerField(
        verbose_name='Рейтинг',
        validators=[
            MinValueValidator(1, 'Выберите от 1 до 10'),
            MaxValueValidator(10, 'Выберите от 1 до 10')
        ]
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['pub_date']
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_review'
            ),
        ]


class Comment(models.Model):
    text = models.TextField(
        verbose_name='Текст',
    )
    review = models.ForeignKey(
        Review,
        verbose_name='Отзыв',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['pub_date']
