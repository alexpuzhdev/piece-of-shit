DJANGO=django
BOT=bot
DC=docker compose --env-file ../.env

.PHONY: up down logs build shell migrate makemigrations superuser collectstatic bot restart logs-bot logs-django rebuild

# ─── Запуск / остановка ──────────────────────────────
up:
	$(DC) up -d

down:
	$(DC) down

restart:
	$(DC) restart

rebuild:
	$(DC) down
	$(DC) build --no-cache
	$(DC) up -d

build:
	$(DC) build --no-cache

# ─── Логи ────────────────────────────────────────────
logs:
	$(DC) logs -f

logs-bot:
	$(DC) logs -f $(BOT)

logs-django:
	$(DC) logs -f $(DJANGO)

logs-db:
	$(DC) logs -f db

# ─── Shell ───────────────────────────────────────────
shell:
	$(DC) exec $(DJANGO) bash

sh-bot:
	$(DC) exec $(BOT) bash

sh-db:
	$(DC) exec db psql -U piece_of_shit_user -d piece_of_shit

# ─── Django management ───────────────────────────────
migrate:
	$(DC) exec $(DJANGO) python project/manage.py migrate

makemigrations:
	$(DC) exec $(DJANGO) python project/manage.py makemigrations

superuser:
	$(DC) exec $(DJANGO) python project/manage.py createsuperuser

collectstatic:
	$(DC) exec $(DJANGO) python project/manage.py collectstatic --noinput

# ─── Перезапуск отдельных сервисов ───────────────────
bot:
	$(DC) restart $(BOT)

django:
	$(DC) restart $(DJANGO)
