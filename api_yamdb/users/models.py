from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(
        unique=True,
        verbose_name='Электронная почта'
    )

    bio = models.TextField(
        null=True,
        blank=True,
        verbose_name='Биография',
    )

    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'

    ROLE_CHOICES = (
        (USER, 'Аутентифицированный пользователь'),
        (MODERATOR, 'Модератор'),
        (ADMIN, 'Администратор'),
    )

    role = models.CharField(
        max_length=15,
        choices=ROLE_CHOICES,
        default=USER,
        verbose_name='Пользовательская роль',
    )

    @property
    def is_admin(self):
        return self.role == self.ADMIN or self.is_superuser

    @property
    def is_moderator(self):
        return self.role == self.MODERATOR

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
