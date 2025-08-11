PY=python

.PHONY: venv install lint fmt test run migrate makemigrations seed clearseed check

venv:
	python3 -m venv venv
	. venv/bin/activate && pip install -U pip

install:
	. venv/bin/activate && pip install -r requirements.txt && pip install pre-commit pytest pytest-django
	. venv/bin/activate && pre-commit install

lint:
	. venv/bin/activate && pre-commit run --all-files

fmt:
	. venv/bin/activate && ruff --fix . && ruff format . && isort .

test:
	. venv/bin/activate && pytest -q

run:
	. venv/bin/activate && python manage.py runserver 0.0.0.0:8000

migrate:
	. venv/bin/activate && python manage.py migrate

makemigrations:
	. venv/bin/activate && python manage.py makemigrations

check:
	. venv/bin/activate && python manage.py check && python manage.py makemigrations --check --dry-run

seed:
	. venv/bin/activate && python manage.py load_checklists && python manage.py populate_demo

clearseed:
	. venv/bin/activate && python manage.py clear_demo_data


