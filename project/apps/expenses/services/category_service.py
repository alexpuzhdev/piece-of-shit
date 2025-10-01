from project.apps.expenses.models import Category, CategoryAlias


class CategoryService:
    @staticmethod
    async def get_or_create(name: str) -> Category:
        normalized = name.strip().title()

        category = await Category.objects.filter(name__iexact=normalized).afirst()
        if category:
            return category

        alias = await CategoryAlias.objects.select_related("category").filter(alias__iexact=normalized).afirst()
        if alias:
            return alias.category

        category = await Category.objects.acreate(name=normalized)
        return category

    @staticmethod
    async def add_alias(category: Category, alias_name: str) -> CategoryAlias:
        normalized = alias_name.strip().title()
        alias, _ = await CategoryAlias.objects.aget_or_create(
            alias=normalized,
            category=category,
        )
        return alias
