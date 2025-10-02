DJANGO=django
BOT=bot

.PHONY: up down logs build shell migrate makemigrations superuser collectstatic bot restart logs-bot logs-django sh-bot

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build --no-cache

logs:
	docker compose logs -f

logs-bot:
	docker compose logs -f $(BOT)

logs-django:
	docker compose logs -f $(DJANGO)

shell:
	docker compose exec $(DJANGO) bash

sh-bot:
	docker compose exec $(BOT) bash

migrate:
	docker compose exec $(DJANGO) poetry run python -m project.manage migrate

makemigrations:
	docker compose exec $(DJANGO) poetry run python -m project.manage makemigrations

superuser:
	docker compose exec $(DJANGO) poetry run python -m project.manage createsuperuser

collectstatic:
	docker compose exec $(DJANGO) poetry run python -m project.manage collectstatic --noinput

bot:
	docker compose restart $(BOT)

restart:
	docker compose restart
