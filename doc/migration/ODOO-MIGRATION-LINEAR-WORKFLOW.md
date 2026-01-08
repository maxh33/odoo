# Odoo Migration - Linear Workflow Summary

**Created**: 2025-12-11  
**Project**: Odoo Multi-Tenant Platform - JoiasMax ERP Migration  
**Linear URL**: https://linear.app/maxhaiderdev/project/odoo-multi-tenant-platform-joiasmax-erp-migration-1e05d7e6d94d

---

## 📊 Overview

Complete Linear workflow created for Odoo 18 multi-tenant platform deployment with JoiasMax as first production tenant. Workflow prioritized by dependencies and business value.

**Total Issues Created**: 6  
**Priority Breakdown**:
- P1 (Urgent): 3 issues - Prerequisites and local validation
- P2 (High): 3 issues - Infrastructure deployment and business logic

---

## 🎯 Prioritized Workflow

### PHASE 1: Prerequisites (P1 - URGENT) ⚡

Must complete BEFORE any deployment can happen.

#### MAX-34: 🔐 Configure GitHub Repository Secrets
**Priority**: P1 (Urgent)  
**Status**: Backlog  
**Blocks**: All automated deployment

**Critical Secrets Needed**:
- VPS_KEY (SSH access to server)
- VPS_PASSPHRASE
- GHCR_TOKEN (GitHub Container Registry)
- ODOO_DB_PASSWORD
- ODOO_ADMIN_PASSWORD
- EMAIL_PASS
- GOLD_PRICE_API_KEY (Metals.dev)
- N8N_API_KEY
- JWT_SECRET

**Action Required**: Add secrets in GitHub repository settings

---

#### MAX-35: ⚙️ Configure Local .env File  
**Priority**: P1 (Urgent)  
**Status**: Backlog  
**Depends On**: None

**Tasks**:
1. Copy `.env.example` to `.env`
2. Fill in essential variables
3. Register for Metals.dev API key (free tier, 5000 requests/month)
4. Generate N8N API key
5. Set strong passwords

**Location**: `D:\Programacao\Repositorios\odoo\.env`

---

#### MAX-36: 🧪 Test Local Odoo Deployment
**Priority**: P1 (Urgent)  
**Status**: Backlog  
**Depends On**: MAX-35

**Purpose**: Validate setup before VPS deployment

**Steps**:
1. Start Docker containers locally
2. Verify HTTP service running
3. Access database manager
4. Create test database
5. Validate Brazilian localization

**Success Criteria**:
✅ Odoo accessible at http://localhost:8069  
✅ Can create database  
✅ Portuguese (BR) working  
✅ No critical errors

---

### PHASE 2: Infrastructure (P2 - HIGH) 🏗️

Deploy production infrastructure after local validation.

#### MAX-37: 🚀 Deploy Odoo to VPS
**Priority**: P2 (High)  
**Status**: Backlog  
**Depends On**: MAX-34, MAX-35, MAX-36, WordPress Migration Complete

**Deployment Options**:
- **Option A**: GitHub Actions (automated, recommended)
- **Option B**: Manual deployment via SSH

**Key Tasks**:
- Configure DNS (odoo.maxhaider.dev)
- Integrate with Traefik for SSL
- Set up monitoring (Prometheus/Grafana)
- Configure automated backups
- Health checks and validation

**Success Criteria**:
✅ Accessible at https://odoo.maxhaider.dev  
✅ SSL certificate valid  
✅ Monitoring integrated  
✅ Backups configured

---

#### MAX-38: 🏪 Create JoiasMax Tenant Database
**Priority**: P2 (High)  
**Status**: Backlog  
**Depends On**: MAX-37

**Purpose**: First production tenant for gold jewelry e-commerce

**Configuration**:
- Database: `joiasmax_prod`
- Domain: `joiasmax.odoo.maxhaider.dev`
- Language: Portuguese (BR)
- Currency: BRL (R$)
- Company: JoiasMax E-commerce

**Modules to Install**:
- Brazilian localization (l10n_br_*)
- Sales Management
- Inventory Management
- eCommerce (WooCommerce prep)

**Product Categories**:
- Gold 18K (750)
- Gold 10K (416)
- Silver 950/925
- Stainless Steel 316L

---

### PHASE 3: Business Logic (P2 - HIGH) 💎

**CORE BUSINESS VALUE** - The reason for Odoo migration!

#### MAX-39: 💎 Develop Dynamic Pricing Custom Module
**Priority**: P2 (High)  
**Status**: Backlog  
**Depends On**: MAX-38

**Purpose**: Automated precious metals pricing based on market quotations

**Module Name**: `joiasmax_pricing`  
**Location**: `odoo/addons/tenant_templates/jewelry_template/joiasmax_pricing/`

**Database Schema** (4 Custom Tables):

1. **precious_metal_product** - Extends product.template
   - metal_type (gold/silver/steel)
   - metal_weight_grams
   - metal_purity (750, 416, 950, 925)
   - supplier_cost_index
   - labor_cost
   - calculated_base_cost

2. **metal_quotation_history** - Market price tracking
   - date
   - metal_type
   - price_per_gram (BRL)
   - source_api
   - api_response (JSON)

3. **price_update_log** - Complete audit trail
   - product_id
   - old_price / new_price
   - quotation_id
   - reason (quotation_change, manual, cost_adjustment)
   - triggered_by (n8n, manual, scheduled_job)

4. **pricing_config** - Formula parameters
   - Tax: 7%
   - Commission: 5%
   - Installment fee: 7.5%
   - Profit margin: 5%
   - Fixed costs: R$ 2,422/month
   - Operational: R$ 812/month
   - Avg sales: 7.25 units/month

**Pricing Formula**:
```python
# Base cost
base = quotation × weight × purity × supplier_index + labor

# Fixed per unit
fixed_unit = (2422 + 812) / 7.25 = R$ 445.93

# Total fixed
total_fixed = base + labor + 14 + 445.93

# Divisor
divisor = (1 - 0.245) × (1 - 0.035) = 0.7286

# Final price
sale_price = total_fixed / 0.7286
```

**Test Cases**:
- Gold 18K ring: R$ 385.50/g × 2.5g × 0.75 × 1.1 = Expected: R$ 1,722.07
- Silver chain: R$ 4.50/g × 15g × 0.95 × 1.05 + R$ 20 labor = Expected: R$ 751.02

**Integration Points**:
- n8n webhook for quotation updates (every 6 hours)
- WooCommerce price sync
- Bling data import

---

## 📋 Next Issues to Create (Future)

After completing MAX-34 through MAX-39, additional issues needed:

### Data Migration (P3 - Medium)
- **MAX-40**: Set up n8n gold price automation workflow
- **MAX-41**: Create Python data extraction scripts (weight/material from descriptions)
- **MAX-42**: Import Bling product data to Odoo
- **MAX-43**: Configure WooCommerce bidirectional sync
- **MAX-44**: Parallel operation testing (Bling + Odoo)

### Production Cutover (P3 - Medium)
- **MAX-45**: Final data migration
- **MAX-46**: DNS cutover and monitoring
- **MAX-47**: Post-deployment optimization

---

## 📚 Documentation References

### Odoo Repository
- **README.md**: Platform overview
- **CLAUDE.md**: Complete development guide
- **docs/tenants/README.md**: Tenant documentation structure (NEW!)

### JoiasMax Repository
- **Dynamic Pricing Specs**: `D:\Programacao\Repositorios\joiasmax-ecommerce\doc\dynamicPricing\`
  - 10 detailed markdown files (65.89 KB total)
  - Complete business case, technical specs, and implementation roadmap
  - Database schemas, formulas, test cases
  - 10-week implementation timeline

### Linear Project
- **URL**: https://linear.app/maxhaiderdev/project/odoo-multi-tenant-platform-joiasmax-erp-migration-1e05d7e6d94d
- **Team**: Maxhaiderdev
- **Timeline**: Jan 6, 2025 → Feb 28, 2025

---

## 🎯 Critical Path

```
START
  ↓
MAX-34 (GitHub Secrets) ← MUST DO FIRST
  ↓
MAX-35 (.env Config) ← Configure locally
  ↓
MAX-36 (Test Local) ← Validate before VPS
  ↓
WordPress Migration Complete ← WAIT for this
  ↓
MAX-37 (Deploy VPS) ← Production infrastructure
  ↓
MAX-38 (Create Tenant) ← JoiasMax database
  ↓
MAX-39 (Dynamic Pricing Module) ← CORE BUSINESS VALUE
  ↓
[Future issues for data migration & automation]
  ↓
PRODUCTION CUTOVER
```

---

## ⚡ Immediate Next Steps

### This Week (Priority Order):

1. **MAX-34**: Add GitHub secrets
   - Action: Go to GitHub repository settings
   - Add all required secrets
   - Test access in GitHub Actions

2. **MAX-35**: Configure local .env
   - Action: Copy .env.example
   - Register for Metals.dev API key
   - Fill in all variables

3. **MAX-36**: Test local deployment
   - Action: `docker-compose up -d`
   - Verify Odoo starts
   - Create test database

### After WordPress Migration:

4. **MAX-37**: Deploy to VPS
5. **MAX-38**: Create JoiasMax tenant
6. **MAX-39**: Develop dynamic pricing module

---

## 💡 Key Insights

### Why This Order?

1. **Prerequisites First** (MAX-34, MAX-35)
   - No point deploying without proper configuration
   - Secrets block all automation
   - .env needed for local testing

2. **Local Validation** (MAX-36)
   - Catch issues before VPS deployment
   - Cheaper to debug locally
   - Faster iteration

3. **Infrastructure Then Business Logic**
   - Need platform running (MAX-37, MAX-38)
   - Before developing custom modules (MAX-39)
   - Can't test pricing without tenant

4. **Sequential, Not Parallel**
   - Each phase depends on previous
   - Reduces risk of conflicts
   - Easier troubleshooting

### Documentation Strategy

**Use joiasmax-ecommerce repo for business specs**:
- ✅ Detailed planning documents (65KB of specs!)
- ✅ Formula calculations and test cases
- ✅ Data model design
- ✅ Implementation roadmap

**Use odoo repo for technical implementation**:
- ✅ Actual custom module code
- ✅ Deployment configurations
- ✅ Multi-tenant infrastructure
- ✅ Platform-wide documentation

**Reference Link**: `docs/tenants/README.md` connects both repositories

---

## 🔄 Multi-Tenant Advantage

**JoiasMax is First Tenant**, but architecture supports:
- Multiple business types (retail, manufacturing, services)
- Shared infrastructure (cost savings)
- Isolated databases (security)
- Business-specific templates
- Scalable to dozens of tenants

**Future Growth Path**:
1. JoiasMax (jewelry - FIRST)
2. Other jewelry stores (use same template)
3. Retail businesses (different template)
4. Service companies (different template)
5. Custom tenants (build new templates)

---

## 📊 Success Metrics

After MAX-39 complete, should achieve:

**Business Goals**:
- ✅ Zero products with negative margins
- ✅ Gold prices updated 3-6x daily (automatic)
- ✅ <5 minute Odoo → WooCommerce sync
- ✅ Complete price change audit trail
- ✅ <5% products requiring manual review

**Technical Goals**:
- ✅ Price calculation: <30 sec for 1500 products
- ✅ WooCommerce sync: <5 minutes
- ✅ 100% gold products with accurate weight
- ✅ 95%+ average data quality score
- ✅ <1% failed WooCommerce syncs

**Financial Impact**:
- Stop selling at loss: +R$ 2,500+/month
- Time saved: 10 hours/week (manual pricing eliminated)
- Break-even: Week 1 (first loss prevented)
- 5-year savings: Significant vs Bling ERP

---

## 🚨 Remember

**DO NOT IMPLEMENT** dynamic pricing until:
- ✅ WordPress migration complete (Weeks 1-2)
- ✅ Odoo deployed and stable
- ✅ JoiasMax tenant created
- ✅ Custom module tested with sample data
- ✅ All stakeholders approve

**This is Week 3-4 work**, not immediate!

---

**Created by**: Claude (via Linear MCP)  
**Date**: December 11, 2025  
**Status**: Ready for execution
