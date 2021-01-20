# This isn't a traditional Makefile for compiling an application, it just serves as a shortcut for some commonly-needed development commands like dumping and reloading the database, running tests, etc.

all:
	docker-compose up
detached:
	docker-compose up -d
stop:
	docker-compose stop django
down:
	docker-compose down
attach:
	docker-compose exec django bash
db:
	docker-compose exec postgres psql -U admin -d authority
restart:
	docker-compose restart django nginx
check:
	docker-compose exec django python manage.py check
shell:
	docker-compose exec django python manage.py shell
build:
	docker-compose build
rebuild:
	docker-compose build --no-cache django
test:
	docker-compose exec django python manage.py test
blank: stop
	docker-compose exec postgres psql -U admin -d postgres -c 'DROP DATABASE authority;'
wipe: blank
	docker-compose exec postgres psql -U admin -d postgres -c 'CREATE DATABASE authority;'
	$(MAKE) restart
migrate: wipe
	docker-compose exec django python manage.py migrate
	$(MAKE) restoreusers
dumpusers:
	docker-compose exec django python manage.py dumpdata --indent 2 auth authtoken -e auth.permission -o /vol/data/bkp/users.json
restoreusers:
	docker-compose exec django python manage.py loaddata /vol/data/bkp/users.json
backup:
	docker-compose exec postgres pg_dump -U admin -d authority > data/bkp/bk.sql
restore: wipe
	docker-compose exec -T postgres psql -U admin -d authority < data/bkp/bk.sql
resetmigrations:
	find django -type f -regex ".*/migrations/[0-9].*" -exec rm {} \;
dumptest:
	docker-compose exec django python manage.py dumpdata authority entity auth --indent 2 -e auth.permission -e auth.group -o authority/fixtures/test.json
loadtest: migrate
	docker-compose exec django python manage.py loaddata authority/fixtures/test.json
reindex:
	docker-compose exec django python manage.py search_index --rebuild -f