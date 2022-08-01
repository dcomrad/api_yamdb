import hashlib
import random
from datetime import datetime, timedelta

from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenViewBase
from reviews.models import (Category, ConfirmationCode, Genre, Review, Title,
                            User)

from .filters import TitlesFilter
from .mixins import ListCreateDestroyViewSet
from .permissions import IsAdmin, IsAdminOrReadOnly, IsOwnerOrReadOnly
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, ObtainTokenSerializer,
                          ReadOnlyTitleSerializer, RegistrationUserSerializer,
                          ReviewSerializer, TitleSerializer, UserSerializer)


class UserViewSet(viewsets.ModelViewSet):
    lookup_field = 'username'
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdmin,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)


class UserMeAPI(generics.RetrieveUpdateAPIView):
    """View-класс, отвечающий за управление собственной учётной записью"""
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


def get_confirmation_code(username, email) -> str:
    code = hashlib.sha256()
    code.update(random.choice(username).encode('utf-8'))
    code.update(username.encode('utf-8'))
    code.update(random.choice(email).encode('utf-8'))
    code.update(email.encode('utf-8'))
    code.update(str(random.randint(1, 100000)).encode('utf-8'))
    return code.hexdigest()


class UserRegistrationAPI(APIView):
    """View-класс, отвечающий за создание нового пользователя, формирование и
    отправку на email кода подтверждения
    """
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = RegistrationUserSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            email = serializer.validated_data['email']

            try:
                user = User.objects.get(username=username, email=email)
            except User.DoesNotExist:
                user = serializer.save()

            confirmation_code = get_confirmation_code(username, email)
            ConfirmationCode.objects.update_or_create(
                user=user,
                defaults={
                    'code': confirmation_code,
                    'expiration': datetime.now() + timedelta(hours=1)
                }
            )

            subject = 'Код подтверждения для получения JWT токена'
            message = ('Ваш код подтверждения для получения токена: '
                       f'"{confirmation_code}".\n'
                       'Код действителен в течение одного часа')
            user.email_user(subject, message, from_email=None)

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ObtainToken(TokenViewBase):
    serializer_class = ObtainTokenSerializer
    permission_classes = (AllowAny,)


class CategoryViewSet(ListCreateDestroyViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name",)
    lookup_field = "slug"


class GenreViewSet(ListCreateDestroyViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name",)
    lookup_field = "slug"


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all().annotate(
        Avg("reviews__score")
    ).order_by("name")
    serializer_class = TitleSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = TitlesFilter

    def get_serializer_class(self):
        if self.action in ("retrieve", "list"):
            return ReadOnlyTitleSerializer
        return TitleSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        title = get_object_or_404(Title, pk=self.kwargs.get("title_id"))
        return title.reviews.all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, id=title_id)
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        review = get_object_or_404(Review, pk=self.kwargs.get("review_id"))
        return review.comments.all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, id=review_id, title=title_id)
        serializer.save(author=self.request.user, review=review)
