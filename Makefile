BASE_CMD = python scripts/index_script.py
CFG_PATH = config/georef.cfg
TIMEOUT = 320

index:
	$(BASE_CMD) -t $(TIMEOUT) -c ../$(CFG_PATH)

start_dev_server:
	@test -f $(CFG_PATH) || \
		(echo "No existe el archivo de configuración $(CFG_PATH)." && exit 1)
	GEOREF_CONFIG=$(CFG_PATH) \
	FLASK_APP=service/__init__.py \
	FLASK_ENV=development \
	flask run
