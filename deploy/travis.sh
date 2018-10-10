#!/bin/bash
# script de deploy TravisCI para georef-ar-api

readonly reindex_regex="\[force reindex\]"

echo "- Iniciando el script de deploy para georef-ar-api..."

# Lectura de variables dependiendo del entorno seleccionado

case "$1" in
        production)
            echo '- Entorno: production'
            IP=$IP_PROD
            PORT_SSH=$PORT_SSH_PROD
            USER_SSH=$USER_SSH_PROD
            BRANCH=$BRANCH_PROD
            ;;

        staging)
            echo '- Entorno: staging'
            IP=$IP_STG
            PORT_SSH=$PORT_SSH_STG
            USER_SSH=$USER_SSH_STG
            BRANCH=$BRANCH_STG
            ;;

        development)
            echo '- Entorno: development'
            IP=$IP_DEV
            PORT_SSH=$PORT_SSH_DEV
            USER_SSH=$USER_SSH_DEV
            BRANCH=$BRANCH_DEV
            ;;
        *)
            echo 'No se especificó un entorno.'
            exit 1
esac

echo "- Agregando host a known hosts..."
ssh-keyscan -p "$PORT_SSH" "$IP" >> ~/.ssh/known_hosts

# Re-deploy de aplicación Flask y reinicio de servicio

DEPLOY_SCRIPT="
cd $GEOREF_API_DIR;
echo '- Activando virtualenv...'
source venv/bin/activate
echo '- Pulleando branch git...'
git pull origin $BRANCH
echo '- Actualizando dependencias...'
pip install --upgrade --force-reinstall -r requirements.txt
echo '- Reiniciando servicio...'
sudo systemctl restart georef-api
echo 'Listo.'
"

echo "- Haciendo ssh a la máquina y corriendo script de deploy..."
ssh -p "$PORT_SSH" "$USER_SSH"@"$IP" "$DEPLOY_SCRIPT"

# Re-indexación opcional de datos

REINDEX_SCRIPT="
cd $GEOREF_API_DIR
source venv/bin/activate
make index_forced
"

if [[ "$TRAVIS_COMMIT_MESSAGE" =~ $reindex_regex ]]; then
    echo "- Activando script de re-indexación..."
    ssh -p "$PORT_SSH" "$USER_SSH"@"$IP" "$REINDEX_SCRIPT"
else
    echo "- No se especificó una re-indexación."
fi
