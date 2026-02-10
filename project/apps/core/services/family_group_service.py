import secrets
import string

from asgiref.sync import sync_to_async

from project.apps.core.models import User, FamilyGroup, FamilyGroupMembership


class FamilyGroupService:
    """Сервис управления семейными группами."""

    @staticmethod
    def _generate_invite_code(length: int = 8) -> str:
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    @sync_to_async
    def create_group(user: User, name: str) -> FamilyGroup:
        """Создаёт группу и добавляет создателя как администратора."""
        code = FamilyGroupService._generate_invite_code()
        # Гарантируем уникальность
        while FamilyGroup.objects.filter(invite_code=code).exists():
            code = FamilyGroupService._generate_invite_code()

        group = FamilyGroup.objects.create(
            name=name,
            created_by=user,
            invite_code=code,
        )
        FamilyGroupMembership.objects.create(
            group=group,
            user=user,
            role=FamilyGroupMembership.ROLE_ADMIN,
        )
        return group

    @staticmethod
    @sync_to_async
    def join_group(user: User, invite_code: str) -> FamilyGroupMembership | None:
        """Присоединяет пользователя к группе по коду приглашения.
        Возвращает None, если код не найден или уже в группе."""
        group = FamilyGroup.objects.filter(
            invite_code=invite_code.strip().upper(),
            deleted_at__isnull=True,
        ).first()

        if not group:
            return None

        membership, created = FamilyGroupMembership.objects.get_or_create(
            group=group,
            user=user,
            defaults={"role": FamilyGroupMembership.ROLE_MEMBER},
        )

        if not created:
            return None

        # select_related для доступа к group.name без дополнительного запроса
        return FamilyGroupMembership.objects.select_related("group").get(pk=membership.pk)

    @staticmethod
    @sync_to_async
    def get_user_groups(user: User) -> list[FamilyGroup]:
        """Возвращает группы пользователя."""
        return list(
            FamilyGroup.objects.filter(
                memberships__user=user,
                deleted_at__isnull=True,
            ).distinct()
        )

    @staticmethod
    @sync_to_async
    def get_group_members(group: FamilyGroup) -> list[FamilyGroupMembership]:
        """Возвращает участников группы."""
        return list(
            FamilyGroupMembership.objects.filter(
                group=group,
                deleted_at__isnull=True,
            ).select_related("user").order_by("role", "created_at")
        )

    @staticmethod
    @sync_to_async
    def get_group_member_ids(user: User) -> list[int]:
        """Возвращает ID всех пользователей из всех групп пользователя.
        Используется для фильтрации отчётов."""
        group_ids = FamilyGroupMembership.objects.filter(
            user=user,
            deleted_at__isnull=True,
        ).values_list("group_id", flat=True)

        member_user_ids = FamilyGroupMembership.objects.filter(
            group_id__in=group_ids,
            deleted_at__isnull=True,
        ).values_list("user_id", flat=True).distinct()

        return list(member_user_ids)

    @staticmethod
    @sync_to_async
    def get_notification_recipients(user: User) -> list[int]:
        """Возвращает список Telegram ID участников групп пользователя,
        у которых включены уведомления. Исключает самого пользователя.

        Используется для отправки уведомлений о расходах/доходах."""
        # Группы, в которых состоит пользователь
        user_group_ids = FamilyGroupMembership.objects.filter(
            user=user,
            deleted_at__isnull=True,
        ).values_list("group_id", flat=True)

        # Участники этих групп с включёнными уведомлениями, исключая автора
        recipient_tg_ids = (
            FamilyGroupMembership.objects.filter(
                group_id__in=user_group_ids,
                deleted_at__isnull=True,
                notifications_enabled=True,
            )
            .exclude(user=user)
            .select_related("user")
            .values_list("user__tg_id", flat=True)
            .distinct()
        )

        return list(recipient_tg_ids)

    @staticmethod
    @sync_to_async
    def toggle_notifications(user: User, group: FamilyGroup) -> bool:
        """Переключает уведомления для пользователя в группе.
        Возвращает новое значение notifications_enabled."""
        membership = FamilyGroupMembership.objects.filter(
            group=group,
            user=user,
            deleted_at__isnull=True,
        ).first()

        if not membership:
            return False

        membership.notifications_enabled = not membership.notifications_enabled
        membership.save(update_fields=["notifications_enabled", "updated_at"])
        return membership.notifications_enabled

    @staticmethod
    @sync_to_async
    def leave_group(user: User, group: FamilyGroup) -> bool:
        """Выходит из группы. Админ не может выйти, пока он единственный."""
        membership = FamilyGroupMembership.objects.filter(
            group=group,
            user=user,
            deleted_at__isnull=True,
        ).first()

        if not membership:
            return False

        if membership.role == FamilyGroupMembership.ROLE_ADMIN:
            admin_count = FamilyGroupMembership.objects.filter(
                group=group,
                role=FamilyGroupMembership.ROLE_ADMIN,
                deleted_at__isnull=True,
            ).count()
            if admin_count <= 1:
                return False

        membership.soft_delete()
        return True
