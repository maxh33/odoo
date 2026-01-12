# Odoo Multi-Tenant Platform - API Reference

> **Navigation**: [TABLE-OF-CONTENTS.md](TABLE-OF-CONTENTS.md) | [AGENT-CONTEXT.md](AGENT-CONTEXT.md)

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Odoo APIs](#odoo-apis)
4. [N8N Webhook Endpoints](#n8n-webhook-endpoints)
5. [Jewelry Template Webhooks](#jewelry-template-webhooks)
6. [XML-RPC Methods](#xml-rpc-methods)
7. [E-commerce Integration APIs](#e-commerce-integration-apis)

---

## Overview

This document describes all API endpoints, webhooks, and integration methods available in the Odoo multi-tenant platform.

**Base URLs**:
- **Odoo API**: `https://odoo.maxhaider.dev`
- **Tenant API**: `https://api.odoo.maxhaider.dev/tenant/{tenant-id}`
- **N8N Webhooks**: `https://n8n.maxhaider.dev/webhook/`

---

## Authentication

### API Key Authentication

Most webhook endpoints require API key authentication:

```bash
# Example request with API key
curl -X POST https://odoo.maxhaider.dev/api/v1/jewelry/update_market_price \
  -H "Content-Type: application/json" \
  -d '{"api_key": "your_api_key", "gold_24k": 700.0}'
```

**API Key Configuration**:
```python
# In Odoo: Settings > Technical > Parameters > System Parameters
# Key: jewelry.webhook_api_key
# Value: your_secure_api_key
```

### XML-RPC Authentication

For XML-RPC access, use standard Odoo authentication:

```python
import xmlrpc.client

# Authenticate
common = xmlrpc.client.ServerProxy('http://localhost:8069/xmlrpc/2/common')
uid = common.authenticate('database_name', 'username', 'password', {})

# Execute methods
models = xmlrpc.client.ServerProxy('http://localhost:8069/xmlrpc/2/object')
result = models.execute_kw('database_name', uid, 'password',
                           'product.template', 'search_read',
                           [[('is_jewelry', '=', True)]],
                           {'fields': ['name', 'default_code']})
```

---

## Odoo APIs

### Health Check

**Endpoint**: `GET /web/health`

**Response**:
```json
{
  "status": "pass"
}
```

**Usage**:
```bash
curl https://odoo.maxhaider.dev/web/health
```

### Products API

**Endpoint**: `GET /api/v1/products`

**Description**: List all products (requires custom implementation)

**Response**:
```json
{
  "products": [
    {
      "id": 1,
      "name": "Product Name",
      "sku": "SKU123",
      "price": 100.00
    }
  ]
}
```

### Tenant API

**Endpoint**: `GET /api/tenant/{tenant-id}`

**Description**: Access tenant-specific API

**Headers**:
- `Authorization: Bearer {token}`

---

## N8N Webhook Endpoints

### Gold Price Update

**Endpoint**: `POST /webhook/gold-price-update`

**Description**: N8N workflow triggers gold price updates in Odoo

**Payload**:
```json
{
  "gold_24k_usd": 60.50,
  "silver_950_usd": 0.85,
  "exchange_rate_brl": 5.25,
  "timestamp": "2026-01-12T10:30:00Z"
}
```

**N8N Workflow**:
1. Fetch gold price from external API
2. Calculate BRL price: `gold_24k_brl = gold_24k_usd * exchange_rate_brl`
3. Call Odoo webhook: `/api/v1/jewelry/update_market_price`

### WooCommerce Sync

**Endpoint**: `POST /webhook/woocommerce-sync`

**Description**: Triggers product synchronization with WooCommerce

**Payload**:
```json
{
  "tenant_id": "jewelry_store_1",
  "sync_type": "products",
  "direction": "odoo_to_woocommerce"
}
```

**Sync Types**:
- `products`: Product data synchronization
- `inventory`: Inventory levels
- `orders`: Order data
- `prices`: Price updates

### Tenant Notifications

**Endpoint**: `POST /webhook/tenant/{tenant-id}`

**Description**: Send notifications to specific tenant

**Payload**:
```json
{
  "notification_type": "low_stock",
  "product_id": 123,
  "current_qty": 5,
  "threshold": 10
}
```

---

## Jewelry Template Webhooks

### Update Market Price

**Endpoint**: `POST /api/v1/jewelry/update_market_price`

**Description**: Updates gold/silver market prices and triggers product recalculation

**Authentication**: API Key (in payload)

**Payload**:
```json
{
  "api_key": "your_webhook_api_key",
  "gold_24k_brl": 700.00,
  "silver_950_brl": 50.00,
  "exchange_rate": 5.25,
  "fetched_at": "2026-01-12T10:30:00Z",
  "source_api": "gold_api_com"
}
```

**Response**:
```json
{
  "status": "success",
  "products_updated": 150,
  "gold_price": 700.00,
  "silver_price": 50.00,
  "timestamp": "2026-01-12T10:30:05Z"
}
```

**Error Response**:
```json
{
  "status": "error",
  "error": "Unauthorized",
  "message": "Invalid API key"
}
```

### Recalculate Prices

**Endpoint**: `POST /api/v1/jewelry/recalculate_prices`

**Description**: Manually triggers price recalculation for all products or specific products

**Payload**:
```json
{
  "api_key": "your_webhook_api_key",
  "template_ids": [1, 2, 3],
  "material_type": "gold"
}
```

**Optional Parameters**:
- `template_ids`: Array of product template IDs (if omitted, updates all)
- `material_type`: Filter by material type ("gold" or "silver")

**Response**:
```json
{
  "success": true,
  "templates_processed": 50,
  "variants_recalculated": 2050
}
```

### Health Check (Jewelry-Specific)

**Endpoint**: `GET /api/v1/jewelry/recalculate_prices/health`

**Description**: Verify jewelry template configuration

**Response**:
```json
{
  "status": "healthy",
  "size_adjustments_loaded": 45,
  "size_based_templates": 150,
  "market_prices_active": 2
}
```

---

## XML-RPC Methods

### Market Price Update (Python Example)

```python
import xmlrpc.client

# Connection
url = 'http://localhost:8069'
db = 'tenant_joiasmax'
username = 'admin'
password = 'admin'

# Authenticate
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

# Models proxy
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Update market price
result = models.execute_kw(
    db, uid, password,
    'joiasmax.market.price',
    'update_from_n8n',
    [],
    {
        'gold_24k_brl': 700.0,
        'silver_950_brl': 50.0,
        'exchange_rate': 5.25
    }
)

print(result)  # {'status': 'success', 'products_updated': 150}
```

### Product Search and Read

```python
# Search for jewelry products
product_ids = models.execute_kw(
    db, uid, password,
    'product.template',
    'search',
    [[('is_jewelry', '=', True), ('has_size_based_pricing', '=', True)]]
)

# Read product details
products = models.execute_kw(
    db, uid, password,
    'product.template',
    'read',
    [product_ids],
    {'fields': ['name', 'default_code', 'metal_weight_grams', 'size_pricing_coef']}
)
```

### Create Product with Variants

```python
# Create product template
template_id = models.execute_kw(
    db, uid, password,
    'product.template',
    'create',
    [{
        'name': 'Wedding Ring C725R',
        'default_code': 'C725R',
        'is_jewelry': True,
        'material_type': 'gold_24k',
        'metal_weight_grams': 7.0,
        'metal_purity': 'gold_24k',
        'has_size_based_pricing': True,
        'size_pricing_coef': 1.15
    }]
)

# Create pricing record
pricing_id = models.execute_kw(
    db, uid, password,
    'joiasmax.jewelry.pricing',
    'create',
    [{
        'product_id': template_id,
        'provider_indice': 1.05,
        'markup_percentage': 200.0
    }]
)
```

### Force Price Recalculation

```python
# Get all jewelry pricing records
pricing_ids = models.execute_kw(
    db, uid, password,
    'joiasmax.jewelry.pricing',
    'search',
    [[]]
)

# Trigger recalculation
for pricing_id in pricing_ids:
    models.execute_kw(
        db, uid, password,
        'joiasmax.jewelry.pricing',
        'action_recalculate_costs',
        [[pricing_id]]
    )
```

---

## E-commerce Integration APIs

### WooCommerce Connector

**Configuration**:
```python
# Settings > Technical > Parameters > System Parameters
woocommerce.url = https://store.example.com
woocommerce.consumer_key = ck_xxxxxxxxxxxxx
woocommerce.consumer_secret = cs_xxxxxxxxxxxxx
```

**Sync Methods**:

```python
# Sync products to WooCommerce
models.execute_kw(
    db, uid, password,
    'woocommerce.connector',
    'sync_products',
    [],
    {'direction': 'odoo_to_woocommerce'}
)

# Sync orders from WooCommerce
models.execute_kw(
    db, uid, password,
    'woocommerce.connector',
    'sync_orders',
    [],
    {'direction': 'woocommerce_to_odoo'}
)
```

### Shopify Connector

**Configuration**:
```python
# Settings > Technical > Parameters > System Parameters
shopify.shop_url = yourstore.myshopify.com
shopify.api_key = xxxxxxxxxxxxx
shopify.api_secret = xxxxxxxxxxxxx
shopify.access_token = shpat_xxxxxxxxxxxxx
```

**Sync Methods**: Similar to WooCommerce connector

---

## Error Handling

### Common Error Responses

**Unauthorized (401)**:
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing API key"
}
```

**Bad Request (400)**:
```json
{
  "error": "Bad Request",
  "message": "Missing required parameter: gold_24k_brl"
}
```

**Server Error (500)**:
```json
{
  "error": "Internal Server Error",
  "message": "Failed to update market prices"
}
```

### Retry Logic

For N8N workflows, implement exponential backoff:

```javascript
// N8N Retry Configuration
{
  "retry": {
    "enabled": true,
    "maxRetries": 3,
    "waitBetween": 1000,
    "waitMultiplier": 2
  }
}
```

---

## Rate Limiting

**Webhook Endpoints**: No rate limiting (trusted internal N8N)

**Public APIs**: 100 requests per minute per IP

**XML-RPC**: Limited by Odoo configuration (`limit_request` parameter)

---

## Testing APIs

### Test Market Price Update

```bash
# Test webhook
curl -X POST http://localhost:8069/api/v1/jewelry/update_market_price \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "test_key",
    "gold_24k_brl": 700.0,
    "silver_950_brl": 50.0
  }'
```

### Test Health Check

```bash
# Jewelry template health
curl http://localhost:8069/api/v1/jewelry/recalculate_prices/health

# Odoo health
curl http://localhost:8069/web/health
```

---

**Related Documentation**:
- [ARCHITECTURE.md](ARCHITECTURE.md) - Integration architecture
- [DEVELOPMENT.md](DEVELOPMENT.md) - Custom webhook development
- [jewelry_template/GUIDE.md](addons/tenant_templates/jewelry_template/GUIDE.md) - Jewelry API details

**Last Updated**: 2026-01-12
