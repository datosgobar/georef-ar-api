CFG_PATH ?= config/georef.cfg
TIMEOUT ?= 320

docs:
	mkdocs build
	$(BROWSER) site/index.html

servedocs:
	mkdocs serve

check_config_file:
	@test -f $(CFG_PATH) || \
		(echo "No existe el archivo de configuración $(CFG_PATH)." && exit 1)

index: check_config_file
	python scripts/utils_script.py -m index -t $(TIMEOUT) -c ../$(CFG_PATH)

index_forced: check_config_file
	python scripts/utils_script.py -m index -t $(TIMEOUT) -c ../$(CFG_PATH) -f

print_index_stats: check_config_file
	python scripts/utils_script.py -m index_stats -t $(TIMEOUT) -i -c ../$(CFG_PATH)

load_sql: check_config_file
	python scripts/utils_script.py -m run_sql -c ../$(CFG_PATH) -s scripts/function_geocodificar.sql

start_dev_server: check_config_file
	GEOREF_CONFIG=$(CFG_PATH) \
	FLASK_APP=service/__init__.py \
	FLASK_ENV=development \
	flask run

start_gunicorn_dev_server: check_config_file
	GEOREF_CONFIG=$(CFG_PATH) \
	gunicorn service:app -w 1 --log-config=config/logging.ini

test_live: check_config_file
	GEOREF_CONFIG=$(CFG_PATH) \
	python -m unittest tests/test_search_*

test_mock: check_config_file
	GEOREF_CONFIG=$(CFG_PATH) \
	python -m unittest tests/test_mock_*

test_all: test_live test_mock

code_style:
	flake8 tests service scripts
