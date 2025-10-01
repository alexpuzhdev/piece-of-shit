# Имя сервиса в docker-compose
DJANGO=django
BOT=bot

.PHONY: up down logs build shell migrate makemigrations superuser collectstatic bot

# Запуск всех контейнеров
up:
	docker compose up --build -d

# Остановка всех контейнеров
down:
	docker compose down

# Пересборка контейнеров
build:
	docker compose build --no-cache

# Логи (все сервисы)
logs:
	docker compose logs -f

# Попасть внутрь контейнера Django
shell:
	docker compose exec $(DJANGO) bash

# Применить миграции
migrate:
	docker compose exec $(DJANGO) poetry run python -m project.manage migrate

# Создать новые миграции
makemigrations:
	docker compose exec $(DJANGO) poetry run python -m project.manage makemigrations

# Создать суперпользователя
superuser:
	docker compose exec $(DJANGO) poetry run python -m project.manage createsuperuser

# Собрать статику
collectstatic:
	docker compose exec $(DJANGO) poetry run python -m project.manage collectstatic --noinput

# Перезапустить бота
bot:
	docker compose restart $(BOT)

docker exec -it expenses_django poetry run python -m project.manage makemigrations
