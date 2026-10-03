-- Executado apenas na primeira inicialização do volume do Postgres
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgmq;

-- Fila de exemplo do PGMQ
SELECT pgmq.create('default');
