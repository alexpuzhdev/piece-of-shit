from project.apps.expenses.models import Category, CategoryAlias


class CategoryService:
    @staticmethod
    async def get_or_create(name: str) -> Category:
        normalized = name.strip().title()

        category = await Category.objects.filter(name__iexact=normalized).afirst()
        if category:
            return category

        alias = await CategoryAlias.objects.filter(alias__iexact=normalized).select_related("category").afirst()
        if alias:
            return alias.category

        alias = await CategoryAlias.objects.filter(alias__icontains=normalized).select_related("category").afirst()
        if alias:
            await CategoryAlias.objects.aget_or_create(alias=normalized, category=alias.category)
            return alias.category

        category = await Category.objects.filter(name__icontains=normalized).afirst()
        if category:
            await CategoryAlias.objects.aget_or_create(alias=normalized, category=category)
            return category

        category = await Category.objects.filter(name__iexact="Прочее").afirst()
        if category:
            await CategoryAlias.objects.aget_or_create(alias=normalized, category=category)
            return category

        category = await Category.objects.acreate(name="Прочее")
        await CategoryAlias.objects.acreate(alias=normalized, category=category)
        return category

    @staticmethod
    async def add_alias(category: Category, alias_name: str) -> CategoryAlias:
        normalized = alias_name.strip().title()
        alias, _ = await CategoryAlias.objects.aget_or_create(
            alias=normalized,
            category=category,
        )
        return alias
