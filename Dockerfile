FROM python:3.11.6-bullseye

RUN apt-get update && \
  apt-get install -y \
  # General dependencies
  locales \
  locales-all && \
  # Clean local repository of package files since they won't be needed anymore.
  # Make sure this line is called after all apt-get update/install commands have
  # run.
  apt-get clean && \
  # Also delete the index files which we also don't need anymore.
  rm -rf /var/lib/apt/lists/*

ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Add app code here
COPY . /srv/mesop-app

WORKDIR /srv/mesop-app

RUN uv sync

# Run Mesop through gunicorn. Application will be available at localhost:8080
CMD ["uv", "run", "uvicorn", "--host", "0.0.0.0", "--port", "8080", "--workers", "1", "main:app", "--reload"]

# Run nothing, indefinitely. Usefull for debugging
#CMD ["tail", "-f", "/dev/null"]
