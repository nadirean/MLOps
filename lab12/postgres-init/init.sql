CREATE TABLE exchange_rates (
    symbol VARCHAR(50),
    rate FLOAT
);

CREATE TABLE IF NOT EXISTS model_performance (
    id SERIAL PRIMARY KEY,
    training_date TIMESTAMPTZ NOT NULL,
    model_name TEXT NOT NULL,
    train_size INTEGER NOT NULL,
    test_mae DOUBLE PRECISION NOT NULL
);
