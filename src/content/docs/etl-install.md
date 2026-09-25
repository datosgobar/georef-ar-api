---
title: "Instalación y Ejecución de Georef ETL"
---

En este documento se detallan los pasos a seguir si se desea ejecutar el ETL de Georef en un entorno propio.

## Dependencias

Según la rama `development` de [georef-ar-etl](https://github.com/datosgobar/georef-ar-etl) (último commit revisado: `7cfcb02`, 16/04/2026), el ETL usa:

- PostgreSQL 17 con PostGIS 3 (imagen `postgres:17-bullseye` de `docker/Dockerfile_db`).
- Python 3.12 (imagen `python:3.12-slim-bullseye` de `docker/Dockerfile_app`) con SQLAlchemy 1.3.3, GeoAlchemy2 0.6.1, Alembic 1.0.9 y Shapely 2.0.7 (ver `requirements.txt`).
- `ogr2ogr` (paquete `gdal-bin`).

## Opción A: Docker Compose

`docker-compose.yml` (en la raíz del repositorio) levanta la base `georef-etl_db` y la aplicación `georef-etl_app`, que monta las carpetas `config/`, `files/` y `reports/`. Las credenciales de la base se leen de `.env`.

```bash
git clone https://github.com/datosgobar/georef-ar-etl.git
cd georef-ar-etl
git checkout development
cp .example.env .env
cp config/georef.example.cfg config/georef.cfg
docker compose up -d db
docker compose run app make migrate
docker compose run app make run
```

Dentro de la red de Docker, el host de la base es `db`. Por defecto, el contenedor `app` ejecuta `make migrate && make run`.

:::caution[A validar]
El `README.md` del ETL indica situarse en la carpeta `docker/` para correr `docker-compose`, pero en la rama `development` `docker-compose.yml` está en la raíz. Tampoco verificamos el contenido de `config/georef.example.cfg` de esa rama. Esta guía sigue los archivos, no el README.
:::

## Opción B: instalación manual

:::caution[A validar]
Los pasos de esta sección vienen de la documentación de la v1.0 (Ubuntu 16.04, PostgreSQL 9.5, PostGIS 2.4) y solo se actualizaron las versiones. No se probaron con PostgreSQL 17, PostGIS 3 ni Python 3.12.
:::

### 1. Instalación

#### 1.1 Dependencias

Instalá PostgreSQL, PostGIS y ogr2ogr con `apt` (en Debian o Ubuntu con el repositorio de PostgreSQL configurado):
```bash
$ sudo apt update
$ sudo apt install postgresql-17 postgresql-17-postgis-3 gdal-bin libpq-dev
```

#### 1.2 Código

Cloná el repositorio:
```bash
$ git clone https://github.com/datosgobar/georef-ar-etl.git
$ cd georef-ar-etl
$ git checkout development
```

#### 1.3 Configuración

Creá `config/georef.cfg` a partir del ejemplo:
```bash
cp config/georef.example.cfg config/georef.cfg
```

La sección `[db]` tiene los datos de conexión a PostgreSQL. Los pasos siguientes usan estos valores de ejemplo:
```ini
[db]
host = localhost
port = 5432
database = georef_ar_etl
user = georef
password = changeme
```

#### 1.4 Base de datos

El ETL necesita una base con la extensión PostGIS y un usuario que pueda crear, borrar y modificar tablas.

Con un usuario administrador de PostgreSQL (por defecto, `postgres`), ejecutá en `psql`:
```sql
create database georef_ar_etl with encoding = 'utf-8';
create user georef with login password 'changeme';
```

Después conectate a la base con `\c georef_ar_etl` y ejecutá:
```sql
create extension postgis;
grant all privileges on all tables in schema public to georef;
```

#### 1.5 Entorno Python

En la raíz del repositorio, creá un entorno virtual:

```bash
$ python3.12 -m venv env
$ source env/bin/activate
```

Instalá las dependencias:
```bash
(env) $ pip install -r requirements.txt
```

Si usás Anaconda:
```bash
(env) $ conda install psycopg2
(env) $ conda install gdal
(env) $ pip install -r requirements.txt
```

#### 1.6 Migración inicial

Creá las tablas con la receta `migrate`:
```bash
(env) $ make migrate
```

Volvé a ejecutarla cada vez que actualices el proyecto: si no hay migraciones nuevas, no cambia nada.

## Ejecución

Con la instalación lista, la receta `run` ejecuta todas las tareas del ETL. **El entorno virtual de Python tiene que estar activado**.

```bash
(env) $ make run
```

Para procesar solo algunas entidades, usá la opción `-p` (o las recetas del `Makefile` con el nombre de cada entidad, como `make gobiernos_locales`):
```bash
(env) $ python -m georef_ar_etl -p provincias -p departamentos
```

### Opciones Adicionales

El ETL cuenta con varias opciones de ejecución que modifican su comportamiento. La primera opción a destacar es `-c`/`--command`, la cual permite elegir qué tarea (subcomando) se desea ejecutar. Sus valores posibles son:

- `etl`: Valor por defecto. Ejecuta el ETL. Las subopciones disponibles son:
	+ `-p`/`--processes`: Permite seleccionar entidades geográficas específicas. Por defecto, se utilizan todas las disponibles.
	+ `-s`/`--start`: Permite especificar el número de paso por donde comenzar el ETL.
	+ `-e`/`--end`: Permite especificar el número de paso por donde finalizar el ETL.
	+ `--no-mail`: Deshabilita el envío de emails.
- `console`: Ejecuta una consola interactiva Python la cual puede ser utilizada para realizar pruebas con distintos componentes internos del ETL. La variable `ctx` contiene una instancia de `Context` lista para ser utilizada.
- `info`: Muestra los pasos que componen el ETL de cada entidad geográfica.
- `stats`: Muestra información sobre los datos actualmente cargados en la base de datos.

Las siguientes opciones se aplican a todos los subcomandos:

- `-m`/`--mode`: Permite especificar el modo de ejecución (`normal`, `interactive` o `testing`). En modo `interactive`, se saltean operaciones costosas para agilizar el ETL, y se crean las tablas automáticamente incluso si no se ejecutaron las migraciones. Su uso es recomendado solo durante el desarrollo del proyecto.
- `-v`/`--verbose`: Muestra información adicional durante la ejecución.
- `-h`/`--help`: Muestra ayuda sobre el uso de `georef_ar_etl`.

## Resultados

El ETL carga los datos en PostgreSQL y genera los archivos bajo `files/latest/` (y una carpeta por versión). Los archivos que publica la descarga de la v2.1 (listado del 25/09/2026, versión de datos 13.0.0) son, para cada entidad, `.ndjson`, `.json`, `.csv` y `.geojson`:

- `provincias`
- `departamentos`
- `aglomerados`
- `fracciones_censales`
- `radios_censales`
- `gobiernos_locales`
- `localidades_censales`
- `asentamientos`
- `localidades`
- `calles`
- `intersecciones`
- `cuadras`
- `establecimientos_educativos`
- `instituciones_universitarias`

Además genera `sinonimos-nombres.txt` y `terminos-excluyentes-nombres.txt`, que usa la API al indexar.

:::caution[A validar]
La lista de tablas de PostgreSQL de la documentación de v1.0 (`georef_provincias`, `georef_municipios`, etc.) no se verificó contra las migraciones actuales del ETL, por eso no se repite acá.
:::
