# -*- coding: utf-8 -*-
import os
import psycopg2
import re


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
    return results


def build_query_for(params):
    address = params.get('direccion')
    road, number = get_parts_from(address)
    locality = params.get('localidad')
    state = params.get('provincia')
    query = "SELECT tipo_camino, nombre_completo, \
                altura_inicial, altura_final, localidad, provincia \
                FROM nombre_calles \
                WHERE nombre_completo ILIKE '%s%%'" % (road)
    if locality:
        query += " AND localidad ILIKE '%%%s%%'" % (locality)
    if state:
        query += " AND provincia ILIKE '%%%s%%'" % (state)
    query += " LIMIT 10"
    return query


def build_query_for_search(address):
    parts = address.split(',')
    query = "SELECT tipo_camino, nombre_completo, \
                altura_inicial, altura_final, localidad, provincia \
                FROM nombre_calles "
    if len(parts) > 1:
        road, number = get_parts_from(parts[0].strip())
        locality = parts[1].strip()
        query += "WHERE nombre_completo ILIKE '%(road)s%%' \
                AND localidad ILIKE '%%%(locality)s%%'" % {
                    'road': road,
                    'locality': locality }
    else:
        road, number = get_parts_from(address)
        query += "WHERE nombre_completo ILIKE '%s%%'" % (road)
    query += " LIMIT 10"
    return query


def get_parts_from(address):
    match = re.search(r'(\s[0-9]+?)$', address)
    number = int(match.group(1)) if match else None
    address = re.sub(r'(\s[0-9]+?)$', r'', address)
    return address.strip(), number
