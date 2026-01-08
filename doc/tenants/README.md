# Tenant Documentation Structure

This directory contains tenant-specific documentation for the multi-tenant Odoo platform.

## Documentation Organization

### Global Platform Documentation
Located in `/docs/` (parent directory):
- `PROJECT_STRUCTURE.md` - Overall project organization
- `DIRECTORY_STRUCTURE.md` - File system layout
- `CONFIGURATION-GUIDE.md` - Platform configuration

### Tenant-Specific Documentation
Located in `/docs/tenants/{tenant-name}/`:
- Business requirements
- Custom module specifications
- Integration details
- Deployment notes

## Current Tenants

### JoiasMax (Gold Jewelry E-commerce)
**Status**: 📋 Planning Phase  
**Custom Module**: Dynamic Precious Metals Pricing  
**Documentation Location**: External repository

#### Documentation References

**Primary Specs** (joiasmax-ecommerce repository):
```
D:\Programacao\Repositorios\joiasmax-ecommerce\doc\dynamicPricing\
├── README.md                          # Overview and navigation
├── 01-executive-summary.md            # Business case and solution
├── 02-current-situation.md            # Bling data structure issues
├── 03-architecture.md                 # System design and data flows
├── 04-data-model.md                   # PostgreSQL schemas (4 custom tables)
├── 05-data-cleanup.md                 # Data extraction strategy
├── 06-automation-workflows.md         # n8n automation
├── 07-implementation-roadmap.md       # 10-week timeline
├── 08-scripts-tools.md                # Python utilities
├── 09-performance-testing.md          # Optimization
└── 10-risks-success.md                # Risk management
```

**Key Features**:
- Automated gold/silver pricing based on market quotations
- Complex pricing formula with fixed/variable costs
- n8n workflow integration
- WooCommerce bidirectional sync
- Complete price change audit trail

**Technical Implementation**:
```
Location: odoo/addons/tenant_templates/jewelry_template/joiasmax_pricing/
Module Name: joiasmax_pricing
Database Tables: 4 custom tables extending product.template
- precious_metal_product (metal attributes)
- metal_quotation_history (market prices)
- price_update_log (audit trail)
- pricing_config (formula parameters)
```

**Migration Plan**:
- Migrate from Bling ERP to Odoo
- Import ~1500 products (gold, silver, steel)
- Data cleanup required (weights in text descriptions)
- Parallel operation with Bling for 2 weeks
- Go-live: Week 9 of implementation

#### Linear Project
**Project**: Odoo Multi-Tenant Platform - JoiasMax ERP Migration  
**URL**: https://linear.app/maxhaiderdev/project/odoo-multi-tenant-platform-joiasmax-erp-migration-1e05d7e6d94d

**Key Issues**:
- MAX-34: Configure GitHub Secrets (P1 - Urgent)
- MAX-35: Configure Local .env (P1 - Urgent)
- MAX-36: Test Local Deployment (P1 - Urgent)
- MAX-37: Deploy Odoo to VPS (P2 - High)
- MAX-38: Create JoiasMax Tenant (P2 - High)
- MAX-39: Develop Dynamic Pricing Module (P2 - High) **CORE VALUE**

---

## Future Tenants

### Placeholder for Additional Tenants
As the platform grows, additional tenant documentation will be organized here following the same structure.

**Template Structure**:
```
/docs/tenants/{tenant-name}/
├── README.md                   # Tenant overview
├── business-requirements.md    # Business needs
├── technical-specs.md          # Custom modules and integrations
├── deployment-notes.md         # Specific configurations
└── data-migration.md           # Migration plan (if applicable)
```

---

## Documentation Best Practices

### For New Tenants

1. **Create Tenant Directory**
   ```bash
   mkdir docs/tenants/{tenant-name}
   ```

2. **Document Business Requirements**
   - Problem statement
   - Proposed solution
   - Success criteria

3. **Specify Technical Implementation**
   - Custom modules needed
   - Database schema changes
   - Integration requirements
   - Performance considerations

4. **Plan Deployment**
   - Configuration requirements
   - Domain setup
   - User accounts
   - Training needs

5. **Link to Linear Project**
   - Create Linear project for tenant
   - Reference in documentation
   - Track implementation progress

### Cross-Repository Documentation

When tenant documentation exists in external repositories (like JoiasMax):
- Reference location in this document
- Maintain high-level overview here
- Link to Linear project for tasks
- Keep deployment/configuration notes here

---

## Maintenance

### Regular Updates
- Update tenant status as implementation progresses
- Document lessons learned
- Update technical specs as requirements evolve
- Keep Linear project references current

### Documentation Review
- Quarterly review of tenant documentation
- Update as business requirements change
- Archive deprecated tenants (with historical reference)

---

**Last Updated**: 2025-12-11  
**Maintainer**: Max Haider
