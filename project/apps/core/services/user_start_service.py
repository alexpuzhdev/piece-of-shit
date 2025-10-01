from asgiref.sync import sync_to_async

from project.apps.core.models import User


class UserService:
    @staticmethod
    @sync_to_async
    def get_or_create_from_aiogram(tg_user) -> User:
        user, created = User.objects.get_or_create(
            tg_id=tg_user.id,
            defaults={
                "username": tg_user.username,
                "first_name": tg_user.first_name,
                "last_name": tg_user.last_name,
                "is_bot": tg_user.is_bot,
                "language_code": tg_user.language_code,
            },
        )
        return user, created
