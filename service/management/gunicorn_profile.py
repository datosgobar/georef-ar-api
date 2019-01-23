"""gunicorn_profile.py - profiler para endpoints
Requiere: git, imagemagick tools, graphviz

Para utilizar, ejecutar el siguiente comando en la carpeta raíz del proyecto:

$ make start_profile_server

Luego, realizar una request HTTP a localhost:5000 para llevar a cabo un
análisis de performance. Los resultados se depositan en el directorio
'profile'.
"""

import cProfile
import pstats
import io
import subprocess
import os
import time
import shutil

MAX_ROWS = 20
PROFILE_DIR = 'profile'


def run_cmd(cmd, input_data=None):
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE,
                            encoding='utf-8', check=True, input=input_data)
    return result.stdout


def assert_command_exists(cmd):
    if not shutil.which(cmd):
        raise RuntimeError('The following command is required: {}'.format(cmd))


def when_ready(_):
    assert_command_exists('git')
    assert_command_exists('dot')
    assert_command_exists('gprof2dot')
    assert_command_exists('convert')

    if not os.path.exists(PROFILE_DIR):
        os.makedirs(PROFILE_DIR)


def pre_request(worker, _):
    worker.profile = cProfile.Profile()
    worker.profile.enable()


def post_request(worker, req, *_):
    worker.profile.disable()
    t = time.strftime('%Y.%m.%d-%H.%M.%S')
    s = io.StringIO()
    ps = pstats.Stats(worker.profile, stream=s)
    ps.sort_stats('time', 'cumulative')

    try:
        git_commit = run_cmd('git describe --always --tags --dirty')
    except subprocess.CalledProcessError:
        git_commit = 'unknown commit'

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
        run_cmd('dot -Tpng -o {}'.format(img_path), input_data=graph)

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
        print('No se pudo generar imagen utilizando gprof2dot y dot.')
