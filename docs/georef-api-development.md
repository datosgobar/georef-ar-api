# Georef API - Guía de instalación para entorno de desarrollo

## Dependencias

- [ElasticSearch >=5.5](https://www.elastic.co/guide/en/elasticsearch/reference/current/_installation.html)
- [Python >=3.6.x](https://www.python.org/downloads/)
- [Pip](https://pip.pypa.io/en/stable/installing/)
- Postgresql Client Common
- [Virtualenv](https://packaging.python.org/guides/installing-using-pip-and-virtualenv/)

## Instalación

1. Clonar repositorio

    `$ git clone https://github.com/datosgobar/georef-api.git`
    
2. Crear entorno virtual e instalar dependencias con pip

    `$ python3.6 -m venv venv`
    
    `(venv)$ pip install -r requirements.txt`

3. Copiar las variables de entorno

    `$ cp environment.example.sh environment.sh`
    
4. Completar los valores con los datos correspondientes:

    ```bash
    export FLASK_APP=service/__init__.py
    export GEOREF_URL= # URL
    export OSM_API_URL='http://nominatim.openstreetmap.org/search'
    export GEOREF_DB_HOST= # 'localhost'
    export GEOREF_DB_NAME= # georef 
    export GEOREF_DB_USER= # user
    export GEOREF_DB_PASS= # password
    ```
 
## ElasticSearch

- Levantar el servicio de ElasticSearch

  `$ cd path/to/elasticsearch/bin/ && ./elasticseach`
  
- Listar índices

  `$ curl localhost:9200/_cat/indices?v`

- Borrar índices

  `$ curl -XDELETE 'localhost:9200/<nombre_indice>?pretty&pretty'`

## Correr API 

- Correr los siguientes comandos:

    `(venv)$ . environment.sh`
    
    `(venv)$ flask run`

## Pruebas

- Test

  `(venv) $ python -m unittest tests/test_normalization.py`
  
  `(venv) $ python -m unittest tests/test_parsing.py`
  
- Consumir mediante la herramienta CURL:

  `$ curl localhost:5000/api/v1.0/direcciones?direccion=cabral+500`
  
  `$ curl localhost:5000/api/v1.0/provincias`
