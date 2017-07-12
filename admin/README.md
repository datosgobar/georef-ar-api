# Integración

## Migración

- Definir variable de entorno para nuestra conexión a PostgreSQL:

    `$ export POSTGRES_CONNECTION='postgresql://<user>:<password>@<host>/<dbname>'`

- Crear repositorio de migración:

    `$ python manage.py db init`
    
- Crear migración:

    `$ python manage.py db migrate`
    
- Aplicar la migración en la base de datos:

    `$ python manage.py db upgrade`
    
## Usuarios
    
- Generar usuario:

    `$ python manage.py createuser`
    
## Json Web Token

### Ejemplo de uso

- Acceder a un servicio sin Token:

    `$ curl localhost:5000/api/v1.0/direcciones?direccion=cabral`

- Generar Token:

    `$ curl -XPOST localhost:5000/api/v1.0/auth -H "Content-Type: application/json" -d '{"username":"<username>", "password": "<password>"}'`
    
- Acceder a un servicio con Token:

    `$ curl localhost:5000/api/v1.0/direcciones?direccion=cabral -H "Authorization: JWT <token>"`