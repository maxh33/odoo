# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 🎯 Quick Navigation

**For immediate context**: [AGENT-CONTEXT.md](AGENT-CONTEXT.md) - Essential quick reference
**For detailed navigation**: [TABLE-OF-CONTENTS.md](TABLE-OF-CONTENTS.md) - Master index organized by role and task

---

## Project Overview


This is a **Multi-Tenant Odoo 18 Community Platform** serving multiple business types (jewelry, retail, manufacturing, services) with configurable tenant templates, automated N8N workflows, and scalable PostgreSQL multi-database architecture.

**Current Status** (2026-01-15):
- ✅ Jewelry Template: Production-ready with CPL supplier integration
- ✅ Multi-tenant infrastructure: Docker deployment with Traefik routing
- ✅ E-commerce Phase 1: WordPress 6.9 + WooCommerce 10.4.3 + MinIO + PostgreSQL 16 (local)
- ⏳ E-commerce Phase 2: Odoo ↔ WooCommerce integration layer (next)
- ⏳ E-commerce Phase 3: VPS production deployment
- ⏳ Retail/Manufacturing/Services Templates: Planned
- ⏳ N8N Automation: Framework ready, workflows pending

---

## 📋 Documentation Structure

All comprehensive guides have been split into specialized documents for easier navigation:

### Core Platform Documentation

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [AGENT-CONTEXT.md](AGENT-CONTEXT.md) | Quick reference, formulas, paths, commands | First reference for any task |
| [TABLE-OF-CONTENTS.md](TABLE-OF-CONTENTS.md) | Master index by role and task | Finding specific documentation |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Docker deployment, VPS setup, CI/CD | Deploying locally or to production |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, components, integrations | Understanding the system |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Development workflows, guidelines, testing | Building features or modules |
| [MULTI-TENANT-OPERATIONS.md](MULTI-TENANT-OPERATIONS.md) | Tenant creation, management, checklists | Managing tenants |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues, diagnostics, solutions | Fixing problems |
| [API.md](API.md) | Webhook endpoints, XML-RPC methods | Integration development |

### Business Templates

| Template | Status | Documentation |
|----------|--------|---------------|
| Jewelry | ✅ Production | [jewelry_template/GUIDE.md](addons/tenant_templates/jewelry_template/GUIDE.md) |
| Retail | ⏳ Planned | Coming soon |
| Manufacturing | ⏳ Planned | Coming soon |
| Services | ⏳ Planned | Coming soon |

### E-commerce Integration

| Component | Status | Location |
|-----------|--------|----------|
| WooCommerce Stack | ✅ Phase 1 Complete | `D:\Programacao\Repositorios\odoo-ecommerce` |
| Integration Layer | ⏳ Phase 2 | `odoo-ecommerce/integration/` |
| VPS Deployment | ⏳ Phase 3 | `odoo-ecommerce/docker-compose.prod.yml` |
| Planning Docs | ✅ Complete | [supplier/log.md](addons/tenant_templates/supplier/log.md) |

---

## 🚀 Quick Start

### Local Development

```bash
# 1. Clone and setup
git clone <repository-url> odoo-platform
cd odoo-platform
cp .env.example .env

# 2. Start with minimal configuration
docker-compose up -d

# 3. Verify
docker logs odoo_community_18 | grep "HTTP service"
curl -I http://localhost:8069

# 4. Access
# Browser: http://localhost:8069
# Save the generated master password!
```

**For detailed deployment instructions**: See [DEPLOYMENT.md](DEPLOYMENT.md)

---

## 📁 Directory Structure

```
odoo-platform/
├── addons/
│   ├── tenant_templates/           # Business templates
│   │   ├── jewelry_template/       # ✅ Production ready
│   │   ├── retail_template/        # ⏳ Planned
│   │   └── ...
│   ├── multi_tenant_core/          # Core multi-tenancy
│   ├── n8n_connector/              # N8N integration
│   └── integration_modules/        # E-commerce connectors
├── configs/
│   └── odoo/
│       ├── odoo-minimal.conf       # Development (proven working)
│       └── odoo.conf               # Production
├── docker-compose.yml              # Local deployment
└── scripts/                        # Deployment and migration
```

**For complete structure**: See [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 🔑 Key Integration Points

### Multi-Tenant Architecture
- **Database per tenant**: `tenant_{business_type}_{name}`
- **Subdomain routing**: `tenant-name.odoo.maxhaider.dev`
- **Row-level security**: Hard-coded `tenant_id = 1` (current limitation)

### N8N Automation
- **Market price updates**: Gold/silver price automation
- **Inventory sync**: Multi-platform synchronization
- **Webhook framework**: Ready for workflow integration

### E-commerce Sync (WooCommerce)
- **Repository**: `D:\Programacao\Repositorios\odoo-ecommerce` (separate repo)
- **Stack**: WordPress 6.9 + WooCommerce 10.4.3 + MinIO S3 + PostgreSQL 16
- **Status**: Phase 1 ✅ Local environment ready
- **Phase 2**: Integration layer (Odoo XML-RPC → WooCommerce REST API)
- **Phase 3**: VPS production with Traefik routing

**Access Points** (local):
- WordPress: `http://localhost:8080`
- MinIO Console: `http://localhost:9001`
- PostgreSQL: `localhost:5433`

**For integration details**: See [ARCHITECTURE.md](ARCHITECTURE.md), [API.md](API.md), and [supplier/log.md](addons/tenant_templates/supplier/log.md)

---

## 💎 Jewelry Template Highlights

**CPL Supplier Integration** (✅ Production Ready):
- 41 ring size variants (sizes 6-46) per product
- Automatic calculations: Weight → Cost → Price
- Gold market price automation
- Bulk import capability

**Business Formulas**:
```
Weight = Base Weight × COEF × Size Adjustment Factor
Cost = Weight × Gold Price/gram × Purity × Provider Index
Price = Cost × (1 + Markup%)
```

**Quick Start**:
```bash
cd addons/tenant_templates/jewelry_template/import
python3 bulk_import_cpl_products.py --csv products.csv --db tenant_joiasmax --password admin
```

**For complete guide**: See [jewelry_template/GUIDE.md](addons/tenant_templates/jewelry_template/GUIDE.md)

---

## 🛠️ Common Development Tasks

### "I need to deploy locally"
→ [DEPLOYMENT.md](DEPLOYMENT.md) → Quick Start section

### "I need to add a new tenant"
→ [MULTI-TENANT-OPERATIONS.md](MULTI-TENANT-OPERATIONS.md) → Tenant Creation

### "I need to import CPL products"
→ [jewelry_template/import/CPL_WORKFLOW_SUMMARY.md](addons/tenant_templates/jewelry_template/import/CPL_WORKFLOW_SUMMARY.md)

### "I need to troubleshoot an issue"
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md) → Common Issues

### "I need to develop a new module"
→ [DEVELOPMENT.md](DEVELOPMENT.md) → Custom Module Development

### "I need to add a new supplier (Gold Indice, Cronus, etc.)"
→ [jewelry_template/GUIDE.md](addons/tenant_templates/jewelry_template/GUIDE.md) → Reusable Patterns section

### "I need to work on WooCommerce integration"
→ [supplier/log.md](addons/tenant_templates/supplier/log.md) → Phase 2/3 sections
→ Repository: `D:\Programacao\Repositorios\odoo-ecommerce`

### "I need to sync products to WooCommerce"
→ Phase 2 integration layer at `odoo-ecommerce/integration/sync/products.py`

---

## 🎯 Development Standards

- **Odoo 18 Standards**: Follow community guidelines
- **Multi-tenant Isolation**: All custom models MUST have `tenant_id` field + RLS rules
- **External IDs**: Use for idempotent imports
- **Computed Fields**: Use `@api.depends()` decorator
- **Audit Trails**: Log all price/cost changes
- **API Keys**: Validate webhook calls

**For detailed guidelines**: See [DEVELOPMENT.md](DEVELOPMENT.md)

---

## 📞 Support & References

### Documentation Navigation
- Start here: [AGENT-CONTEXT.md](AGENT-CONTEXT.md)
- Find anything: [TABLE-OF-CONTENTS.md](TABLE-OF-CONTENTS.md)
- Report issues: `https://github.com/anthropics/claude-code/issues`

### External References
- **VPS Infrastructure**: See `D:\Programacao\Repositorios\my-portfolio\CLAUDE.md`
- **Odoo Official**: https://www.odoo.com/documentation/18.0/

---

**Last Updated**: 2026-01-15
**Project Type**: Multi-Tenant Odoo 18 Community Platform
**Primary Contact**: Development Team

**For detailed information on any topic, see [TABLE-OF-CONTENTS.md](TABLE-OF-CONTENTS.md)**
