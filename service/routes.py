from service import app
from flask import jsonify


@app.route('/api/v1.0/normalizador', methods=['GET'])
def get_normalized_data():
    return jsonify({
        'estado':'SIN_RESULTADOS',
        'direcciones': [],
        })
