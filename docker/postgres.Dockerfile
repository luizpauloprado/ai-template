# Postgres 17 + pgvector (imagem oficial do pgvector) + PGMQ (compilado do fonte)
FROM pgvector/pgvector:pg17

ARG PGMQ_VERSION=1.13.0

# PGMQ é uma extensão só de SQL: o `make install` apenas copia os arquivos
# para o diretório de extensões do Postgres.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential ca-certificates curl postgresql-server-dev-17 \
    && curl -fsSL "https://github.com/pgmq/pgmq/archive/refs/tags/v${PGMQ_VERSION}.tar.gz" \
        | tar -xz -C /tmp \
    && make -C "/tmp/pgmq-${PGMQ_VERSION}/pgmq-extension" \
    && make -C "/tmp/pgmq-${PGMQ_VERSION}/pgmq-extension" install \
    && rm -rf "/tmp/pgmq-${PGMQ_VERSION}" \
    && apt-get purge -y --auto-remove build-essential curl postgresql-server-dev-17 \
    && rm -rf /var/lib/apt/lists/*
