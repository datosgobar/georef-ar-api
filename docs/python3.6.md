# Python 3.6

## Instalación

- Librerias requeridas:

  `$ sudo apt install build-essential libssl-dev zlib1g-dev`

  `$ sudo apt install libbz2-dev libreadline-dev libsqlite3-dev`

- Descargando los archivos binarios

  `$ wget https://www.python.org/ftp/python/3.6.2/Python-3.6.4.tgz`

  `$ tar xvf Python-3.6.4.tgz`

  `$ cd Python-3.6.4`

- Instalación

  `# ./configure --enable-optimizations`

  `# make altinstall`

- Pip

  `$ sudo apt install python-pip` o `python3-pip`

## Entorno virtuales

- Instalación de Virtualenv

  `$ sudo apt-get install virtualenv python-virtualenv`

- Crear entorno

  `$ python3.6 -m venv <name-venv>`

- Activar entorno virtual

  `$ . venv/bin/activate`
