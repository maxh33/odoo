# E-commerce Architecture Plan

## Overview

Separate repository for e-commerce frontend, keeping Odoo focused on ERP backend.

## Repository Structure

```
d:\Programacao\Repositorios\
├── odoo\                           # ERP Backend (THIS REPO)
│   ├── docker-compose.yml          # Odoo + PostgreSQL
│   └── addons/tenant_templates/    # Business logic, pricing engine
│
└── odoo-ecommerce\                 # E-commerce Frontend (NEW REPO)
    ├── docker-compose.yml          # WordPress + WooCommerce + MinIO
    ├── wordpress/                  # WordPress multi-site
    │   ├── wp-content/
    │   │   ├── plugins/
    │   │   │   ├── woocommerce/
    │   │   │   └── odoo-sync/     # Custom Odoo integration plugin
    │   │   └── themes/
    │   │       └── joiasmax/       # Custom jewelry theme
    │   └── wp-config.php
    ├── minio/                      # MinIO S3-compatible storage
    │   ├── buckets/
    │   │   ├── odoo-products/     # Product images
    │   │   └── tenant-assets/     # Tenant-specific assets
    │   └── policies/
    ├── integration/                # Odoo ↔ WooCommerce sync
    │   ├── sync_products.py       # Product catalog sync
    │   ├── sync_inventory.py      # Stock level sync
    │   ├── sync_orders.py         # Order import to Odoo
    │   └── webhooks/              # Real-time event handlers
    └── nginx/                      # Optional reverse proxy for WP
```

## Network Architecture

### Local Development

```
┌─────────────────────────────────────────────────────────────┐
│  Docker Network: odoo_ecommerce_shared                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Odoo       │◄──►│    MinIO     │◄──►│  WordPress   │ │
│  │  (ERP)       │    │  (Storage)   │    │ (Storefront) │ │
│  │ :8069        │    │  :9000       │    │  :8080       │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                    │         │
│         └────────────────────┼────────────────────┘         │
│                              │                              │
│                    ┌─────────▼─────────┐                   │
│                    │   PostgreSQL      │                   │
│                    │  (Shared DB)      │                   │
│                    │    :5432          │                   │
│                    └───────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### VPS Production

```
                        Internet
                           │
                    ┌──────▼──────┐
                    │   Traefik   │
                    │ (SSL + LB)  │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼────────┐  ┌──────▼──────┐  ┌───────▼────────┐
│ odoo.maxhaider │  │ minio.max   │  │ shop.maxhaider │
│ .dev           │  │ haider.dev  │  │ .dev           │
│                │  │             │  │                │
│ Odoo ERP       │  │ MinIO S3    │  │ WordPress      │
│ Multi-tenant   │  │ Storage     │  │ Multi-site     │
└────────────────┘  └─────────────┘  └────────────────┘
         │                  │                  │
         └──────────────────┼──────────────────┘
                            │
                 monitoring_shared_monitoring_network
```

## Multi-Tenancy Strategy

### WordPress Multi-Site Setup

**Tenant Domains**:
- Tenant 1: `joiasmax.shop` → WordPress site ID: 1
- Tenant 2: `outrajoalheria.shop` → WordPress site ID: 2
- Tenant 3: `lojaprata.shop` → WordPress site ID: 3

**Odoo Tenant Mapping**:
```python
# integration/tenant_mapping.py
TENANT_MAP = {
    'tenant_joiasmax': {
        'wp_site_id': 1,
        'domain': 'joiasmax.shop',
        'woo_api_key': 'ck_xxx',
        'woo_api_secret': 'cs_xxx',
    },
    'tenant_outrajoalheria': {
        'wp_site_id': 2,
        'domain': 'outrajoalheria.shop',
        'woo_api_key': 'ck_yyy',
        'woo_api_secret': 'cs_yyy',
    },
}
```

### MinIO Bucket Strategy

**Per-Tenant Buckets**:
- `odoo-products-tenant1/` - JoiasMax product images
- `odoo-products-tenant2/` - Outra Joalheria images
- `shared-assets/` - Shared logos, icons, etc.

**Access Control**:
- Each tenant has separate MinIO access credentials
- Bucket policies enforce tenant isolation
- Public read for product images

## Data Sync Workflow

### 1. Product Catalog Sync (Odoo → WooCommerce)

```python
# integration/sync_products.py
def sync_product_to_woocommerce(odoo_product_id, tenant_id):
    """
    Sync product from Odoo to WooCommerce

    Flow:
    1. Fetch product from Odoo (with jewelry pricing)
    2. Get MinIO image URLs
    3. Map to WooCommerce product format
    4. Create/update WooCommerce product
    5. Sync stock levels
    """

    # Get from Odoo
    odoo_product = odoo_api.get_product(odoo_product_id)

    # Map to WooCommerce
    woo_product = {
        'sku': odoo_product['default_code'],
        'name': odoo_product['name'],
        'price': odoo_product['calculated_price_brl'],
        'description': odoo_product['description_sale'],
        'images': [
            {'src': odoo_product['image_url']}  # MinIO URL
        ],
        'weight': str(odoo_product['weight']),
        'meta_data': [
            {'key': '_jewelry_weight', 'value': odoo_product['metal_weight_grams']},
            {'key': '_material_type', 'value': odoo_product['material_type']},
        ]
    }

    # Sync to WooCommerce
    woo_api.create_or_update_product(woo_product)
```

### 2. Inventory Sync (Real-time)

```python
# integration/sync_inventory.py
def sync_stock_levels():
    """
    Sync inventory from Odoo to WooCommerce
    Triggered by:
    - Odoo stock move confirmation
    - Scheduled cron job (every 5 minutes)
    """

    for tenant in tenants:
        odoo_stock = odoo_api.get_stock_levels(tenant['odoo_db'])

        for product_sku, qty in odoo_stock.items():
            woo_api.update_stock(
                site_id=tenant['wp_site_id'],
                sku=product_sku,
                quantity=qty
            )
```

### 3. Order Import (WooCommerce → Odoo)

```python
# integration/sync_orders.py
def import_woocommerce_order(woo_order_id, tenant_id):
    """
    Import order from WooCommerce to Odoo
    Triggered by WooCommerce webhook: order.created
    """

    woo_order = woo_api.get_order(woo_order_id)

    # Create sale order in Odoo
    odoo_order = {
        'partner_id': get_or_create_customer(woo_order['billing']),
        'order_line': [
            (0, 0, {
                'product_id': get_product_by_sku(line['sku']),
                'product_uom_qty': line['quantity'],
                'price_unit': line['price'],
            })
            for line in woo_order['line_items']
        ],
        'note': f"WooCommerce Order #{woo_order['number']}",
    }

    odoo_api.create_sale_order(odoo_order)
```

## Technology Stack

### E-commerce Repo Stack

**WordPress Multi-Site**:
- WordPress 6.4+
- WooCommerce 8.5+
- WordPress Multi-Site (subdomain or subdirectory)

**Plugins**:
- Media Cloud (MinIO S3 integration)
- WooCommerce REST API
- Custom Odoo Sync Plugin (to be developed)

**MinIO**:
- MinIO latest (S3-compatible)
- Public bucket for product images
- Private buckets for tenant-specific data

**Integration Layer**:
- Python 3.11+
- FastAPI (webhook receiver)
- Celery (async task queue)
- Redis (task broker)

### Odoo Repo Stack (Existing)

- Odoo 18 Community
- PostgreSQL 16
- Custom jewelry template
- XML-RPC API

## Development Workflow

### Phase 1: Local Setup (This Week)

1. **Create new repo**: `odoo-ecommerce`
2. **Setup docker-compose**: WordPress + MinIO + PostgreSQL
3. **Configure WordPress multi-site**: Single tenant for testing
4. **Deploy MinIO**: Create buckets, test image upload
5. **Test integration**: Manual product sync from Odoo

### Phase 2: Integration Development (Next Week)

1. **Build sync scripts**: Product catalog sync
2. **WooCommerce webhook handlers**: Order import
3. **Inventory sync**: Real-time stock updates
4. **Image management**: Upload to MinIO from Odoo import

### Phase 3: Multi-Tenant (Week 3)

1. **WordPress multi-site configuration**: Tenant isolation
2. **Tenant-specific WooCommerce stores**: Per-tenant config
3. **MinIO bucket policies**: Tenant data isolation
4. **Automated tenant provisioning**: Scripts to create new stores

### Phase 4: VPS Deployment (Week 4)

1. **Deploy to VPS**: Using Traefik for routing
2. **SSL configuration**: Let's Encrypt certificates
3. **Monitoring setup**: Integrate with existing Prometheus/Grafana
4. **Backup procedures**: Database + MinIO data

## Security Considerations

### API Security

- WooCommerce REST API: Use OAuth 1.0a or JWT
- Odoo XML-RPC: SSL/TLS encryption
- MinIO: Access keys with bucket policies

### Tenant Isolation

- WordPress: Separate database tables per site
- MinIO: Bucket policies enforce tenant boundaries
- Odoo: Database-level tenant separation

### Data Privacy

- Customer data: GDPR compliance
- Payment info: PCI-DSS (WooCommerce handles this)
- Image storage: Public URLs for products only

## Cost Considerations

### VPS Resources

**Current VPS Allocation**:
- Odoo: 1GB RAM, 0.7 CPU
- PostgreSQL: 256MB RAM, 0.2 CPU

**New E-commerce Stack**:
- WordPress: 512MB RAM, 0.3 CPU
- MinIO: 256MB RAM, 0.2 CPU
- Redis: 128MB RAM, 0.1 CPU

**Total**: ~2.1GB RAM, 1.5 CPU (within VPS capacity)

### Storage

- MinIO disk usage: ~10GB for 1000 products (avg 10 images/product)
- Database: ~500MB for WordPress multi-site
- Backups: Include in existing VPS backup strategy

## Next Steps

1. ✅ **Create `odoo-ecommerce` repository** (today)
2. ✅ **Setup basic docker-compose** with WordPress + MinIO
3. ✅ **Test MinIO deployment** and image upload
4. ✅ **Configure WordPress** for single-tenant testing
5. ✅ **Build first integration**: Product sync from Odoo

## Decision: Separate Repos

**RECOMMENDATION**: ✅ **Create separate `odoo-ecommerce` repository NOW**

**Rationale**:
- Clean separation of concerns (ERP vs Storefront)
- Independent scaling and deployment
- Easier team collaboration (backend vs frontend)
- MinIO logically belongs with e-commerce (serves product catalog)
- WordPress multi-site will grow complex - keep isolated

**Integration**:
- Both repos share `monitoring_shared_monitoring_network` on VPS
- API-based communication (REST, XML-RPC)
- Shared MinIO storage (each repo accesses independently)
