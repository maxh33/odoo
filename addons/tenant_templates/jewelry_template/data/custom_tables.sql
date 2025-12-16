-- Custom tables for JoiasMax dynamic pricing

-- Table 1: Product Pricing Intelligence
CREATE TABLE IF NOT EXISTS joiasmax_product_pricing (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    tenant_id INTEGER,

    -- Material Information
    material_type VARCHAR(50) NOT NULL,
    metal_weight_grams NUMERIC(10, 3),
    metal_purity VARCHAR(10),
    gemstone_type VARCHAR(50),
    gemstone_carats NUMERIC(8, 3),

    -- Cost Components
    material_cost_brl NUMERIC(12, 2),
    labor_cost_brl NUMERIC(12, 2),
    overhead_cost_brl NUMERIC(12, 2),
    total_cost_brl NUMERIC(12, 2),

    -- Pricing Strategy
    markup_percentage NUMERIC(5, 2) DEFAULT 200.00,
    calculated_price_brl NUMERIC(12, 2),
    manual_override_price NUMERIC(12, 2),
    use_manual_override BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(product_id, tenant_id)
);

-- Table 2: Market Prices (Gold, Silver, etc.)
CREATE TABLE IF NOT EXISTS joiasmax_market_prices (
    id SERIAL PRIMARY KEY,
    material_type VARCHAR(50) NOT NULL,
    price_per_gram_brl NUMERIC(12, 4) NOT NULL,
    source_api VARCHAR(100),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Table 3: Supplier Costs
CREATE TABLE IF NOT EXISTS joiasmax_supplier_costs (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    unit_cost_brl NUMERIC(12, 2) NOT NULL,
    last_purchase_date DATE,
    valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_until DATE,
    is_preferred_supplier BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 4: Price Change History (Audit Trail)
CREATE TABLE IF NOT EXISTS joiasmax_price_history (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    old_price_brl NUMERIC(12, 2),
    new_price_brl NUMERIC(12, 2) NOT NULL,
    price_difference_brl NUMERIC(12, 2),
    change_reason VARCHAR(50) NOT NULL,
    change_details TEXT,
    changed_by_user_id INTEGER,
    gold_price_at_change NUMERIC(12, 4),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_to_woocommerce BOOLEAN DEFAULT FALSE
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_pricing_product ON joiasmax_product_pricing(product_id);
CREATE INDEX IF NOT EXISTS idx_pricing_material ON joiasmax_product_pricing(material_type);
CREATE INDEX IF NOT EXISTS idx_market_active ON joiasmax_market_prices(is_active, fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_supplier_product ON joiasmax_supplier_costs(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_product ON joiasmax_price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_date ON joiasmax_price_history(changed_at DESC);

-- Sample Market Price Data (Initial Values)
INSERT INTO joiasmax_market_prices (material_type, price_per_gram_brl, source_api) VALUES
('gold_24k', 385.50, 'manual_initial'),
('gold_18k', 289.13, 'manual_initial'),
('silver_950', 4.50, 'manual_initial'),
('diamond_1ct_vs1', 35000.00, 'manual_initial')
ON CONFLICT DO NOTHING;

COMMENT ON TABLE joiasmax_product_pricing IS 'Jewelry-specific pricing data with material breakdown';
COMMENT ON TABLE joiasmax_market_prices IS 'Current market prices for precious materials';
COMMENT ON TABLE joiasmax_supplier_costs IS 'Historical supplier cost tracking';
COMMENT ON TABLE joiasmax_price_history IS 'Complete audit trail of all price changes';
