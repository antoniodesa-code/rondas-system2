-- Criado automaticamente pelo seed.py via SQLAlchemy
-- Este arquivo serve apenas como referência da estrutura

CREATE TABLE IF NOT EXISTS setores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL UNIQUE,
    ativo BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS tecnicos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    login VARCHAR(100) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS rondas (
    id SERIAL PRIMARY KEY,
    setor_id INTEGER REFERENCES setores(id),
    tecnico_id INTEGER REFERENCES tecnicos(id),
    sistema_operante BOOLEAN,
    usuario_utilizando BOOLEAN,
    observacao TEXT,
    status VARCHAR(20) DEFAULT 'pendente',
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS auditoria_confirmacao (
    id SERIAL PRIMARY KEY,
    ronda_id INTEGER REFERENCES rondas(id),
    ip VARCHAR(50),
    user_agent TEXT,
    fingerprint_hash VARCHAR(64),
    device_data TEXT,
    resposta VARCHAR(10) NOT NULL,
    confirmado_em TIMESTAMPTZ DEFAULT NOW()
);
