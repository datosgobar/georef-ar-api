# -*- coding: utf-8 -*-

from datetime import datetime
import logging
import requests
import os


DOMAIN = os.environ.get('DOMAIN_GEOREF_API')
QUERIES_AVG_REQUESTED = int(int(
    os.environ.get('QUERIES_LENGTH_REQUESTED')) / 100)  # multiplo de  100


QUERIES = [
    'provincias',
    'provincias?id=06',
    'provincias?nombre=santiago+del+estero',
    'provincias?orden=nombre',
    'provincias?campos=nombre',
    'provincias?max=5',
    'provincias?nombre=tucuman&exacto',
    'provincias?formato=geojson',
    'provincias?formato=csv',
    'provincias?formato=json',
    'provincias?id=46&nombre=la+rioja',
    'provincias?nombre=sant&orden=nombre&campos=nombre',
    'provincias?nombre=buenos&max=5&formato=geojson',
    'provincias?nombre=buenos+aires&exacto',
    'departamentos',
    'departamentos?id=02098',
    'departamentos?nombre=presidente+peron',
    'departamentos?provincia=formosa',
    'departamentos?provincia=jujuy&orden=nombre',
    'departamentos?provincia=la+pampa&aplanar',
    'departamentos?provincia=mendoza&campos=nombre',
    'departamentos?provincia=misiones&max=3',
    'departamentos?provincia=rio+negro&exacto',
    'departamentos?formato=csv',
    'departamentos?formato=geojson',
    'departamentos?formato=json',
    'departamentos?id=66154&nombre=san+carlos',
    'departamentos?id=90070&nombre=montero&provincia=tucuman',
    'departamentos?nombre=carlos&provincia=buenos+aires',
    'departamentos?nombre=general&orden=id',
    'departamentos?nombre=gualeguay&aplanar',
    'departamentos?nombre=santa+maria&campos=provincia',
    'departamentos?nombre=libertad&exacto',
    'departamentos?nombre=maipu&max=2&formato=csv',
    'departamentos?nombre=martin&provincia=buenos+aires&aplanar&'
    'campos=provincia&max=20',
    'municipios',
    'municipios?id=060098',
    'municipios?nombre=el+fuerte',
    'municipios?provincia=salta',
    'municipios?departamento=tafi+viejo',
    'municipios?provincia=tierra+del+fuego&orden=nombre',
    'municipios?nombre=tartagal&aplanar',
    'municipios?nombre=villa&campos=nombre',
    'municipios?nombre=arroyo&max=4',
    'municipios?nombre=rivadavia&exacto',
    'municipios?formato=csv',
    'municipios?formato=geojson',
    'municipios?formato=json',
    'municipios?provincia=14&aplanar&max=3',
    'municipios?departamento=san+justo&formato=csv',
    'municipios?nombre=vera&provincia=santa+fe&orden=nombre&aplanar&'
    'campos=nombre&max=2',
    'municipios?nombre=municipalidad&provincia=tucuman&orden=nombre&aplanar&'
    'campos=nombre&max=50',
    'localidades',
    'localidades?id=06147020000',
    'localidades?nombre=san+gotardo',
    'localidades?provincia=chaco',
    'localidades?departamento=parana',
    'localidades?municipio=puerto',
    'localidades?departamento=uruguay&orden=id',
    'localidades?municipio=machagi&aplanar',
    'localidades?departamento=la+matanza&campos=departamento',
    'localidades?provincia=catamarca&max=1000',
    'localidades?nombre=lavalle&exacto',
    'localidades?nombre=antonio&formato=csv',
    'localidades?nombre=villa&formato=geojson',
    'localidades?nombre=villa&formato=json',
    'localidades?nombre=pueblo&aplanar&max=1000&formato=json',
    'localidades?id=14161030000&nombre=corralito',
    'localidades?nombre=aldea&provincia=entre+rios',
    'localidades?nombre=barrio&provincia=chubut&departamento=escalante',
    'localidades?nombre=presidencia&provincia=chaco&municipio=presidencia',
    'localidades?nombre=santa&provincia=buenos&departamento=coronel&'
    'municipio=coronel&orden=id&aplanar&campos=provincia'
    '&formato=csv',
    'calles',
    'calles?id=7802801002870',
    'calles?nombre=gregorio+alvarez',
    'calles?tipo=av',
    'calles?provincia=58',
    'calles?departamento=78021',
    'calles?aplanar',
    'calles?campos=provincia',
    'calles?nombre=echeverria&exacto',
    'calles?provincia=santa+cruz&formato=csv',
    'calles?max=8',
    'calles?nombre=remedios+escalada&provincia=mendoza&aplanar&'
    'campos=provincia&formato=json',
    'calles?nombre=pamplona&provincia=cordoba&aplanar&campos=departamento',
    'calles?nombre=catamarca&tipo=calle&provincia=buenos+aires&'
    'departamento=lomas&aplanar&campos=provincia&formato=csv',
    'direcciones?direccion=corrientes+1000',
    'direcciones?direccion=roque+saenz+pena+100&tipo=calle',
    'direcciones?direccion=mayo+500&provincia=buenos+aires',
    'direcciones?direccion=luro+2000&provincia=buenos+aires&'
    'departamento=la+matanza',
    'direcciones?direccion=san+martin+5000&aplanar',
    'direcciones?direccion=corrientes+900&campos=provincia',
    'direcciones?direccion=bernardo+60&max=4',
    'direcciones?direccion=santa+fe+60&exacto',
    'direcciones?direccion=cordona+70&formato=csv',
    'direcciones?direccion=echeverrria+4497&tipo=calle&provincia=buenos+aires&'
    'departamento=la+matanza&aplanar',
    'ubicacion?lat=-32.8551545&lon=-60.697636',
    'ubicacion?lat=-33.4356132&lon=-60.2434267&aplanar',
    'ubicacion?lat=-24.3909671&lon=-65.3301425&aplanar&campos=lat,lon',
    'ubicacion?lat=-28.2661907&lon=-68.7345846&formato=geojson'
]

logging.basicConfig(
    filename='geore_api_requests_{:%Y%m%d}.log'.format(datetime.now()),
    level=logging.INFO, datefmt='%H:%M:%S',
    format='%(asctime)s | %(levelname)s | %(name)s | %(module)s | %(message)s')


def main():
    """
    Genera un registro de actividades sobre las consultas enviadas a Georef API

    Return: None
    """
    try:
        seconds = 0
        queries_length_requested = len(QUERIES) * QUERIES_AVG_REQUESTED
        print('-- Iniciando test de consultas. Total de consultas: {}.'
              .format(queries_length_requested))
        for i in range(0, QUERIES_AVG_REQUESTED):
            query_ok = 0
            query_error = 0
            for query in QUERIES:
                url = ''.join([DOMAIN, query])
                r = requests.get(url)
                response_time = str(r.elapsed.total_seconds())
                response_status = str(r.status_code)
                seconds += r.elapsed.total_seconds()
                if response_status in "200":
                    query_ok += 1
                    logging.info('{} | "/{}" | {} | {} seg.'
                                 .format('GET', query, response_status,
                                         response_time))
                else:
                    query_error += 1
                    logging.error('{} | "/{}" | {} | {} seg.'
                                  .format('GET', query, response_status,
                                          response_time))
            logging.info('Consultas ejecutadas con éxito: {}.'.format(query_ok))
            logging.info('Consultas ejecutadas con errores: {}.'
                         .format(query_error))
        logging.info('{} consultas ejecutadas en {} seg.'
                     .format(queries_length_requested, seconds))
    except requests.HTTPError as e:
        logging.error(e)
    finally:
        print('-- Proceso terminado.')


if __name__ == '__main__':
    main()
