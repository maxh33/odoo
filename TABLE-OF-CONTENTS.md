# Odoo Multi-Tenant Platform - Documentation Index

## 🚀 Quick Start

- **New User?** Start here: [AGENT-CONTEXT.md](AGENT-CONTEXT.md)
- **First Deployment?** Follow: [DEPLOYMENT.md](DEPLOYMENT.md) → Quick Start section
- **Existing Project?** Reference: This document for navigation

---

## 📋 By Role

### For Developers

1. [AGENT-CONTEXT.md](AGENT-CONTEXT.md) - Essential context and quick reference
2. [ARCHITECTURE.md](ARCHITECTURE.md) - System design and components
3. [DEVELOPMENT.md](DEVELOPMENT.md) - Development workflows and standards
4. [jewelry_template/GUIDE.md](addons/tenant_templates/jewelry_template/GUIDE.md) - Template development patterns
5. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions

### For DevOps Engineers

1. [DEPLOYMENT.md](DEPLOYMENT.md) - Complete deployment guide
2. [ARCHITECTURE.md](ARCHITECTURE.md) - Infrastructure overview
3. [MULTI-TENANT-OPERATIONS.md](MULTI-TENANT-OPERATIONS.md) - Tenant management
4. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Deployment issues
5. [SECURITY.md](SECURITY.md) - Security configuration

### For Import Specialists

1. [jewelry_template/GUIDE.md](addons/tenant_templates/jewelry_template/GUIDE.md) - Complete import guide
2. [jewelry_template/import/CPL_WORKFLOW_SUMMARY.md](addons/tenant_templates/jewelry_template/import/CPL_WORKFLOW_SUMMARY.md) - CPL quick reference
3. [jewelry_template/import/CPL_VALIDATION_STATUS.md](addons/tenant_templates/jewelry_template/import/CPL_VALIDATION_STATUS.md) - Validation status
4. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Import troubleshooting

### For Business Stakeholders

1. [IMPLEMENTATION-SUMMARY.md](IMPLEMENTATION-SUMMARY.md) - Business overview and status
2. [JOIASMAX-QUICK-START.md](JOIASMAX-QUICK-START.md) - JoiasMax tenant guide
3. [JOIASMAX-IMPLEMENTATION-PLAN.md](JOIASMAX-IMPLEMENTATION-PLAN.md) - Project roadmap
4. [ARCHITECTURE.md](ARCHITECTURE.md) - High-level system overview

---

## 📚 Complete Documentation

### Core Platform Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [AGENT-CONTEXT.md](AGENT-CONTEXT.md) | Quick reference with critical context | All |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, components, integrations | Developers, DevOps |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Docker deployment, VPS setup, CI/CD | DevOps |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Development workflows, standards, testing | Developers |
| [MULTI-TENANT-OPERATIONS.md](MULTI-TENANT-OPERATIONS.md) | Tenant creation, management, isolation | DevOps, Developers |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues, diagnostics, solutions | All |
| [API.md](API.md) | API reference, webhooks, integrations | Developers |
| [SECURITY.md](SECURITY.md) | Security policies, compliance | DevOps, Security |

### Business Templates

| Template | Status | Documentation |
|----------|--------|---------------|
| Jewelry | ✅ Production | [jewelry_template/GUIDE.md](addons/tenant_templates/jewelry_template/GUIDE.md) |
| Retail | ⏳ Planned | Coming soon |
| Manufacturing | ⏳ Planned | Coming soon |
| Services | ⏳ Planned | Coming soon |

### Business-Specific Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [IMPLEMENTATION-SUMMARY.md](IMPLEMENTATION-SUMMARY.md) | Current status, business context | Stakeholders |
| [JOIASMAX-QUICK-START.md](JOIASMAX-QUICK-START.md) | JoiasMax tenant setup | JoiasMax team |
| [JOIASMAX-IMPLEMENTATION-PLAN.md](JOIASMAX-IMPLEMENTATION-PLAN.md) | Project roadmap, milestones | Stakeholders |

### Infrastructure Integration

| Document | Purpose | Location |
|----------|---------|----------|
| Core Infrastructure Guide | Essential VPS commands | `D:\Programacao\Repositorios\my-portfolio\CLAUDE.md` |
| File Structure Guide | VPS directory structure | `D:\Programacao\Repositorios\my-portfolio\FILE-STRUCTURE.md` |
| VPS Compatibility Notes | Deployment constraints | `D:\Programacao\Repositorios\my-portfolio\VPS-COMPATIBILITY-NOTES.md` |

---

## 🔍 By Task

### "I need to deploy Odoo locally"

1. [DEPLOYMENT.md](DEPLOYMENT.md) → Quick Start section
2. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) → Container Deployment Issues

### "I need to deploy to production VPS"

1. [DEPLOYMENT.md](DEPLOYMENT.md) → VPS Production Deployment section
2. Infrastructure guides (listed above under Infrastructure Integration)
3. [SECURITY.md](SECURITY.md) → Production security checklist

### "I need to create a new tenant"

1. [MULTI-TENANT-OPERATIONS.md](MULTI-TENANT-OPERATIONS.md) → Tenant creation workflow
2. [ARCHITECTURE.md](ARCHITECTURE.md) → Multi-tenant architecture section

### "I need to import CPL supplier products"

1. [jewelry_template/import/CPL_WORKFLOW_SUMMARY.md](addons/tenant_templates/jewelry_template/import/CPL_WORKFLOW_SUMMARY.md) - Quick start
2. [jewelry_template/GUIDE.md](addons/tenant_templates/jewelry_template/GUIDE.md) → CPL section for details

### "I need to add a new supplier (Gold Indice, Cronus, etc.)"

1. [jewelry_template/GUIDE.md](addons/tenant_templates/jewelry_template/GUIDE.md) → Reusable patterns section
2. [DEVELOPMENT.md](DEVELOPMENT.md) → Custom module development
3. [AGENT-CONTEXT.md](AGENT-CONTEXT.md) → Reusable patterns reference

### "I need to understand the database schema"

1. [ARCHITECTURE.md](ARCHITECTURE.md) → Database schema section
2. [jewelry_template/GUIDE.md](addons/tenant_templates/jewelry_template/GUIDE.md) → Database schema chapter

### "I need to troubleshoot import issues"

1. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) → Import-specific section
2. [jewelry_template/GUIDE.md](addons/tenant_templates/jewelry_template/GUIDE.md) → Troubleshooting chapter

### "I need to set up N8N automation"

1. [ARCHITECTURE.md](ARCHITECTURE.md) → N8N integration section
2. [API.md](API.md) → Webhook endpoints
3. [jewelry_template/GUIDE.md](addons/tenant_templates/jewelry_template/GUIDE.md) → API reference

### "I need to develop a new business template (retail, manufacturing)"

1. [jewelry_template/GUIDE.md](addons/tenant_templates/jewelry_template/GUIDE.md) → Template architecture patterns
2. [ARCHITECTURE.md](ARCHITECTURE.md) → Template architecture section
3. [DEVELOPMENT.md](DEVELOPMENT.md) → Custom module development

---

## 📦 Archived Documentation

Historical development artifacts moved to `addons/tenant_templates/jewelry_template/import/ARCHIVE/`:
- BUG_ANALYSIS_SKU_VARIANTS.md
- COST_COMPUTATION_ISSUE.md
- SKU_FIX_SUMMARY.md
- ADVANCED_FEATURES_ANALYSIS.md
- VARIANT_TEMPLATE_FIX.md
- LATEST_FIXES_SUMMARY.md
- DOCUMENTATION_UPDATE_SUMMARY.md

**Note**: These documents contain valuable lessons learned but are not needed for daily operations.

---

## 🔗 External References

### VPS Infrastructure (Required for Production)

1. [Core Infrastructure Guide](D:\Programacao\Repositorios\my-portfolio\CLAUDE.md)
2. [File Structure Guide](D:\Programacao\Repositorios\my-portfolio\FILE-STRUCTURE.md)
3. [VPS Compatibility Notes](D:\Programacao\Repositorios\my-portfolio\VPS-COMPATIBILITY-NOTES.md)
4. [Script Usage Guide](D:\Programacao\Repositorios\my-portfolio\SCRIPT-USAGE-GUIDE.md)
5. [Security Guidelines](D:\Programacao\Repositorios\my-portfolio\SECURITY.md)
6. [Monitoring Configuration](D:\Programacao\Repositorios\my-portfolio\MONITORING-SECURITY-README.md)

### Odoo Official Documentation

- [Odoo 18 Documentation](https://www.odoo.com/documentation/18.0/)
- [Odoo Developer Guide](https://www.odoo.com/documentation/18.0/developer.html)

---

**Last Updated**: 2026-01-12
**Maintained By**: Project team
**Questions?** Start with [AGENT-CONTEXT.md](AGENT-CONTEXT.md) or [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
