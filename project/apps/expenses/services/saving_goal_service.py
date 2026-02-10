from datetime import date
from decimal import Decimal

from asgiref.sync import sync_to_async

from project.apps.core.models import User
from project.apps.expenses.models import SavingGoal


class SavingGoalService:
    """Управление целями накопления."""

    @staticmethod
    @sync_to_async
    def create_goal(
        user: User,
        name: str,
        target_amount: Decimal,
        deadline: date | None = None,
    ) -> SavingGoal:
        return SavingGoal.objects.create(
            user=user,
            name=name,
            target_amount=target_amount,
            deadline=deadline,
        )

    @staticmethod
    @sync_to_async
    def close_goal(goal: SavingGoal) -> SavingGoal:
        """Завершает/закрывает цель (помечает как достигнутую)."""
        goal.is_achieved = True
        goal.save(update_fields=["is_achieved", "updated_at"])
        return goal

    @staticmethod
    @sync_to_async
    def add_to_goal(goal: SavingGoal, amount: Decimal) -> SavingGoal:
        """Добавляет сумму к цели. Если цель достигнута — помечает."""
        goal.current_amount += abs(amount)
        if goal.current_amount >= goal.target_amount:
            goal.is_achieved = True
        goal.save(update_fields=["current_amount", "is_achieved", "updated_at"])
        return goal

    @staticmethod
    @sync_to_async
    def get_active_goals(user: User) -> list[SavingGoal]:
        return list(
            SavingGoal.objects.filter(
                user=user,
                is_achieved=False,
                deleted_at__isnull=True,
            ).order_by("deadline", "created_at")
        )

    @staticmethod
    @sync_to_async
    def get_all_goals(user: User) -> list[SavingGoal]:
        return list(
            SavingGoal.objects.filter(
                user=user,
                deleted_at__isnull=True,
            ).order_by("-is_achieved", "deadline", "created_at")
        )

    @staticmethod
    def format_goal(goal: SavingGoal) -> str:
        """Форматирует цель для отображения в Telegram."""
        status_icon = "✅" if goal.is_achieved else "🎯"
        deadline_text = f"\n   📅 Дедлайн: {goal.deadline}" if goal.deadline else ""

        progress_bar = SavingGoalService._progress_bar(goal.progress_percent)

        return (
            f"{status_icon} <b>{goal.name}</b>\n"
            f"   {goal.current_amount:.0f} / {goal.target_amount:.0f} ₽ "
            f"({goal.progress_percent:.0f}%)\n"
            f"   {progress_bar}"
            f"{deadline_text}"
        )

    @staticmethod
    def _progress_bar(percent: Decimal, length: int = 10) -> str:
        filled = int(float(percent) / 100 * length)
        filled = min(filled, length)
        empty = length - filled
        return "▓" * filled + "░" * empty

    @staticmethod
    @sync_to_async
    def distribute_to_goals(goal_ids: list[int], total_amount: Decimal) -> list[SavingGoal]:
        """Распределяет общую сумму поровну между выбранными целями. Возвращает обновлённые цели."""
        if not goal_ids or total_amount <= 0:
            return []
        goals = list(
            SavingGoal.objects.filter(id__in=goal_ids, deleted_at__isnull=True, is_achieved=False)
        )
        if not goals:
            return []
        per_goal = (total_amount / len(goals)).quantize(Decimal("0.01"))
        remainder = total_amount - per_goal * len(goals)
        updated = []
        for i, goal in enumerate(goals):
            add_amount = per_goal + (remainder if i == 0 else Decimal("0"))
            goal.current_amount += add_amount
            if goal.current_amount >= goal.target_amount:
                goal.is_achieved = True
            goal.save(update_fields=["current_amount", "is_achieved", "updated_at"])
            updated.append(goal)
        return updated

    @staticmethod
    @sync_to_async
    def calculate_monthly_saving_needed(goal: SavingGoal) -> Decimal | None:
        """Сколько нужно откладывать в месяц для достижения цели к дедлайну."""
        if goal.is_achieved or not goal.deadline:
            return None

        today = date.today()
        if goal.deadline <= today:
            return goal.remaining

        months_remaining = (
            (goal.deadline.year - today.year) * 12
            + (goal.deadline.month - today.month)
        )

        if months_remaining <= 0:
            return goal.remaining

        return (goal.remaining / months_remaining).quantize(Decimal("0.01"))
