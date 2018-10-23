"""Módulo es_config.py de georef-ar-api

Contiene toda la información necesaria para la creación de documentos e índices
de Elasticsearch para Georef.
"""

from elasticsearch_dsl import Index, Document
from elasticsearch_dsl import analyzer, normalizer
from elasticsearch_dsl import Object, Float, GeoShape, Keyword, Text, MetaField

name_analyzer = analyzer(
    'name_analyzer',
    tokenizer='standard',
    filter=['lowercase', 'asciifolding'] # TODO stopwords
)

# name_analyzer_synonyms TODO

lowcase_ascii_normalizer = normalizer(
    'lowcase_ascii_normalizer',
    filter=['lowercase', 'asciifolding']
)

class Entity(Document):
    id = Keyword()

class Centroid(Document):
    lat = Float(index=False)
    lon = Float(index=False)

CentroidField = Object(doc_class=Centroid)

NameField = Text(
    analyzer=name_analyzer, # TODO search analyzer
    fields={
        'exacto': Keyword(
            normalizer=lowcase_ascii_normalizer
        )
    }
)

class State(Entity):
    nombre = NameField
    centroide = CentroidField
    geometria = GeoShape()

    class Meta:
        source = MetaField(excludes=['geometria'])

class StateGeom(Entity):
    geometria = GeoShape()

class StateSimple(Entity):
    nombre = NameField
    interseccion = Float(index=False)

StateSimpleField = Object(doc_class=StateSimple)

class Department(Entity):
    nombre = NameField
    centroide = CentroidField
    geometria = GeoShape()
    provincia = StateSimpleField

class DepartmentGeom(Entity):
    geometria = GeoShape()

class DepartmentSimple(Entity):
    nombre = NameField

DepartmentSimpleField = Object(doc_class=DepartmentSimple)

class Municipality(Entity):
    nombre = NameField
    centroide = CentroidField
    geometria = GeoShape()
    provincia = StateSimpleField

class MunicipalityGeom(Entity):
    geometria = GeoShape()

class MunicipalitySimple(Entity):
    nombre = NameField

MunicipalitySimpleField = Object(doc_class=MunicipalitySimpleField)

class Locality(Entity):
    nombre = NameField
    centroide = CentroidField
    tipo = Keyword()
    geometria = GeoShape()
    provincia = StateSimpleField
    departamento = DepartmentSimpleField
    municipio = MunicipalitySimpleField

class Street(Entity):
    class Limit(Document):
        derecha = Integer()
        izquierda = Integer()

    class Numbers(Document):
        inicio = Object(doc_class=Limit)
        fin = Object(doc_class=Limit)

    nombre = NameField
    nomenclatura = Text(index=False)
    tipo = Text(analyzer=name_analyzer) # TODO search analyzer
    altura = Object(doc_class=Numbers)
    geometria = Text(index=False)
    provincia = StateSimpleField
    departamento = DepartmentSimpleField
