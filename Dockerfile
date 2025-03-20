# Adapted from https://github.com/astral-sh/uv-docker-example

# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.10-bookworm AS builder

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# Then, use a final image without uv
FROM ghcr.io/praekeltfoundation/docker-django-bootstrap-nw:py3.10-bullseye
# It is important to use the image that matches the builder, as the path to the
# Python executable must be the same, e.g., using `python:3.11-slim-bookworm`
# will fail.

# Copy the application from the builder
COPY --from=builder --chown=app:app /app /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

ENV DJANGO_SETTINGS_MODULE "config.settings.production"
RUN SECRET_KEY=placeholder ALLOWED_HOSTS=placeholder python manage.py collectstatic --noinput
CMD [\
    "config.wsgi:application",\
    "--workers=2",\
    "--threads=4",\
    "--worker-class=gthread",\
    "--worker-tmp-dir=/dev/shm"\
]
