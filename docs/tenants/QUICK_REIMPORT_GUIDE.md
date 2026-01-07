# Quick Product Re-Import Guide

**Scenario:** You deleted sample products from inventory and need to reimport them from your Bling CSV export.

## ⚡ Quick Steps (5 Minutes)

### Step 1: Locate Your CSV File

**PowerShell (Windows):**
```powershell
# Find your Bling export file
# Common locations:
# - D:\Programacao\Repositorios\odoo\addons\tenant_templates\jewelry_template\import\
# - Your Downloads folder
# - Export/backup directory

# Search for it:
dir /s /b D:\Programacao\Repositorios\odoo\*.csv | findstr /i "bling produto"
```

**Bash (WSL/Linux):**
```bash
# Search for CSV files
find /mnt/d/Programacao/Repositorios/odoo -name "*.csv" -type f | grep -i "bling\|produto"

# Or if not using WSL:
find /path/to/odoo -name "*.csv" -type f | grep -i "bling\|produto"
```

### Step 2: Navigate to Import Directory

**PowerShell (Windows):**
```powershell
cd D:\Programacao\Repositorios\odoo\addons\tenant_templates\jewelry_template\import
```

**Bash (WSL/Linux):**
```bash
cd /mnt/d/Programacao/Repositorios/odoo/addons/tenant_templates/jewelry_template/import
# Or if not using WSL:
cd /path/to/odoo/addons/tenant_templates/jewelry_template/import
```

### Step 3: Run Import Command

**PowerShell (Windows):**
```powershell
# SIMPLEST COMMAND (uses defaults - recommended):
python import_products.py --csv "D:\path\to\produtos_bling.csv"

# OR with all parameters explicit (if you need different values):
python import_products.py --csv "D:\path\to\produtos_bling.csv" --url http://localhost:8069 --database tenant_joiasmax --username admin --password admin
```

**Bash (WSL/Linux):**
```bash
# SIMPLEST COMMAND (uses defaults - recommended):
python import_products.py --csv "/path/to/produtos_bling.csv"

# OR with all parameters explicit (multiline with backslashes):
python import_products.py \
  --csv "/path/to/produtos_bling.csv" \
  --url http://localhost:8069 \
  --database tenant_joiasmax \
  --username admin \
  --password admin
```

**Note:** Use `--database` (not `--db`). Default values: database=tenant_joiasmax, username=admin, password=admin, url=http://localhost:8069

**Expected output:**
```
2026-01-07 15:30:00 - INFO - Connected to Odoo successfully
2026-01-07 15:30:01 - INFO - Reading CSV file...
2026-01-07 15:30:02 - INFO - Found 28 products to import
2026-01-07 15:30:03 - INFO - Processing batch 1/1 (28 products)
2026-01-07 15:30:15 - INFO - Batch completed: 28 products imported
2026-01-07 15:30:16 - INFO - Creating product variants...
2026-01-07 15:30:20 - INFO - Created 12 variants for 1 product
2026-01-07 15:30:20 - INFO - Import completed successfully!
```

### Step 4: Verify Import

**PowerShell (Windows):**
```powershell
# Run validation (uses defaults)
python verify_import_results.py

# Check the validation report
type VALIDATION_SUMMARY.md
```

**Bash (WSL/Linux):**
```bash
# Run validation (uses defaults)
python verify_import_results.py

# Check the validation report
cat VALIDATION_SUMMARY.md
```

### Step 5: Check Products in Odoo UI

1. Open browser: `http://localhost:8069`
2. Login with admin credentials
3. Navigate to: **Products → Products**
4. Remove filters to see all products
5. Verify products are listed with correct:
   - Categories (Anéis, Pulseiras, Brincos, etc.)
   - Barcodes
   - Weights
   - Prices

---

## 🔧 If You Need to Start Fresh

### Delete All Products First

**PowerShell (Windows):**
```powershell
cd D:\Programacao\Repositorios\odoo\addons\tenant_templates\jewelry_template\import

# Uses defaults (database=tenant_joiasmax, username=admin, password=admin)
python delete_imported_products.py

# When prompted, type: yes
```

**Bash (WSL/Linux):**
```bash
cd /mnt/d/Programacao/Repositorios/odoo/addons/tenant_templates/jewelry_template/import

# Uses defaults (database=tenant_joiasmax, username=admin, password=admin)
python delete_imported_products.py

# When prompted, type: yes
```

**Then run the import again** (Step 3 above)

---

## 📋 Checklist

Before importing, verify:
- [ ] Odoo is running: `docker ps` (should show odoo_community_18)
- [ ] CSV file exists and is UTF-8 encoded
- [ ] You know your admin password
- [ ] Database name is correct: `tenant_joiasmax`
- [ ] Jewelry template module is installed

---

## 🆘 Quick Troubleshooting

### "Authentication failed"
```bash
# Test your credentials by logging into Odoo UI first
# http://localhost:8069
# If login works, use same username/password for import
```

### "CSV file not found"

**PowerShell (Windows):**
```powershell
# Use full absolute path with double quotes:
python import_products.py --csv "D:\Downloads\produtos_bling.csv"
```

**Bash (WSL/Linux):**
```bash
# Use full absolute path:
python import_products.py --csv "/mnt/d/Downloads/produtos_bling.csv"
```

### "Database not found"

**PowerShell (Windows):**
```powershell
# Check database name
docker exec -it odoo_postgres psql -U odoo -c "\l" | findstr tenant

# If different, use actual database name in --database parameter:
python import_products.py --csv "file.csv" --database your_database_name
```

**Bash (WSL/Linux):**
```bash
# Check database name
docker exec -it odoo_postgres psql -U odoo -c "\l" | grep tenant

# If different, use actual database name in --database parameter:
python import_products.py --csv "file.csv" --database your_database_name
```

### "Module not installed"
```bash
# Install jewelry template:
# Odoo UI → Apps → Remove "Apps" filter → Search "jewelry_template" → Install
```

---

## 📚 Full Documentation

For detailed information, see:
- [Complete Import Guide](../../addons/tenant_templates/jewelry_template/import/README.md)
- [Tenant Management](README.md)
- [Project Overview](../../CLAUDE.md)

---

**Last Updated**: 2026-01-07
