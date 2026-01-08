# Dockerfile for Odoo 18 - Built from Source
# This builds Odoo from the current repository (forked from odoo/odoo)

FROM python:3.12-slim-bookworm

# Set environment variables
ENV LANG=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    ODOO_RC=/etc/odoo/odoo.conf

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build dependencies
    build-essential \
    libpq-dev \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    # Runtime dependencies
    postgresql-client \
    curl \
    wget \
    git \
    # Fonts and rendering
    fonts-liberation \
    fonts-noto-cjk \
    # Image processing
    libjpeg62-turbo \
    libpng16-16 \
    libfreetype6 \
    # PDF rendering
    libxrender1 \
    libxext6 \
    # Node.js for Less/JS processing
    nodejs \
    npm \
    # Localization
    locales \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Generate locales
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen \
    && sed -i '/pt_BR.UTF-8/s/^# //g' /etc/locale.gen \
    && locale-gen

# Install wkhtmltopdf (for PDF reports)
RUN curl -o wkhtmltox.deb -sSL https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
    && apt-get update \
    && apt-get install -y --no-install-recommends ./wkhtmltox.deb \
    && rm -rf /var/lib/apt/lists/* wkhtmltox.deb

# Create odoo user
RUN useradd -m -d /var/lib/odoo -s /bin/bash odoo

# Copy Odoo source code from current repository
WORKDIR /usr/lib/python3/dist-packages/odoo
COPY --chown=odoo:odoo ./odoo ./
COPY --chown=odoo:odoo ./addons /usr/lib/python3/dist-packages/odoo/addons
COPY --chown=odoo:odoo setup.py /usr/lib/python3/dist-packages/
COPY --chown=odoo:odoo requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt \
    && pip3 install --no-cache-dir -e /usr/lib/python3/dist-packages/

# Install additional production requirements
COPY requirements.prod.txt /tmp/requirements.prod.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.prod.txt

# Create necessary directories
RUN mkdir -p /mnt/extra-addons \
    && mkdir -p /var/lib/odoo \
    && mkdir -p /etc/odoo \
    && chown -R odoo:odoo /mnt/extra-addons \
    && chown -R odoo:odoo /var/lib/odoo \
    && chown -R odoo:odoo /etc/odoo

# Expose ports
EXPOSE 8069 8072

# Switch to odoo user
USER odoo

# Set entrypoint
ENTRYPOINT []
CMD ["python3", "/usr/lib/python3/dist-packages/odoo-bin", "-c", "/etc/odoo/odoo.conf"]
