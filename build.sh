set -o errexit

echo "-> Sincronizando dependencias con uv..."
pip install uv
uv sync

echo "-> Ejecutando migraciones de base de datos..."
uv run python manage.py migrate

echo "-> Recolectando archivos estáticos..."
uv run python manage.py collectstatic --no-input

echo "✓ Build finalizado con éxito."

