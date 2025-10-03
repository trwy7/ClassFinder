# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

# Want to help us make this template better? Share your feedback here: https://forms.gle/ybq9Krt8jtBL3iCk7

ARG PYTHON_VERSION=3.13.1
FROM python:${PYTHON_VERSION}-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=1000
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Install sqlite3, mostly for debugging purposes.
RUN apt-get update && apt-get install -y sqlite3

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install pytest freezegun pytest-dependency

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# Switch to the non-privileged user to run the application.
USER appuser

# Copy the source code into the container.
COPY . .

# Run tests with pytest and fail the build if any test fails.
RUN --mount=type=cache,target=/root/.cache/pip \
    pytest

# Remove pytest to reduce the size of the final image.
USER root
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip uninstall -y pytest freezegun

# Delete the tests folder to reduce the size of the final image.

RUN rm -rf tests pytest.ini
# If there is a after-build.sh, run it.

RUN if [ -f after-build.sh ]; then \
        chmod +x after-build.sh && \
        source ./after-build.sh; \
    fi
# Switch back to the non-privileged user.
USER appuser

# Expose the port that the application listens on.
EXPOSE 7842

# Run the application using exec form (JSON array) so signals are delivered properly.
CMD ["waitress-serve", "--host=0.0.0.0", "--port=7842", "app:app"]
# CMD ["gunicorn", "--bind", "0.0.0.0:7842", "-w", "4", "app:app"]Z