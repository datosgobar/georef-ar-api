from flask import Flask


app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['JSON_AS_ASCII'] = False

import service.routes
