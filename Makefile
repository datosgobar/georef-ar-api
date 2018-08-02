CFG_PATH = config/georef.cfg
TIMEOUT = 320


check_config_file:
	@test -f $(CFG_PATH) || \
		(echo "No existe el archivo de configuración $(CFG_PATH)." && exit 1)

index: check_config_file
	python scripts/index_script.py -t $(TIMEOUT) -c ../$(CFG_PATH)

index_stats: check_config_file
	python scripts/index_script.py -i -c ../$(CFG_PATH)

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
