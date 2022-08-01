from datetime import datetime

from reviews.models import ConfirmationCode, User


class AuthenticationByConfirmationCode:
    @staticmethod
    def authenticate(request, username=None, confirmation_code=None, **kwargs):
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)

            if ConfirmationCode.objects.filter(
                user_id=user.id,
                code=confirmation_code,
                expiration__gte=datetime.now()
            ).exists():
                return user

        return None

    @staticmethod
    def get_user(user_id):
        if User.objects.filter(pk=user_id).exists():
            return User.objects.get(pk=user_id)

        return None
