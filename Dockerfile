# Imagen base ligera con Python 3.12 (Debian Bookworm)
FROM python:3.12-slim-bookworm

# Copiar binarios oficiales de uv desde la imagen oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Variables de entorno para optimización de Python y uv
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Copiar manifiestos de dependencias primero para aprovechar el cache de Docker
COPY pyproject.toml uv.lock ./

# Instalar dependencias exactas con uv (congeladas desde uv.lock)
RUN uv sync --frozen --no-install-project

# Copiar el codigo fuente del proyecto
COPY . .

# Instalar el paquete raíz del proyecto
RUN uv sync --frozen

# Exponer el puerto del servidor de desarrollo de Django
EXPOSE 8000

# Comando por defecto (sobrescribible en docker-compose)
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]

