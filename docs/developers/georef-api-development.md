# Guía de instalación para desarrolladores

En este documento se detallan los pasos a seguir si se desea configurar un servidor de API Georef propio.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
 

- [Dependencias](#dependencias)
- [Instalación](#instalacion)
    - [1. Base de datos](#1-base-de-datos)
    - [2. Elasticsearch](#2-elasticsearch)
    - [3. Repositorio y dependencias](#3-repositorio-y-dependencias)
    - [4. Cargar las funciones SQL](#4-cargar-las-funciones-sql)
    - [5. Crear los índices](#5-crear-los-indices)
    - [6. (Opcional) Re-indexar datos](#6-opcional-re-indexar-datos)
    - [7. Correr API](#7-correr-api)
- [Tests](#tests)
- [Archivos de datos](#archivos-de-datos)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Dependencias

- [Elasticsearch >=6.2.0](https://www.elastic.co/guide/en/elasticsearch/reference/current/_installation.html)
- [Python >=3.6.x](https://www.python.org/downloads/)
- [PostgreSQL 9.6](https://www.postgresql.org/download/)
- [PostGIS 2.3](http://postgis.net/install/)
- [Nginx](https://nginx.org/) *(para entornos productivos)*

## Instalación

### 1. Base de datos
Crear una base de datos en PostgreSQL con la extensión PostGIS. A continuación, se muestra un ejemplo utilizando `georef_api` como nombre para la base de datos:
```sql
-- Crear la base de datos:
CREATE DATABASE georef_api WITH ENCODING='UTF8';

-- Agregar PostGIS a la base de datos creada:
CREATE EXTENSION postgis;
```

### 2. Elasticsearch

Para instalar Elasticsearch, seguir las siguientes instrucciones en uno o más servidores (nodos).

#### 2.1 Instalar el entorno de ejecución para Java:
```bash
$ sudo apt install default-jre
```

#### 2.2 Instalar Elasticsearch:
```bash
$ wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-6.2.0.deb
$ sudo dpkg -i elasticsearch-6.2.0.deb
$ sudo systemctl enable elasticsearch # utilizando systemd para administrar el servicio
```
#### 2.3 Aplicar las configuraciones recomendadas

Editar el archivo  `/etc/elasticsearch/elasticsearch.yml` (el valor de `node.name` debe ser único por nodo):

```text
node.name: node-1
http.max_content_length: 100mb
```

Editar el archivo `/etc/elasticsearch/jvm.options` (siguiendo las [recomendaciones de Elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/heap-size.html)):
```text
# Tamaño del heap size de la JVM
# Se recomienda utilizar siempre el mismo valor como mínimo y máximo
# Ejemplo: 4 GB
-Xms4g
-Xmx4g
```

### 3. Repositorio y dependencias

#### 3.1 Clonar el repositorio:
```bash
$ git clone https://github.com/datosgobar/georef-api.git
$ cd georef-api
```

#### 3.2 Crear un entorno virtual y activarlo:
```bash
$ python3 -m venv venv
$ source venv/bin/activate
```

#### 3.3 Instalar dependencias con `pip`:
```bash
(venv) $ pip3 install -r requirements.txt -r requirements-dev.txt
```

#### 3.4 Copiar el archivo de configuración:
```bash
(venv) $ cp config/georef.example.cfg config/georef.cfg
```

Luego, completar el archivo `config/georef.cfg` con los valores apropiados.

#### 3.5 Copiar el archivo de configuración de logs:
```bash
(venv) $ cp config/logging.example.ini config/logging.ini
```
	
Luego, completar el archivo `config/logging.ini` con los valores apropiados. Los valores por defecto son válidos y pueden ser utilizados en entornos productivos.
 
#### 3.6 Crear el archivo de sinónimos
Adicionalmente, se debe crear un archivo `georef_synonyms.txt`, en la ubicación del archivo de configuración de Elasticsearch (`$ES_HOME/config`). El archivo contiene la base de sinónimos utilizados al momento de indexar documentos. Su contenido puede ser vacío o contener, por ejemplo, el siguiente contenido:
```text
buenos aires, bsas
ciudad autonoma de buenos aires, caba, capital federal
santiago, sgo, stgo
```

### 4. Cargar las funciones SQL
Cargar las funciones SQL necesarias para el funcionamiento de la API:
```bash
(venv) $ make load_sql
```

### 5. Crear los índices
Generar índices de entidades y calles:
```bash
(venv) $ make index
```
        
Listar los índices creados, y otros datos adicionales:
```bash
(venv) $ make print_index_stats
```
	
### 6. (Opcional) Re-indexar datos
Si se modifican los archivos de datos JSON, es posible re-indexarlos sin borrar los índices ya existentes. Dependiendo del comportamiento que se desee, se debe tomar una opción:

#### Indexar datos nuevos
Si se desea actualizar los índices con los nuevos datos, solo si los datos entrantes son más recientes, se puede utilizar nuevamente:
  
```bash
(venv) $ make index
```

#### Forzar re-indexado
Si se desea forzar un re-indexado, es decir, si se desea indexar los datos nuevamente sin importar la fecha de creación, se debe utilizar la siguiente receta:

```bash
(venv) $ make index_forced
```

La receta `index_forced` intenta utilizar un archivo de respaldo guardado anteriormente si no pudo acceder a los archivos especificados en `config/georef.cfg`. El uso de la receta es recomendado cuando se requiere re-indexar los datos incondicionalmente, algunas situaciones donde esto es necesario son:

- Modificación de la estructura de los archivos de datos
- Modificación de *mappeos* de tipos de Elasticsearch
- Modificación de analizadores de texto de Elasticsearch
- Modificación de listado de sinónimos

### 7. Correr API 
#### Entornos de desarrollo
Correr la API de Georef utilizando un servidor de prueba (no apto para producción):
```bash
(venv) $ make start_dev_server
```

#### Entornos productivos
##### 7.1 Configurar servicio `georef-api` para `systemd`
Copiar el archivo [`config/georef-api.service`](https://github.com/datosgobar/georef-ar-api/blob/master/config/georef-api.service) a `/etc/systemd/system/` y configurarlo. Notar los campos marcados entre '`<`' y '`>`', que deben ser reemplazados por el usuario.

##### 7.2 Activar y arrancar el servicio
```bash
$ sudo systemctl daemon-reload
$ sudo systemctl enable georef-api.service
$ sudo systemctl start georef-api.service
```

##### 7.3 Configurar `nginx`
Primero, crear `/etc/nginx/sites-available/georef-api` tomando como base la configuración del archivo [`georef-api.nginx`](https://github.com/datosgobar/georef-ar-api/blob/master/config/georef-api.nginx).

##### 7.4 (Opcional) Crear cache para `nginx`
Si se desea activar el uso del cache de `nginx`, descomentar las líneas contentiendo las directivas `proxy_cache` y `proxy_cache_valid` del archivo `georef-api` creado. Luego, activar el cache `georef` agregando la siguiente línea al archivo de configuración `nginx.conf` (sección `http`):

```nginx
proxy_cache_path /data/nginx/cache levels=1:2 inactive=120m keys_zone=georef:10m use_temp_path=off;
```

Finalmente, crear el directorio `/data/nginx/cache`.

##### 7.5 Activar y validar configuración `nginx`
Generar un link simbólico a la configuración del sitio:
```bash
$ sudo ln -s /etc/nginx/sites-available/georef-api /etc/nginx/sites-enabled/georef-api
```

Validar la configuración:
```bash
$ sudo nginx -t
```

Cargar la nueva configuración:
```bash
$ sudo nginx -s reload
```

Reiniciar Nginx:
```bash
$ systemctl restart nginx.service
```

## Tests
Ejecutar los tests unitarios (los servicios Elasticsearch y PostgreSQL deben estar activos y con los datos apropiados cargados):
```bash
(venv) $ make test_all
```

## Archivos de datos

- La estructura de los archivos de datos JSON utilizados por Georef está detallada en [este documento](georef-api-data.md).

- El archivo de configuración `config/georef.cfg` debe especificar una ruta local o una URL externa para cada archivo de datos JSON. Notar que los valores por defecto (en `georef.example.cfg`) utilizan el portal de descargas `infra.datos.gob.ar`, que siempre provee la última versión de los archivos JSON disponibles.
