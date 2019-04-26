# Makefile para georef-ar-api
#
# Contiene recetas para ejecutar tests, correr servidores de prueba
# y generar la documentación.

CFG_PATH ?= config/georef.cfg
EXAMPLE_CFG_PATH = config/georef.example.cfg
INDEX_NAME ?= all
INDEXER_PY = service.management.indexer

.PHONY: docs

check_config_file:
	@test -f $(CFG_PATH) || \
		(echo "No existe el archivo de configuración $(CFG_PATH)." && exit 1)

index: check_config_file
	GEOREF_CONFIG=$(CFG_PATH) \
	python -m $(INDEXER_PY) -m index -n $(INDEX_NAME) -v

index_forced: check_config_file
	GEOREF_CONFIG=$(CFG_PATH) \
	python -m $(INDEXER_PY) -m index -n $(INDEX_NAME) -f -v

print_index_stats: check_config_file
	GEOREF_CONFIG=$(CFG_PATH) \
	python -m $(INDEXER_PY) -m index_stats -i

start_dev_server: check_config_file
	GEOREF_CONFIG=$(CFG_PATH) \
	FLASK_APP=service/__init__.py \
	FLASK_ENV=development \
	flask run

start_gunicorn_dev_server: check_config_file
	GEOREF_CONFIG=$(CFG_PATH) \
	gunicorn service:app -w 4 -k gevent --log-config=config/logging.ini -b 127.0.0.1:5000

start_profile_server:
	GEOREF_CONFIG=$(EXAMPLE_CFG_PATH) \
	gunicorn service:app -c service/management/gunicorn_profile.py -b 127.0.0.1:5000

test_live:
	GEOREF_CONFIG=$(EXAMPLE_CFG_PATH) \
	python -m unittest discover -p test_search_*

test_mock:
	GEOREF_CONFIG=$(EXAMPLE_CFG_PATH) \
	python -m unittest discover -p test_mock_*

# TEST_FILES se puede definir opcionalmente
test:
	GEOREF_CONFIG=$(EXAMPLE_CFG_PATH) \
	python -m unittest $(TEST_FILES)

code_checks:
	flake8 tests/ service/
	pylint tests/ service/

coverage:
	GEOREF_CONFIG=$(EXAMPLE_CFG_PATH) \
	coverage run --source=service --omit=service/management/* -m unittest
	coverage report

console:
	GEOREF_CONFIG=$(CFG_PATH) \
	python -c 'import service; service.georef_console()'

docs:
	mkdocs build
	rsync -vau --remove-source-files docs/site/ docs/
	rm -rf docs/site

servedocs:
	mkdocs serve

pdf:
	mkdocs_datosgobar md2pdf mkdocs.yml docs/georef-ar-api-docs.pdf
