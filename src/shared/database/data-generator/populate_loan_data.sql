-- Create the table for loan products
CREATE TABLE IF NOT EXISTS loan_products (
    document_id TEXT PRIMARY KEY,
    region TEXT,
    language TEXT,
    document_type TEXT,
    loan_type TEXT,
    min_credit_score INTEGER,
    product_name TEXT,
    interest_rate_range TEXT,
    estimated_closing_costs TEXT,
    loan_term TEXT,
    max_dti REAL,
    allowed_property_types TEXT
);

