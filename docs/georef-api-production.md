# Deploy Georef API

## Dependencias

- [ElasticSearch >=6.2](https://www.elastic.co/guide/en/elasticsearch/reference/current/_installation.html)
- Gunicorn
- [Nginx](https://nginx.org/)
- [Python >=3.6.x](https://www.python.org/downloads/)
- [Pip](https://pip.pypa.io/en/stable/installing/)
- [PostgreSQL 9.6](https://www.postgresql.org/download/)
- [PostGis 2.3](http://postgis.net/install/)
- [Virtualenv](https://packaging.python.org/guides/installing-using-pip-and-virtualenv/)
- Wget

## Datos

Los datos de las entidades políticas y vías de circulación deben descargarse del [portal de datos](http://datos.gob.ar/).  

## Base de datos

Crear una base de datos en PostgreSQL con la extensión Postgis.

Ejemplo:

```plsql
-- Creando base de datos
CREATE DATABASE georef_api WITH ENCODING='UTF8';

-- Agregando Postgis a la base de datos creada
CREATE EXTENSION postgis;
```

## Instalación

- Clonar repositorio:

    `$ git clone https://github.com/datosgobar/georef-api.git`
    
- Crear un entorno virtual y activarlo:

    `$ python3.6 -m venv venv`
    
    `$ . venv/bin/activate`

- Instalar dependencias con _pip_:
    
    `(venv)$ pip install -r requirements.txt`
    
- Copiar las variables de entorno:

    `(venv)$ cp environment.example.sh environment.sh`
    
- Completar el archivo `environment.sh` con los valores con los datos correspondientes:

    ```bash
    export GEOREF_API_DB_HOST= # localhost
    export GEOREF_API_DB_NAME= # georef 
    export GEOREF_API_DB_USER= # postgres
    export GEOREF_API_DB_PASS= # postgres   
 
    export ENTIDADES_DATA_DIR= # /directorio/datos/de/entidades
    export VIAS_DATA_DIR= # /directorio/datos/de/vias
 
    export FLASK_APP=service/__init__.py
    export FLASK_DEBUG=0

    export OSM_API_URL='http://nominatim.openstreetmap.org/search'
    ```
    
- Cargar funciones en PostgreSQL:

    `(venv)$ python scripts/functions_load.py`
 
## ElasticSearch

- Instalar dependencias _JDK_ version 1.8.0_131:

    `$ sudo apt install default-jre`
  
- Instalar eleasticSearch:

    `$ wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-6.2.0.deb`

    `# dpkg -i elasticsearch-6.2.0.deb`

- Configuraciones recomendadas:

    `$ sudo vi /etc/elasticsearch/elasticsearch.yml`

    ```
    cluster.name: georef-api
    node.name: node-1
    network.host: 0.0.0.0
    http.max_content_length: 100mb
    ```
    
- Probar el servicio:

    `$ curl -X GET 'http://localhost:9200'`

### Generar índices

- Importar variables de entorno:
    
    `(venv)$ . environment.sh`
    
- Generar índices de entidades:

    `(venv)$ python scripts/index_entities.py crear-entidades`
    
- Generar índices de vías de circulación:

    `(venv)$ python scripts/index_entities.py crear-vias`

- Listar otros comandos utiles:

    `(venv)$ python scripts/index_entities.py`

## Correr API  

Agregar la configuración de los servicios `gunicorn` y `nginx`.

- Configurar servicio en `/etc/systemd/system/`. Completar y modificar el archivo `georef-api.service` [de este repositorio](config/georef-api.service).

- Levantar el servicio:

    `# systemctl start georef-api.service`

- Para `nginx`, crear `/etc/nginx/sites-available/georef-api` tomando como base la configuración del archivo `georef-api.nginx` [de este repositorio](config/georef-api.nginx).

- Generar un link simbólico a la configuración del sitio:

    `# ln -s /etc/nginx/sites-available/georef-api /etc/nginx/sites-enabled`,

- Validar configuración:

    `# nginx -t`

- Cargar la nueva configuración:

    `# nginx -s reload`

- Correr Nginx:

    `# nginx`

## Pruebas

- Pruebas unitarias:

  `(venv) $ python -m unittest`
  
- Consumir mediante la herramienta CURL:

  `$ curl localhost/api/v1.0/direcciones?direccion=cabral+500`
  
  `$ curl localhost/api/v1.0/provincias`
