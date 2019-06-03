# Instalación y ejecución de Georef API

En este documento se detallan los pasos a seguir si se desea configurar un servidor de Georef API propio.

## Dependencias

- Elasticsearch >= 7.0.0
- Python >= 3.6.0

A continuación, se detallan los pasos a seguir para instalar y ejecutar la API en un entorno Ubuntu 16.04 (Xenial).

## Instalación

### 1. Elasticsearch

Para instalar Elasticsearch, seguir las siguientes instrucciones en uno o más servidores (nodos).

#### 1.1 Instalar Elasticsearch

Instalar Elasticsearch siguiendo la [guía de instalación para Debian/Ubuntu](https://www.elastic.co/guide/en/elasticsearch/reference/current/deb.html).

#### 1.2 Habiliar el servicio `elasticsearch`

Asegurar que el servicio `elasticsearch` está habilitado utilizando `systemctl`:
```bash
$ sudo systemctl start elasticsearch
$ sudo systemctl enable elasticsearch
```

#### 1.3 Aplicar las configuraciones recomendadas

Editar el archivo  `/etc/elasticsearch/elasticsearch.yml`. El valor de `node.name` debe ser único por nodo, y todos los nodos deben tener el mismo valor de `cluster.name`:

```text
cluster.name: georef-ar-api
node.name: node-1
```

Editar el archivo `/etc/elasticsearch/jvm.options` (siguiendo las [recomendaciones de Elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/heap-size.html)):
```text
# Tamaño del heap size de la JVM
# Se recomienda utilizar siempre el mismo valor como mínimo y máximo
# Ejemplo: 4 GB
-Xms4g
-Xmx4g
```

### 2. Repositorio y dependencias

#### 2.1 Clonar el repositorio:
```bash
$ git clone https://github.com/datosgobar/georef-ar-api.git
$ cd georef-ar-api
```

#### 2.2 Crear un entorno virtual y activarlo
```bash
$ python3 -m venv env
$ source env/bin/activate
```

#### 2.3 Instalar dependencias con `pip`
```bash
(env) $ pip3 install -r requirements.txt -r requirements-dev.txt
```

#### 2.4 Copiar el archivo de configuración
```bash
(env) $ cp config/georef.example.cfg config/georef.cfg
```

Luego, completar el archivo `config/georef.cfg` con los valores apropiados.

#### 2.5 Copiar el archivo de configuración de logs
```bash
(env) $ cp config/logging.example.ini config/logging.ini
```

Luego, completar el archivo `config/logging.ini` con los valores apropiados. Los valores por defecto son válidos y pueden ser utilizados en entornos productivos.

### 3. Crear los índices
El siguiente paso es indexar todos los datos de entidades geográficas en Elasticsearch, para poder consultarlos vía el servidor de la API. Para lograr esto, la API acepta una serie de archivos NDJSON donde deberían estar almacenados los datos. La estructura de dichos archivos está detallada en [este documento](etl-data.md).

El archivo de configuración `config/georef.cfg` debe especificar una ruta local o una URL externa para cada archivo de datos NDJSON. Notar que los valores por defecto (en `georef.example.cfg`) utilizan el portal de descargas `infra.datos.gob.ar`, que siempre provee la última versión de los archivos NDJSON disponibles. La rama `master` de `georef-ar-api` siempre se mantiene compatible con la última versión de los datos disponibles en `infra.datos.gob.ar`. El archivo de configuración también debe especificar la URL del archivo de sinónimos para utilizar al momento de indexar campos de texto en Elasticsearch. El valor por defecto en `georef.example.cfg` también puede ser utilizado, ya que utiliza la versión del archivo almacenado en `infra.datos.gob.ar`. El mismo criterio se aplica al archivo de términos excluyentes. En resumen, si se utilizó `georef.example.cfg` como base para configurar la API, las URLs de los archivos ya deberían estar configuradas correctamente.

Para indexar los datos, ejecutar:
```bash
(env) $ make index
```

Listar los índices creados, y otros datos adicionales:
```bash
(env) $ make print_index_stats
```
	
### 4. (Opcional) Re-indexar datos
Si se modifican los archivos de datos NDJSON, es posible re-indexarlos sin borrar los índices ya existentes. Dependiendo del comportamiento que se desee, se debe tomar una opción:

#### Indexar datos nuevos
Si se desea actualizar los índices con los nuevos datos, **pero solo si los datos entrantes son más recientes que los ya indexados**, se puede utilizar nuevamente la receta `index`:
  
```bash
(env) $ make index
```

#### Forzar re-indexado
Si se desea forzar un re-indexado, es decir, si se desea indexar los datos nuevamente sin importar la fecha de creación, se debe utilizar la siguiente receta:

```bash
(env) $ make index_forced
```

La receta `index_forced` intenta utilizar un archivo de respaldo guardado anteriormente si no pudo acceder a los archivos especificados en `config/georef.cfg`. El uso de la receta es recomendado cuando se requiere re-indexar los datos incondicionalmente. Algunas de las situaciones donde esto es necesario son:

- Modificación de la estructura de los archivos de datos
- Modificación de *mappeos* de tipos de Elasticsearch
- Modificación de analizadores de texto de Elasticsearch
- Modificación de listado de sinónimos
- Modificación de listado de términos excluyentes


Cualquiera de las dos opciones también permite indexar datos selectivamente: se debe especificar el nombre del índice a crear/re-indexar. Por ejemplo:
```bash
(env) $ make index INDEX_NAME=localidades
(env) $ make index_forced INDEX_NAME=calles
```

Los nombres de los índices disponibles son:

- `provincias`
- `provincias-geometria`
- `departamentos`
- `departamentos-geometria`
- `municipios`
- `municipios-geometria`
- `localidades-censales`
- `asentamientos`
- `localidades`
- `calles`
- `intersecciones`
- `cuadras`

### 5. Ejecutar la API 
#### Entornos de desarrollo
Ejecutar la API de Georef utilizando un servidor de prueba (no apto para producción):
```bash
(env) $ make start_dev_server
```

El servidor lanzado con `start_dev_server` se reinicia automáticamente cuando se modifica el código de la API. Esto es útil al momento de agregar nuevas funcionalidades.

También es posible ejecutar la API utilizando `gunicorn` como servidor HTTP:
```bash
(env) $ make start_gunicorn_dev_server
```

Para comprobar que la API esté funcionando:
```bash
$ curl localhost:5000/api/provincias
```

Si se desea preparar la API para uso en entornos productivos, consultar la guía de instalación para [entornos productivos](deploy.md).

## Tests
Para ejecutar los tests unitarios (el servicio Elasticsearch debe estar activo y con los datos apropiados cargados):
```bash
(env) $ make test
```

Para más información sobre los tests, ver el archivo [`tests/README.md`](https://github.com/datosgobar/georef-ar-api/blob/master/tests/README.md).


Para comprobar que no existan errores comunes en el código, y que su estilo sea correcto:
```bash
(env) $ make code_checks
```

## *Profiling*
Es posible realizar pruebas de *performance* de la API utilizando el siguiente comando:
```bash
(env) $ make start_profile_server
```

Luego, al realizar cualquier consulta a `localhost:5000`, se almacenará en el directorio `profile/` información sobre el tiempo que llevó completar la consulta. Los datos se generan utilizando el módulo `cProfile` de Python.
