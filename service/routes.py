"""Módulo 'routes' de georef-ar-api

Declara las rutas de los recursos que expone la API e
invoca las funciones que procesan dichos recursos.
"""

from functools import wraps
from flask import current_app, request, redirect, Blueprint
from service import app, normalizer, formatter
from service import names as N
from service.decorators import add_params, with_request_logger, deprecated


def disable_cache(f):
    """Dada una función que maneja una request HTTP, modifica los valores de
    los headers para deshabilitar el cacheo de respuestas.

    Args:
        f (function): Función utilizada para manejar un endpoint HTTP de flask.

    Returns:
        function: Endpoint con decorador aplicado.

    """
    @wraps(f)
    def decorated_func(*args, **kwargs):
        resp = f(*args, **kwargs)
        resp.cache_control.no_cache = True
        return resp

    return decorated_func


def add_complete_downloads(bp, urls):
    """Agrega endpoints de descarga completa de datos a un Flask Blueprint.

    Args:
        bp (flask.Blueprint): Objeto donde agregar los endpoints de descarga.
        urls (dict): Diccionario con tipos de entidades como claves, y
            diccionarios como valores. Cada subdiccionario debe contener, por
            cada formato (CSV, JSON, GEOJSON), una URL a donde redirigir (o
            None para no agregar el endpoint). Ver el archivo
            georef.example.cfg para más detalles.

    """
    entities = [N.STATES, N.DEPARTMENTS, N.LOCAL_GOVERNMENTS.replace('_', '-'),
                N.CENSUS_LOCALITIES.replace('_', '-'), N.SETTLEMENTS,
                N.LOCALITIES, N.STREETS, N.STREET_BLOCKS, N.EDUCATIONAL_INSTITUTIONS.replace('_', '-'),
                N.UNIVERSITY_INSTITUTIONS.replace('_', '-')]
    formats = ['json', 'csv', 'geojson', 'ndjson']

    for entity in entities:
        entity_urls = urls[entity]

        for fmt in formats:
            url = entity_urls.get(fmt)
            if url:
                # e.g: /provincias.csv
                endpoint = '{}-{}'.format(entity, fmt)
                rule = '/{}.{}'.format(entity, fmt)

                bp.add_url_rule(rule, endpoint,
                                lambda location=url: redirect(location))


@app.errorhandler(404)
def handle_404(_):
    return formatter.create_404_error_response()


@app.errorhandler(405)
def handle_405(_):
    return formatter.create_405_error_response(app.url_map)


# API v2.0
bp_v2_0 = Blueprint('georef_v2.0', __name__)

add_complete_downloads(bp_v2_0, current_app.config['COMPLETE_DOWNLOAD_URLS'])


@bp_v2_0.route('/provincias', methods=['GET', 'POST'])
def get_states():
    return normalizer.process_state(request)


@bp_v2_0.route('/departamentos', methods=['GET', 'POST'])
def get_departments():
    return normalizer.process_department(request)


@bp_v2_0.route('/aglomerados', methods=['GET', 'POST'])
def get_agglomerations():
    return normalizer.process_agglomeration(request)


@bp_v2_0.route('/fracciones-censales', methods=['GET', 'POST'])
def get_census_tracts():
    return normalizer.process_census_tracts(request)


@bp_v2_0.route('/radios-censales', methods=['GET', 'POST'])
def get_census_blocks():
    return normalizer.process_census_blocks(request)


@bp_v2_0.route('/municipios', methods=['GET', 'POST'])
@deprecated(current_endpoint="municipios", alternative_endpoint='gobiernos-locales')
@add_params(categoria="Municipio")
def get_municipalities():
    return normalizer.process_municipality(request)


@bp_v2_0.route('/gobiernos-locales', methods=['GET', 'POST'])
def get_local_governments():
    return normalizer.process_local_government(request)


@bp_v2_0.route('/localidades-censales', methods=['GET', 'POST'])
def get_census_localities():
    return normalizer.process_census_locality(request)


@bp_v2_0.route('/asentamientos', methods=['GET', 'POST'])
def get_settlements():
    return normalizer.process_settlement(request)


@bp_v2_0.route('/localidades', methods=['GET', 'POST'])
@add_params(categoria="Localidad simple,Componente de localidad compuesta,entidad")
def get_localities():
    return normalizer.process_locality(request)


@bp_v2_0.route('/calles', methods=['GET', 'POST'])
def get_streets():
    return normalizer.process_street(request)


@bp_v2_0.route('/direcciones', methods=['GET', 'POST'])
@with_request_logger
def get_addresses():
    return normalizer.process_address(request)


@bp_v2_0.route('/ubicacion', methods=['GET', 'POST'])
@disable_cache
def get_location():
    return normalizer.process_location(request)


@bp_v2_0.route('/establecimientos-cercanos', methods=['GET'])
@disable_cache
def get_nearby_establishments():
    return normalizer.process_nearby_establishments(request)

@bp_v2_0.route('/establecimientos', methods=['GET', 'POST'])
def get_establishments():
    return normalizer.process_establishments(request)

# TODO: Hacer el cambio cuando estén definidos los campos comunes a todos los establecimientos
@bp_v2_0.route('/establecimientos-educativos', methods=['GET', 'POST'])
@deprecated(current_endpoint="establecimientos-educativos", alternative_endpoint='establecimientos')
#@add_params(tipo=N.EDUCATIONS)
def get_educational_institutions():
    return normalizer.process_educational_institutions(request)
    #return normalizer.process_establishments(request)

@bp_v2_0.route('/instituciones-universitarias', methods=['GET', 'POST'])
@deprecated(current_endpoint="instituciones-universitarias", alternative_endpoint='establecimientos')
#@add_params(tipo=N.UNIVERSITIES)
def get_university_institutions():
    return normalizer.process_university_institutions(request)
    #return normalizer.process_establishments(request)

@bp_v2_0.route('/cuadras', methods=['GET', 'POST'])
def get_street_blocks():
    return normalizer.process_street_block(request)


# Última versión de la API
app.register_blueprint(bp_v2_0, url_prefix='/api')

# v2.0
# app.register_blueprint(bp_v2_0, url_prefix='/api/v2.0')
app.register_blueprint(bp_v2_0, url_prefix='/api/v2.0')
