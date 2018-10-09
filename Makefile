CFG_PATH ?= config/georef.cfg
INDEX_NAME ?= all
UTILS_PY = service.management.utils_script

.PHONY: docs

check_config_file:
	@test -f $(CFG_PATH) || \
		(echo "No existe el archivo de configuración $(CFG_PATH)." && exit 1)

index: check_config_file
	GEOREF_CONFIG=$(CFG_PATH) \
	python -m $(UTILS_PY) -m index -n $(INDEX_NAME)

index_forced: check_config_file
	GEOREF_CONFIG=$(CFG_PATH) \
	python -m $(UTILS_PY) -m index -f -n $(INDEX_NAME)

print_index_stats: check_config_file
	GEOREF_CONFIG=$(CFG_PATH) \
	python -m $(UTILS_PY) -m index_stats -i

load_sql: check_config_file
	GEOREF_CONFIG=$(CFG_PATH) \
	python -m $(UTILS_PY) -m run_sql -s service/management/function_geocodificar.sql

start_dev_server: check_config_file
	GEOREF_CONFIG=$(CFG_PATH) \
	FLASK_APP=service/__init__.py \
	FLASK_ENV=development \
	flask run

start_gunicorn_dev_server: check_config_file
	GEOREF_CONFIG=$(CFG_PATH) \
	gunicorn service:app -w 4 --log-config=config/logging.ini -b 127.0.0.1:5000

test_live: check_config_file
	GEOREF_CONFIG=$(CFG_PATH) \
	python -m unittest discover -p test_search_*

test_mock: check_config_file
	GEOREF_CONFIG=$(CFG_PATH) \
	python -m unittest discover -p test_mock_*

test_custom: check_config_file
	GEOREF_CONFIG=$(CFG_PATH) \
	python -m unittest discover -p $(TEST_FILES) # Variable de entorno definida por el usuario

test_all: check_config_file
	GEOREF_CONFIG=$(CFG_PATH) \
	python -m unittest

code_checks:
	flake8 tests/ service/
	pylint tests/ service/

docs:
	mkdocs build

servedocs:
	mkdocs serve

docs_dist:
	mkdocs build
	rsync -avu docs/site/ docs/
	rm -rf docs/site

# Generar tablas de contenidos, se requiere el comando 'doctoc'
# https://github.com/thlorenz/doctoc
doctoc:
	doctoc --maxlevel 3 --github --notitle docs/src/quick-start.md
	bash docs/src/fix_github_links.sh docs/src/quick-start.md
	doctoc --maxlevel 3 --github --notitle docs/src/spreadsheet-integration.md
	bash docs/src/fix_github_links.sh docs/src/spreadsheet-integration.md
	doctoc --maxlevel 3 --github --notitle docs/src/python-usage.md
	bash docs/src/fix_github_links.sh docs/src/python-usage.md
	doctoc --maxlevel 3 --github --notitle docs/src/jwt-token.md
	bash docs/src/fix_github_links.sh docs/src/jwt-token.md
	doctoc --maxlevel 3 --github --notitle docs/src/georef-api-development.md
	bash docs/src/fix_github_links.sh docs/src/georef-api-development.md
	doctoc --maxlevel 3 --github --notitle docs/src/python3.6.md
	bash docs/src/fix_github_links.sh docs/src/python3.6.md
	doctoc --maxlevel 3 --github --notitle docs/src/georef-api-data.md
	bash docs/src/fix_github_links.sh docs/src/georef-api-data.md
