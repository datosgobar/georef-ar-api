# -*- coding: utf-8 -*-
import os
import psycopg2


def get_db_connection():
    return psycopg2.connect(
        dbname=os.environ.get('POSTGRES_DBNAME'),
        user=os.environ.get('POSTGRES_USER'),
        password=os.environ.get('POSTGRES_PASSWORD'))


def query(address, params=None):
    if params and (len(params)) > 1:
        query = build_query_for(params)
    else:
        query = build_query_for_search(address)
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()
        results_list = [{
            'descripcion': row[0],
            'nombre': row[1],
            'tipo': row[2],
            'localidad': row[3],
            'provincia': row[4]} for row in results]
    return results_list


def build_query_for(params):
    address = params.get('direccion')
    localidad = params.get('localidad')
    provincia = params.get('provincia')
    query = "SELECT tipo_camino || ' ' || nombre_completo || ', ' \
                || localidad || ', ' || provincia AS addr, nombre_completo, \
                tipo_camino, localidad, provincia \
                FROM nombre_calles \
                WHERE nombre_completo ILIKE '%s%%'" % (address)
    if localidad:
        query += " AND localidad ILIKE '%%%s%%'" % (localidad)
    if provincia:
        query += " AND provincia ILIKE '%%%s%%'" % (provincia)
    query += " LIMIT 10"
    return query


def build_query_for_search(address):
    parts = address.split(',')
    query = "SELECT tipo_camino || ' ' || nombre_completo || ', ' \
                || localidad || ', ' || provincia AS addr, nombre_completo, \
                tipo_camino, localidad, provincia \
                FROM nombre_calles "
    if len(parts) > 1:
        query += "WHERE nombre_completo ILIKE '%(road)s%%' \
                AND localidad ILIKE '%%%(locality)s%%'" % {
                    'road': parts[0].strip(),
                    'locality': parts[1].strip()}
    else:
        query += "WHERE nombre_completo ILIKE '%s%%'" % (address)
    query += " LIMIT 10"
    return query
