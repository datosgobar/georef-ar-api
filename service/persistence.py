# -*- coding: utf-8 -*-
import psycopg2


def get_db_connection():
    return psycopg2.connect(
        dbname='georef',
        user='postgres',
        password='postgres')


def query(request):
    connection = get_db_connection()
    address = request.args.get('direccion')
    parts = address.split(',')
    with connection.cursor() as cursor:
        query = "SELECT tipo_camino || ' ' || nombre_completo || ', ' \
                    || localidad || ', ' || provincia AS addr \
                    FROM nombre_calles "
        if len(parts) > 1:
            query += "WHERE nombre_completo ILIKE '%(road)s%%' \
                    AND localidad ILIKE '%%%(locality)s%%'" % {
                        'road': parts[0].strip(),
                        'locality': parts[1].strip()}
        else:
            query += "WHERE nombre_completo ILIKE '%s%%'" % (address)
        query += " LIMIT 10"
        cursor.execute(query)
        results = cursor.fetchall()
        results_list = [{'descripcion': row[0]} for row in results]
    return results_list
