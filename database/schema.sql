CREATE TABLE IF NOT EXISTS jobs (
    id              SERIAL PRIMARY KEY,
    source          VARCHAR(50),
    external_id     VARCHAR(255),
    title           VARCHAR(500),
    company         VARCHAR(255),
    location        VARCHAR(255),
    country         VARCHAR(100),
    salary_min      NUMERIC,
    salary_max      NUMERIC,
    description     TEXT,
    url             VARCHAR(1000),
    tags            TEXT,
    job_type        VARCHAR(100),
    contract_time   VARCHAR(50),
    contract_type   VARCHAR(50),
    created_at      TIMESTAMP,
    extracted_at    TIMESTAMP DEFAULT NOW(),

    CONSTRAINT uq_source_external_id UNIQUE (source, external_id)
);