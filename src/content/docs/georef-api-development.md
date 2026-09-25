---
title: "Instalación y ejecución de Georef API"
---

Esta guía explica cómo levantar un servidor propio de la API Georef v2.1. Las versiones salen de la rama `development` del repositorio (`docker/Dockerfile_api`, `docker-compose.yml`, `.example.env` y `requirements.txt`).

## Dependencias

- Elasticsearch 7.17.9 (versión definida en `.example.env`; `requirements.txt` usa `elasticsearch-dsl==7.0.0`).
- Python 3.11 (imagen `python:3.11-trixie` de `docker/Dockerfile_api`).
- GDAL 3.10 (`gdal>=3.10,<3.11` en `requirements.txt`), GEOS y PROJ, necesarios para los formatos `shp` y `gpkg`.
- Flask 2.0.0, Shapely 2.0.7 y pyproj 3.6.1, entre otras (ver `requirements.txt`).

:::caution[A validar]
La rama `development` instala `georef-ar-address` desde la rama `development` de su repositorio (`-e git+https://github.com/datosgobar/georef-ar-address.git@development`), no desde una versión fija. Verificá qué versión corre en producción antes de reproducir resultados.
:::

## Opción A: Docker Compose

Es la forma que mantiene el repositorio. `docker-compose.yml` levanta dos contenedores: `georef-api_es01` (Elasticsearch, un solo nodo) y `georef-api_app` (la API con el servidor de desarrollo de Flask).

### 1. Clonar el repositorio

```bash
git clone https://github.com/datosgobar/georef-ar-api.git
cd georef-ar-api
git checkout development
```

### 2. Configurar

```bash
cp .example.env .env
cp config/georef.example.cfg config/georef.cfg
cp config/logging.example.ini config/logging.ini
```

`.env` define `ELASTIC_STACK_VERSION=7.17.9`, la memoria de la JVM (`JAVA_OPTS=-Xmx4096m -Xms4096m`) y el puerto del host (`APP_PORT=8080`, que se mapea al 5000 del contenedor).

En `config/georef.cfg`, completá `ES_HOSTS` con el host de Elasticsearch dentro de la red de Docker (el servicio se llama `es01`) y revisá las rutas o URLs de los archivos de datos (ver el paso 3). El contenedor monta `./source`, así que podés poner ahí los archivos NDJSON generados por el [ETL](/georef-ar-api/etl/) y apuntar las rutas a esa carpeta.

### 3. Levantar e indexar

```bash
docker compose up -d
docker compose exec app make index
```

Comprobá que la API responda:

```bash
curl "localhost:8080/api/v2.1/provincias"
```

Si modificás el código, reconstruí la imagen con `docker compose build app`.

:::caution[A validar]
El `README.md` de la rama `development` indica ejecutar `docker-compose` dentro de la carpeta `docker/` y usar el puerto 5000 del host, pero en esa rama `docker-compose.yml` está en la raíz y publica el puerto `$APP_PORT` (8080 en `.example.env`). También menciona `docker/georef.example.cfg`, que no existe en esa rama. Esta guía sigue los archivos, no el README.
:::

## Opción B: instalación manual

### 1. Elasticsearch

Instalá Elasticsearch 7.17 siguiendo la [guía para Debian/Ubuntu](https://www.elastic.co/guide/en/elasticsearch/reference/7.17/deb.html) en uno o más nodos y habilitá el servicio:

```bash
sudo systemctl enable --now elasticsearch
```

En `/etc/elasticsearch/elasticsearch.yml`, `node.name` tiene que ser único por nodo y todos los nodos tienen que compartir `cluster.name`:

```text
cluster.name: georef-ar-api
node.name: node-1
```

Ajustá el tamaño del heap de la JVM siguiendo las [recomendaciones de Elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/7.17/advanced-configuration.html) (usá el mismo valor como mínimo y máximo, por ejemplo 4 GB):

```text
-Xms4g
-Xmx4g
```

### 2. Repositorio y dependencias

```bash
git clone https://github.com/datosgobar/georef-ar-api.git
cd georef-ar-api
git checkout development
python3.11 -m venv env
source env/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp config/georef.example.cfg config/georef.cfg
cp config/logging.example.ini config/logging.ini
```

Para instalar el paquete `gdal` de Python necesitás las bibliotecas de sistema de GDAL 3.10 (en Debian: `gdal-bin`, `libgdal-dev`), además de GEOS y PROJ. Completá `config/georef.cfg` con los valores apropiados; los valores por defecto de `config/logging.ini` sirven para producción.

### 3. Crear los índices

La API indexa en Elasticsearch una serie de archivos NDJSON, cuya estructura está en [Modelo de datos](/georef-ar-api/etl-data/). En `config/georef.cfg` indicá una ruta local o una URL para cada archivo (`STATES_FILE`, `LOCAL_GOVERNMENTS_FILE`, `STREET_BLOCKS_FILE`, etc.), además del archivo de sinónimos (`SYNONYMS_FILE`) y el de términos excluyentes (`EXCLUDING_TERMS_FILE`). Los valores de `georef.example.cfg` apuntan a `https://infra.datos.gob.ar/georef/`.

:::caution[A validar]
Algunos nombres de archivo de `georef.example.cfg` no coinciden con los publicados. Por ejemplo, `LOCAL_GOVERNMENTS_FILE` apunta a `gobiernos_locales.ndjson` (existe), pero las URLs de descarga completa de gobiernos locales usan `gobierno_locales.*`. Revisá cada URL antes de indexar.
:::

Para indexar:

```bash
make index
```

Para listar los índices creados y otros datos:

```bash
make print_index_stats
```

### 4. (Opcional) Reindexar

`make index` actualiza los índices **solo si los datos nuevos son más recientes** que los indexados. Para forzar la reindexación sin importar la fecha, usá:

```bash
make index_forced
```

`index_forced` intenta usar un respaldo guardado si no puede acceder a los archivos configurados. Usala cuando cambian la estructura de los archivos, los mapeos o analizadores de Elasticsearch, o las listas de sinónimos o términos excluyentes.

Las dos recetas aceptan un índice puntual:

```bash
make index INDEX_NAME=localidades
make index_forced INDEX_NAME=calles
```

Índices disponibles:

- `provincias`, `provincias-geometria`
- `departamentos`, `departamentos-geometria`
- `aglomerados`, `aglomerados-geometria`
- `fracciones_censales`, `fracciones_censales-geometria`
- `radios_censales`, `radios_censales-geometria`
- `gobiernos_locales`, `gobiernos_locales-geometria`
- `localidades_censales`
- `asentamientos`
- `localidades`
- `calles`
- `intersecciones`
- `cuadras`
- `establecimientos_educativos`
- `instituciones_universitarias`

### 5. Ejecutar la API

Servidor de desarrollo (se reinicia solo cuando cambia el código; no apto para producción):

```bash
make start_dev_server
```

Con `gunicorn`:

```bash
make start_gunicorn_dev_server
```

Comprobá que funcione:

```bash
curl "localhost:5000/api/v2.1/provincias"
```

Para producción, seguí la guía de [entornos productivos](/georef-ar-api/deploy/).

## Tests

Con Elasticsearch activo y los datos cargados:

```bash
make test
```

Hay recetas separadas para tests contra datos reales (`make test_live`) y con mocks (`make test_mock`). Más información en [`tests/README.md`](https://github.com/datosgobar/georef-ar-api/blob/development/tests/README.md).

Para revisar estilo y errores comunes:

```bash
make code_checks
```

## *Profiling*

```bash
make start_profile_server
```

Cada consulta a `localhost:5000` guarda en `profile/` información sobre cuánto tardó. Los datos se generan con el módulo `cProfile` de Python.
