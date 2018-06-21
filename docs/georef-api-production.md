# Deploy Georef API

## Dependencias

- [Elasticsearch >=6.2.0](https://www.elastic.co/guide/en/elasticsearch/reference/current/_installation.html)
- [Gunicorn](http://gunicorn.org/)
- [Nginx](https://nginx.org/)
- [Python >=3.6.x](https://www.python.org/downloads/)
- [PostgreSQL 9.6](https://www.postgresql.org/download/)
- [PostGIS 2.3](http://postgis.net/install/)
- `wget`

## Instalación

### Datos

En [este documento](georef-api-data.md) se detalla el modelo de datos utilizado por la API y las URLs donde se encuentran publicados. 

### Base de datos

Crear una base de datos en PostgreSQL con la extensión PostGIS.

Ejemplo utilizando `georef_api` como nombre para la base de datos:

```plsql
-- Crear la base de datos
CREATE DATABASE georef_api WITH ENCODING='UTF8';

-- Agregar PostGIS a la base de datos creada
CREATE EXTENSION postgis;
```

### Repositorio y dependencias

- Clonar el repositorio:

    `$ git clone https://github.com/datosgobar/georef-api.git`

	`$ cd georef-api`
    
- Crear un entorno virtual y activarlo:

    `$ python3 -m venv venv`
    
    `$ . venv/bin/activate`

- Instalar dependencias con `pip`:
    
    `(venv)$ pip3 install -r requirements.txt`
    
- Copiar las variables de entorno:

    `(venv)$ cp environment.example.sh environment.sh`

- Copiar el archivo de configuración de logs:

    `(venv)$ cp docs/config/logging.example.ini logging.ini`
    
- Completar el archivo `environment.sh` con los valores con los datos correspondientes:

    ```bash
    export GEOREF_API_DB_HOST= # Dirección de la base de datos PostgreSQL
    export GEOREF_API_DB_NAME= # Nombre de la base de datos (por ejemplo, 'georef_api')
    export GEOREF_API_DB_USER= # Usuario de la base de datos
    export GEOREF_API_DB_PASS= # Contraseña del usuario de la base de datos
 
    export ENTIDADES_DATA_DIR= # /directorio/datos/de/entidades
    export VIAS_DATA_DIR= # /directorio/datos/de/vias
 
    export FLASK_APP=service/__init__.py
    export FLASK_DEBUG=0

    export OSM_API_URL='http://nominatim.openstreetmap.org/search'
    ```
    
- Cargar funciones en PostgreSQL:

    `(venv)$ python scripts/functions_load.py`
 
### Elasticsearch

- Instalar el entorno de ejecución para Java:

    `$ sudo apt install default-jre`
  
- Instalar Elasticsearch:

    `$ wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-6.2.0.deb`

    `# dpkg -i elasticsearch-6.2.0.deb`

- Opcionalmente, aplicar las configuraciones recomendadas:

    `$ sudo vi /etc/elasticsearch/elasticsearch.yml`

    ```
    cluster.name: georef-api
    node.name: node-1
    http.max_content_length: 100mb
    ```

    `$ sudo vi /etc/elasticsearch/jvm.options` (siguiendo las recomendaciones de [Elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/heap-size.html))

    ```
    # Tamaño del heap size de la JVM
    # Se recomienda utilizar siempre el mismo valor como mínimo y máximo
    # Ejemplo: 4 GB
    -Xms4g
    -Xmx4g
    ```
    
- Probar el servicio Elasticsearch:

    `$ curl -X GET 'http://localhost:9200'`

### Crear los índices

- Importar variables de entorno:
    
    `(venv)$ . environment.sh`
    
- Generar índices de entidades. Se debe contar con los archivos de datos para entidades mencionados al comienzo de la guía, y sus directorios deben estar en las variables de entorno (vía el archivo `environment.sh`).

    `(venv)$ make indexar_todos`
        
- Listar los índices creados:

    `(venv)$ make listar_indices`

## Correr API  

Agregar la configuración de los servicios `gunicorn` y `nginx`.

- Configurar servicio en `/etc/systemd/system/`. Completar y modificar el archivo `georef-api.service` [de este repositorio](config/georef-api.service).

- Activar y arrancar el servicio:

	`# systemctl enable georef-api.service`

    `# systemctl start georef-api.service`

- Para `nginx`, crear `/etc/nginx/sites-available/georef-api` tomando como base la configuración del archivo `georef-api.nginx` [de este repositorio](config/georef-api.nginx).

- Para activar el uso del cache de `nginx`, descomentar las líneas contentiendo las directivas `proxy_cache` y `proxy_cache_valid` del archivo `georef-api` creado. Luego, activar el cache `georef` agregando la siguiente línea al archivo de configuración `nginx.conf` (sección `http`):
    ```
    proxy_cache_path /data/nginx/cache levels=1:2 inactive=120m keys_zone=georef:10m use_temp_path=off;
    ```
    Finalmente, crear el directorio `/data/nginx/cache`.

- Generar un link simbólico a la configuración del sitio:

    `# ln -s /etc/nginx/sites-available/georef-api /etc/nginx/sites-enabled/georef-api`

- Validar la configuración:

    `# nginx -t`

- Cargar la nueva configuración:

    `# nginx -s reload`

- Reiniciar Nginx:

    `# systemctl restart nginx.service`

## Pruebas

- Pruebas unitarias:

  `(venv) $ python -m unittest`
  
- Consumir mediante la herramienta CURL:

  `$ curl localhost/api/v1.0/direcciones?direccion=cabral+500`
  
  `$ curl localhost/api/v1.0/provincias`
