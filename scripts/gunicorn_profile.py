"""
Gunicorn - profiler para endpoints
Requiere: git, imagemagick tools, graphviz

Para utilizar, cargar el módulo al inicializar Gunicorn (desde el directorio
raíz del proyecto):

$ gunicorn service:app -c scripts/gunicorn_profile.py

Luego, agregar el header 'X-Gunicorn-Profile' a los requests HTTP realizados.
"""

import cProfile
import pstats
import io
import subprocess
import os
import logging
import time

MAX_ROWS = 20
PROFILE_DIR = 'profile'


def run_cmd(cmd, input=None):
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE,
                            encoding='utf-8', check=True, input=input)
    return result.stdout


def profile_enabled(req):
    return 'X-Gunicorn-Profile'.upper() in [h[0] for h in req.headers]


def when_ready(server):
    if not os.path.exists(PROFILE_DIR):
        os.makedirs(PROFILE_DIR)


def pre_request(worker, req):
    if profile_enabled(req):
        worker.profile = cProfile.Profile()
        worker.profile.enable()


def post_request(worker, req, environ, resp):
    if not profile_enabled(req):
        return

    worker.profile.disable()
    t = time.strftime('%Y.%m.%d-%H.%M.%S')
    s = io.StringIO()
    ps = pstats.Stats(worker.profile, stream=s)
    ps.sort_stats('time', 'cumulative')

    git_commit = 'undefined'
    try:
        git_commit = run_cmd('git describe --always --tags --dirty')
    except subprocess.CalledProcessError:
        # Ignorar excepción completamente
        pass

    base_name = os.path.join(
        PROFILE_DIR,
        '{}_{}'.format(req.path[1:].replace('/', '-'), t)
    )

    # Guardar estadísticas de llamados a funciones
    with open(base_name + '_stats.txt', 'w') as f:
        print('{}?{}'.format(req.path, req.query), file=f)
        print(git_commit, file=f)
        ps.print_stats(MAX_ROWS)
        print(s.getvalue(), file=f)

    # Guardar objeto Stats
    dump_path = base_name + '_dump.bin'
    ps.dump_stats(dump_path)

    # Crear grafo de funciones con gprof2dot
    try:
        graph = run_cmd('gprof2dot -f pstats {}'.format(dump_path))
        img_path = base_name + '_graph.png'
        run_cmd('dot -Tpng -o {}'.format(img_path), input=graph)

        # Agregar texto a la imagen creada
        cmd_template = 'convert ' + img_path + ' \
                        -pointsize 50 \
                        label:{txt} \
                        -gravity center \
                        -append ' + img_path

        run_cmd(cmd_template.format(txt=req.path))
        if req.query:
            run_cmd(cmd_template.format(txt=req.query))
        run_cmd(cmd_template.format(txt=git_commit))
    except subprocess.CalledProcessError:
        # Ignorar excepción completamente
        pass
