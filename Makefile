BASE_CMD = python scripts/index_utils.py
TIMEOUT = 320

indexar_vias:
	$(BASE_CMD) indexar -n vias -c -t $(TIMEOUT)

borrar_vias:
	$(BASE_CMD) borrar -n vias -i

indexar_provincias:
	$(BASE_CMD) indexar -n provincias -c -t $(TIMEOUT)

borrar_provincias:
	$(BASE_CMD) borrar -n provincias -i

indexar_departamentos:
	$(BASE_CMD) indexar -n departamentos -c -t $(TIMEOUT)

borrar_departamentos:
	$(BASE_CMD) borrar -n departamentos -i

indexar_municipios:
	$(BASE_CMD) indexar -n municipios -c -t $(TIMEOUT)

borrar_municipios:
	$(BASE_CMD) borrar -n municipios -i

indexar_bahra:
	$(BASE_CMD) indexar -n bahra -c -t $(TIMEOUT)

borrar_bahra:
	$(BASE_CMD) borrar -n bahra -i

indexar_todos: \
	indexar_vias \
	indexar_provincias \
	indexar_departamentos \
	indexar_municipios \
	indexar_bahra

borrar_todos: \
	borrar_vias \
	borrar_provincias \
	borrar_departamentos \
	borrar_municipios \
	borrar_bahra

listar_indices:
	$(BASE_CMD) listar

