# Flask Migrate

- Definir variable de entorno

    `$ export POSTGRES_CONNECTION='postgresql://<user>:<password>@<host>/<dbname>' `

- Crear repositorio de migración:

    `$ python manage.py db init`
    
- Crear migración:

    `$ python manage.py db migrate`
    
- Aplicar la migración en la db:

    `$ python manage.py db upgrade`