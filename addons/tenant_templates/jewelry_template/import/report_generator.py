# -*- coding: utf-8 -*-
"""
Report Generator for JoiasMax Product Import
Generates import reports (Markdown, CSV exports)
"""

import csv
import os
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class ImportReportGenerator:
    """Generate comprehensive import reports"""

    def __init__(self, stats, output_dir='reports'):
        """
        Initialize report generator

        Args:
            stats (dict): Import statistics
            output_dir (str): Output directory for reports
        """
        self.stats = stats
        self.output_dir = output_dir

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

    def generate_all_reports(self):
        """
        Generate all import reports

        Returns:
            dict: Paths to generated reports
        """
        reports = {}

        try:
            # Main markdown report
            reports['main_report'] = self.generate_markdown_report()

            # Missing weights CSV
            reports['missing_weights'] = self.generate_missing_weights_csv()

            # Missing indices CSV
            reports['missing_indices'] = self.generate_missing_indices_csv()

            # Errors CSV (if any)
            if self.stats.get('errors'):
                reports['errors'] = self.generate_errors_csv()

            _logger.info(f"Generated {len(reports)} reports")
            return reports

        except Exception as e:
            _logger.error(f"Error generating reports: {e}")
            raise

    def generate_markdown_report(self):
        """
        Generate main import summary report in Markdown format

        Returns:
            str: Path to generated report
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report_path = os.path.join(self.output_dir, 'import_report.md')

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# JoiasMax Product Import Report\n\n")
            f.write(f"**Generated**: {timestamp}\n\n")

            # Summary
            f.write("## Summary\n\n")
            f.write(f"- **Total products processed**: {self.stats.get('total_processed', 0)}\n")
            f.write(f"- **Successfully imported**: {self.stats.get('imported', 0)}\n")
            f.write(f"- **Skipped (errors)**: {self.stats.get('skipped', 0)}\n")
            f.write(f"- **Duplicates found**: {self.stats.get('duplicates', 0)}\n\n")

            # Breakdown by material
            f.write("## Breakdown by Material\n\n")
            material_stats = self.stats.get('by_material', {})
            for material, count in material_stats.items():
                f.write(f"- **{material.title()}**: {count} products\n")
            f.write("\n")

            # Pricing strategy
            f.write("## Pricing Strategy\n\n")
            f.write(f"- **Dynamic pricing** (weight found): {self.stats.get('with_weight', 0)} products\n")
            f.write(f"- **Manual pricing** (weight missing): {self.stats.get('without_weight', 0)} products\n\n")

            # Categories
            f.write("## Categories Created\n\n")
            category_stats = self.stats.get('by_category', {})
            for category, count in sorted(category_stats.items()):
                f.write(f"- **{category}**: {count} products\n")
            f.write("\n")

            # Products missing weight data
            f.write("## ⚠️ Products Missing Weight Data\n\n")
            missing_weights = self.stats.get('missing_weights', [])
            if missing_weights:
                f.write(f"**Exported to**: `{os.path.join(self.output_dir, 'missing_weights.csv')}`\n\n")
                f.write(f"**Total**: {len(missing_weights)} products\n\n")
                f.write("| SKU | Name | Category | Material | Current Price | Action |\n")
                f.write("|-----|------|----------|----------|---------------|--------|\n")
                for item in missing_weights[:10]:  # Show first 10
                    f.write(f"| {item.get('sku', '')} | {item.get('name', '')[:30]}... | ")
                    f.write(f"{item.get('category', '')} | {item.get('material', '')} | ")
                    f.write(f"R$ {item.get('price', 0):.2f} | Manual pricing used |\n")
                if len(missing_weights) > 10:
                    f.write(f"\n*...and {len(missing_weights) - 10} more (see CSV for full list)*\n")
            else:
                f.write("✅ All products have weight data!\n")
            f.write("\n")

            # Products missing provider indice
            f.write("## ⚠️ Products Missing Provider Indice\n\n")
            missing_indices = self.stats.get('missing_indices', [])
            if missing_indices:
                f.write(f"**Exported to**: `{os.path.join(self.output_dir, 'missing_indices.csv')}`\n\n")
                f.write(f"**Total**: {len(missing_indices)} products\n\n")
                f.write("**Note**: All products currently use temporary indices (1.10 for 18k, 1.0 default). ")
                f.write("User should provide real provider indices per product type.\n\n")
            else:
                f.write("✅ All products have provider indices!\n")
            f.write("\n")

            # Errors
            errors = self.stats.get('errors', [])
            if errors:
                f.write("## ❌ Errors Encountered\n\n")
                f.write(f"**Total**: {len(errors)} errors\n\n")
                f.write("| SKU | Error | Details |\n")
                f.write("|-----|-------|--------|\n")
                for error in errors[:20]:  # Show first 20
                    f.write(f"| {error.get('sku', 'UNKNOWN')} | {error.get('error_type', 'Error')} | ")
                    f.write(f"{error.get('details', '')} |\n")
                if len(errors) > 20:
                    f.write(f"\n*...and {len(errors) - 20} more errors*\n")
                f.write("\n")

            # Next steps
            f.write("## Next Steps\n\n")
            f.write("1. ✅ Review `missing_weights.csv` - Provide weights for products without weight data\n")
            f.write("2. ✅ Review `missing_indices.csv` - Provide real provider indices per product type\n")
            f.write("3. ✅ Update products via import script or Odoo UI\n")
            f.write("4. ✅ Verify pricing calculations: `(weight × 24k_price × indice) × markup`\n")
            f.write("5. ✅ Test N8N market price updates\n")
            f.write("6. ✅ Process remaining products from full export\n\n")

            # Import details
            f.write("## Import Details\n\n")
            f.write(f"- **Source CSV**: `{self.stats.get('source_csv', 'Unknown')}`\n")
            f.write(f"- **Target Database**: `{self.stats.get('database', 'Unknown')}`\n")
            f.write(f"- **Import Duration**: {self.stats.get('duration_seconds', 0):.1f} seconds\n")

        _logger.info(f"Generated markdown report: {report_path}")
        return report_path

    def generate_missing_weights_csv(self):
        """
        Generate CSV report for products missing weight data

        Returns:
            str: Path to generated CSV
        """
        report_path = os.path.join(self.output_dir, 'missing_weights.csv')
        missing_weights = self.stats.get('missing_weights', [])

        with open(report_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['SKU', 'Name', 'Category', 'Material', 'Current Price (R$)', 'Temp Indice', 'Action Required']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()

            for item in missing_weights:
                writer.writerow({
                    'SKU': item.get('sku', ''),
                    'Name': item.get('name', ''),
                    'Category': item.get('category', ''),
                    'Material': item.get('material', ''),
                    'Current Price (R$)': f"{item.get('price', 0):.2f}",
                    'Temp Indice': f"{item.get('indice', 1.0):.2f}",
                    'Action Required': 'Provide weight in grams'
                })

        _logger.info(f"Generated missing weights CSV: {report_path} ({len(missing_weights)} products)")
        return report_path

    def generate_missing_indices_csv(self):
        """
        Generate CSV report for products needing real provider indices

        Returns:
            str: Path to generated CSV
        """
        report_path = os.path.join(self.output_dir, 'missing_indices.csv')
        missing_indices = self.stats.get('missing_indices', [])

        with open(report_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['SKU', 'Name', 'Material', 'Temp Indice Used', 'Weight (g)', 'Note']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()

            for item in missing_indices:
                writer.writerow({
                    'SKU': item.get('sku', ''),
                    'Name': item.get('name', ''),
                    'Material': item.get('material', ''),
                    'Temp Indice Used': f"{item.get('indice', 1.0):.2f}",
                    'Weight (g)': f"{item.get('weight', 0):.3f}" if item.get('weight') else 'N/A',
                    'Note': 'User to provide real provider indice'
                })

        _logger.info(f"Generated missing indices CSV: {report_path} ({len(missing_indices)} products)")
        return report_path

    def generate_errors_csv(self):
        """
        Generate CSV report for import errors

        Returns:
            str: Path to generated CSV
        """
        report_path = os.path.join(self.output_dir, 'import_errors.csv')
        errors = self.stats.get('errors', [])

        with open(report_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['SKU', 'Product Name', 'Error Type', 'Details', 'Timestamp']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()

            for error in errors:
                writer.writerow({
                    'SKU': error.get('sku', 'UNKNOWN'),
                    'Product Name': error.get('name', ''),
                    'Error Type': error.get('error_type', 'Error'),
                    'Details': error.get('details', ''),
                    'Timestamp': error.get('timestamp', datetime.now().isoformat())
                })

        _logger.info(f"Generated errors CSV: {report_path} ({len(errors)} errors)")
        return report_path


# Test function
def _test_report_generator():
    """Test report generation with sample data"""

    # Sample statistics
    stats = {
        'total_processed': 150,
        'imported': 142,
        'skipped': 8,
        'duplicates': 2,
        'with_weight': 120,
        'without_weight': 22,
        'by_material': {
            'gold': 95,
            'silver': 35,
            'blend': 10,
            'other': 2,
        },
        'by_category': {
            'Alianças Ouro 18k': 45,
            'Brincos': 38,
            'Pingentes': 25,
            'Pulseiras': 20,
            'Anéis': 14,
        },
        'missing_weights': [
            {'sku': 'B191', 'name': 'Brinco Argola 9mm', 'category': 'Brincos',
             'material': 'Gold 18k', 'price': 1003.52, 'indice': 1.10},
            {'sku': 'P208', 'name': 'Pingente Coração', 'category': 'Pingentes',
             'material': 'Gold 18k', 'price': 811.08, 'indice': 1.10},
        ],
        'missing_indices': [
            {'sku': 'B191', 'name': 'Brinco Argola 9mm', 'material': 'Gold 18k',
             'indice': 1.10, 'weight': 1.5},
            {'sku': '2601', 'name': 'Aliança Prata', 'material': 'Silver 950',
             'indice': 1.0, 'weight': None},
        ],
        'errors': [
            {'sku': 'XXXX', 'name': 'Invalid Product', 'error_type': 'Material Detection Failed',
             'details': 'Could not detect material from HTML'},
        ],
        'source_csv': 'produtos_2026-01-05-08-46-50.csv',
        'database': 'tenant_joiasmax',
        'duration_seconds': 45.3,
    }

    print("=== Report Generation Test ===\n")

    generator = ImportReportGenerator(stats, output_dir='test_reports')
    reports = generator.generate_all_reports()

    print("Generated reports:")
    for report_type, path in reports.items():
        print(f"  - {report_type}: {path}")

    print(f"\nTotal reports: {len(reports)}")


if __name__ == '__main__':
    _test_report_generator()
