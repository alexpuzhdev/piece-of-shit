from dataclasses import dataclass

from project.apps.expenses.models import Category, CategoryAlias


@dataclass
class CategoryMatchResult:
    """Результат поиска категории."""
    category: Category
    is_exact_match: bool
    fell_back_to_other: bool  # True = категория неизвестна, попала в «Прочее»


class CategoryService:
    @staticmethod
    async def get_or_create(name: str) -> Category:
        """Совместимый с текущим API метод. Всегда возвращает Category."""
        result = await CategoryService.match(name)
        return result.category

    @staticmethod
    async def match(name: str) -> CategoryMatchResult:
        """Ищет категорию с подробным результатом матчинга."""
        normalized = name.strip().title()

        # 1. Точное совпадение по имени
        category = await Category.objects.filter(name__iexact=normalized).afirst()
        if category:
            return CategoryMatchResult(category=category, is_exact_match=True, fell_back_to_other=False)

        # 2. Точное совпадение по алиасу
        alias = await CategoryAlias.objects.filter(
            alias__iexact=normalized
        ).select_related("category").afirst()
        if alias:
            return CategoryMatchResult(category=alias.category, is_exact_match=True, fell_back_to_other=False)

        # 3. Частичное совпадение по алиасу → создаём новый алиас
        alias = await CategoryAlias.objects.filter(
            alias__icontains=normalized
        ).select_related("category").afirst()
        if alias:
            await CategoryAlias.objects.aget_or_create(alias=normalized, category=alias.category)
            return CategoryMatchResult(category=alias.category, is_exact_match=False, fell_back_to_other=False)

        # 4. Частичное совпадение по имени категории → создаём алиас
        category = await Category.objects.filter(name__icontains=normalized).afirst()
        if category:
            await CategoryAlias.objects.aget_or_create(alias=normalized, category=category)
            return CategoryMatchResult(category=category, is_exact_match=False, fell_back_to_other=False)

        # 5. Fallback → «Прочее»
        category = await Category.objects.filter(name__iexact="Прочее").afirst()
        if category:
            return CategoryMatchResult(category=category, is_exact_match=False, fell_back_to_other=True)

        category = await Category.objects.acreate(name="Прочее")
        return CategoryMatchResult(category=category, is_exact_match=False, fell_back_to_other=True)

    @staticmethod
    async def create_category(name: str) -> Category:
        """Создаёт новую категорию."""
        normalized = name.strip().title()
        category, _ = await Category.objects.aget_or_create(name=normalized)
        return category

    @staticmethod
    async def add_alias(category: Category, alias_name: str) -> CategoryAlias:
        """Добавляет алиас к категории."""
        normalized = alias_name.strip().title()
        alias, _ = await CategoryAlias.objects.aget_or_create(
            alias=normalized,
            category=category,
        )
        return alias

    @staticmethod
    async def get_all_categories() -> list[Category]:
        """Возвращает все категории для выбора."""
        return [cat async for cat in Category.objects.all().order_by("name")]

    @staticmethod
    async def get_expense_categories() -> list[Category]:
        """Категории, которые использовались в расходах."""
        from project.apps.expenses.models import Expense
        used_ids = set()
        async for expense in Expense.objects.filter(
            category__isnull=False, deleted_at__isnull=True,
        ).values_list("category_id", flat=True).distinct():
            used_ids.add(expense)
        if not used_ids:
            return await CategoryService.get_all_categories()
        return [
            cat async for cat in Category.objects.filter(id__in=used_ids).exclude(name="Прочее").order_by("name")
        ]

    @staticmethod
    async def get_income_categories() -> list[Category]:
        """Категории, которые использовались в доходах."""
        from project.apps.expenses.models import Income
        used_ids = set()
        async for income in Income.objects.filter(
            category__isnull=False, deleted_at__isnull=True,
        ).values_list("category_id", flat=True).distinct():
            used_ids.add(income)
        if not used_ids:
            return []
        return [
            cat async for cat in Category.objects.filter(id__in=used_ids).exclude(name="Прочее").order_by("name")
        ]

    @staticmethod
    async def get_or_create_exact(name: str) -> Category:
        """Создаёт категорию с точным именем или находит существующую.
        В отличие от get_or_create, не делает fuzzy-match через алиасы."""
        normalized = name.strip().title()
        category = await Category.objects.filter(name__iexact=normalized).afirst()
        if category:
            return category
        alias = await CategoryAlias.objects.filter(
            alias__iexact=normalized
        ).select_related("category").afirst()
        if alias:
            return alias.category
        category, _ = await Category.objects.aget_or_create(name=normalized)
        return category

    @staticmethod
    async def rename_category(category: Category, new_name: str) -> Category:
        """Переименовывает категорию."""
        normalized = new_name.strip().title()
        category.name = normalized
        await category.asave(update_fields=["name"])
        return category

    @staticmethod
    async def delete_category(category: Category) -> bool:
        """Удаляет категорию и её алиасы. Записи НЕ удаляются."""
        await CategoryAlias.objects.filter(category=category).adelete()
        await category.adelete()
        return True

    @staticmethod
    async def category_exists(name: str) -> bool:
        """Проверяет, существует ли категория с таким именем."""
        return await Category.objects.filter(name__iexact=name.strip().title()).aexists()
