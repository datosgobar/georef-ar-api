from flask import Flask
import logging.config
import json
import os

log_config = os.environ.get('GEOREF_API_LOG_CONFIG')
if log_config:
    with open(log_config) as f:
        config = json.load(f)
        logging.config.dictConfig(config)


app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['JSON_AS_ASCII'] = False

import service.routes
