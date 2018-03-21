import psycopg2
import os


MESSAGES = {
    'functions_load_success': '-- Se cargaron las funciones exitosamente.'
}


def get_db_connection():
    """Se conecta a una base de datos especificada en variables de entorno.

    Returns:
        connection: Conexión a base de datos.
    """
    return psycopg2.connect(host=os.environ.get('GEOREF_API_DB_HOST'),
                            dbname=os.environ.get('GEOREF_API_DB_NAME'),
                            user=os.environ.get('GEOREF_API_DB_USER'),
                            password=os.environ.get('GEOREF_API_DB_PASS'))


def run():
    try:
        files_path = [
            os.path.join('scripts', 'function_geocodificar.sql')
        ]

        for file in files_path:
            with open(file, 'r') as f:
                func = f.read()
            with get_db_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(func)
        print(MESSAGES['functions_load_success'])
    except psycopg2.DatabaseError as e:
        print(e)


if __name__ == '__main__':
    run()
