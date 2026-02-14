# -*- coding: utf-8 -*-
"""
JoiasMax Product Import Script
Main script for importing products from Bling CSV export to Odoo
"""

import argparse
import os
import csv
import logging
import sys
import time
import xmlrpc.client
from datetime import datetime

# Import helper modules
import html_parser
import category_mapper
import data_validator
from report_generator import ImportReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
_logger = logging.getLogger(__name__)


# ============================================================================
# Product Variant Detection Functions
# ============================================================================

def is_variant_sku(sku):
    """
    Check if SKU is a size variant (ends with size suffix)

    Examples:
        "C1010 20cm" → True
        "C1010 50cm" → True
        "44734 11" → True
        "C1010 C" → True (Customizado)
        "C1010" → False
        "B043" → False

    Args:
        sku (str): Product SKU

    Returns:
        bool: True if variant SKU
    """
    if not sku:
        return False

    import re
    # Pattern: ends with space + digits + optional 'cm' OR 'C'/'c' (custom)
    # Matches: "C1010 20cm", "C1010 50cm", "44734 11", "C1010 C", "PC0510 c"
    return re.search(r'\s+(\d+cm|\d+|[cC])$', sku.strip()) is not None


def get_base_sku(sku):
    """
    Extract base SKU by removing size suffix

    Examples:
        "C1010 20cm" → "C1010"
        "44734 11" → "44734"
        "C1010 C" → "C1010" (Customizado)
        "B043" → "B043"

    Args:
        sku (str): Variant or base SKU

    Returns:
        str: Base SKU without size suffix
    """
    if not sku:
        return ''

    import re
    # Remove size suffix (space + digits + optional 'cm' OR 'C'/'c')
    return re.sub(r'\s+(\d+cm|\d+|[cC])$', '', sku.strip()).strip()


def extract_size_value(sku):
    """
    Extract size from variant SKU

    Examples:
        "C1010 20cm" → "20cm"
        "C1010 50cm" → "50cm"
        "44734 11" → "11"
        "C1010 C" → "Customizado"
        "PC0510 c" → "Customizado"
        "B043" → None

    Args:
        sku (str): Variant SKU

    Returns:
        str or None: Size value, or None if not a variant
    """
    if not sku:
        return None

    import re
    match = re.search(r'\s+(\d+cm|\d+|[cC])$', sku.strip())
    if not match:
        return None

    size = match.group(1)
    # Normalize custom flags to "Customizado"
    if size.lower() == 'c':
        return 'Customizado'
    return size


def detect_attribute_type(size_values):
    """
    Determine attribute type based on size values

    Rules:
        - If any size ends with 'cm' → "Comprimento" (Length)
        - Otherwise → "Tamanho" (Size/Number)

    Examples:
        ["20cm", "50cm", "60cm"] → "Comprimento"
        ["11", "12", "13"] → "Tamanho"

    Args:
        size_values (list): List of size values

    Returns:
        str: "Comprimento" or "Tamanho"
    """
    # Check if any size value ends with 'cm'
    for size in size_values:
        if size and str(size).endswith('cm'):
            return 'Comprimento'

    # Default to size/number
    return 'Tamanho'


def get_parent_product_info(row, all_csv_products):
    """
    Lookup parent product info using Código Pai field

    This function retrieves the parent product's full information from the CSV data,
    allowing variant products to inherit the complete product name and HTML description
    from their parent instead of using incomplete variant-specific descriptions.

    Args:
        row (dict): Current product row from CSV
        all_csv_products (list): All products from CSV for lookup

    Returns:
        dict or None: Parent product info {'name': str, 'html_desc': str, 'code': str}
                      or None if no parent found
    """
    # Get parent code from CSV (clean tabs)
    parent_code = row.get('Código Pai', '').strip().replace('\t', '').strip()

    if not parent_code:
        return None

    # Find parent in CSV data
    for product in all_csv_products:
        if product.get('Código', '').strip() == parent_code:
            return {
                'name': product.get('Descrição', ''),
                'html_desc': product.get('Descrição Curta', ''),
                'code': parent_code
            }

    return None


class OdooProductImporter:
    """Import products from Bling CSV to Odoo via XML-RPC"""

    def __init__(self, url, database, username, password, skip_updates=False):
        """
        Initialize Odoo connection

        Args:
            url (str): Odoo server URL (e.g., 'http://localhost:8069')
            database (str): Database name
            username (str): Odoo username
            password (str): Odoo password
            skip_updates (bool): If True, skip updating existing products (only create new ones)
        """
        self.url = url
        self.database = database
        self.username = username
        self.password = password
        self.skip_updates = skip_updates

        # XML-RPC endpoints
        self.common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

        # Authenticate
        try:
            self.uid = self.common.authenticate(database, username, password, {})
            if not self.uid:
                raise Exception("Authentication failed")
            _logger.info(f"✓ Connected to Odoo as user ID: {self.uid}")
        except Exception as e:
            _logger.error(f"✗ Failed to connect to Odoo: {e}")
            raise

        # Category cache
        self.category_cache = {}

        # Product variant tracking
        # Format: {base_sku: [{'size': '20cm', 'barcode': '...', 'weight': 0.1, 'price': 100.0}, ...]}
        self.variant_data = {}
        self.base_products = {}  # Track which products are bases for variants

        # CSV data storage for parent product lookups
        self.all_csv_products = []

        # Statistics
        self.stats = {
            'total_processed': 0,
            'imported': 0,
            'skipped': 0,
            'duplicates': 0,
            'with_weight': 0,
            'without_weight': 0,
            'by_material': {},
            'by_category': {},
            'missing_weights': [],
            'missing_indices': [],
            'errors': [],
        }

    def execute(self, model, method, *args):
        """
        Execute XML-RPC call to Odoo

        Args:
            model (str): Odoo model name
            method (str): Method to call
            *args: Arguments for the method

        Returns:
            Result from Odoo
        """
        try:
            return self.models.execute_kw(
                self.database, self.uid, self.password,
                model, method, args
            )
        except Exception as e:
            _logger.error(f"XML-RPC error: {model}.{method} - {e}")
            raise

    def sanitize_external_id(self, sku):
        """
        Sanitize SKU for use in External ID names.
        External IDs cannot contain spaces or special characters.

        Args:
            sku (str): Product SKU (may contain spaces or special chars)

        Returns:
            str: Sanitized SKU safe for External ID usage
        """
        # Replace spaces and other problematic characters with underscores
        return sku.replace(" ", "_").replace("/", "_").replace("\\", "_")

    def get_or_create_external_id(self, model, res_id, name):
        """
        Create or update External ID for a record.
        External IDs enable Odoo-standard import/export workflows.

        Args:
            model (str): Odoo model name (e.g., 'product.template')
            res_id (int): Record ID
            name (str): External ID name (e.g., 'product_template_C1010')

        Returns:
            int: External ID record ID
        """
        # Check if External ID already exists
        ext_id_search = self.execute('ir.model.data', 'search', [
            ('module', '=', 'jewelry_import'),
            ('name', '=', name),
            ('model', '=', model),
        ])

        if ext_id_search:
            # Update existing External ID (in case res_id changed)
            self.execute('ir.model.data', 'write', [ext_id_search[0]], {
                'res_id': res_id,
            })
            return ext_id_search[0]
        else:
            # Create new External ID
            return self.execute('ir.model.data', 'create', {
                'name': name,
                'module': 'jewelry_import',
                'model': model,
                'res_id': res_id,
            })

    def find_by_external_id(self, model, name):
        """
        Find record by External ID.

        Args:
            model (str): Odoo model name
            name (str): External ID name

        Returns:
            int or False: Record ID if found, False otherwise
        """
        ext_id_search = self.execute('ir.model.data', 'search', [
            ('module', '=', 'jewelry_import'),
            ('name', '=', name),
            ('model', '=', model),
        ])

        if ext_id_search:
            ext_id_data = self.execute('ir.model.data', 'read', [ext_id_search[0]], ['res_id'])
            if ext_id_data and len(ext_id_data) > 0:
                return ext_id_data[0]['res_id']

        return False

    def read_csv(self, csv_path):
        """
        Read products from Bling CSV export

        Args:
            csv_path (str): Path to CSV file

        Returns:
            list: List of product dictionaries
        """
        products = []

        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')

                for row in reader:
                    # Clean values (remove BOM, strip whitespace)
                    clean_row = {
                        k: v.strip() if isinstance(v, str) else v
                        for k, v in row.items()
                    }
                    products.append(clean_row)

            _logger.info(f"✓ Read {len(products)} products from CSV")
            return products

        except Exception as e:
            _logger.error(f"✗ Failed to read CSV: {e}")
            raise

    def create_category_hierarchy(self):
        """
        Create Odoo product categories based on category hierarchy

        Returns:
            dict: Mapping of category names to Odoo category IDs
        """
        _logger.info("Creating category hierarchy...")

        categories = {}

        # Get categories in creation order (parents first)
        ordered_categories = category_mapper.get_all_categories_ordered()

        for cat_name, parent_name in ordered_categories:
            try:
                # Check if category already exists
                existing = self.execute('product.category', 'search', [
                    ('name', '=', cat_name)
                ])

                if existing:
                    categories[cat_name] = existing[0]
                    _logger.debug(f"  Category exists: {cat_name} (ID: {existing[0]})")
                else:
                    # Create category
                    parent_id = categories.get(parent_name) if parent_name else False

                    cat_id = self.execute('product.category', 'create', {
                        'name': cat_name,
                        'parent_id': parent_id,
                    })

                    categories[cat_name] = cat_id
                    _logger.info(f"  ✓ Created category: {cat_name} (ID: {cat_id})")

            except Exception as e:
                _logger.error(f"  ✗ Failed to create category {cat_name}: {e}")
                # Use default category
                if 'Joias' in categories:
                    categories[cat_name] = categories['Joias']

        self.category_cache = categories
        _logger.info(f"✓ Category hierarchy ready ({len(categories)} categories)")

        return categories

    def get_or_create_category(self, bling_category, product_name=None):
        """
        Get Odoo category ID for Bling category, creating if necessary

        Args:
            bling_category (str): Category name from Bling
            product_name (str, optional): Product name for fallback analysis

        Returns:
            int: Odoo category ID
        """
        # Clean category name (with product name fallback if CSV category empty)
        odoo_category = category_mapper.clean_category_name(bling_category, product_name)

        # Check cache
        if odoo_category in self.category_cache:
            return self.category_cache[odoo_category]

        # Try to find in Odoo
        try:
            existing = self.execute('product.category', 'search', [
                ('name', '=', odoo_category)
            ])

            if existing:
                cat_id = existing[0]
                self.category_cache[odoo_category] = cat_id
                return cat_id

        except Exception as e:
            _logger.warning(f"Error searching for category {odoo_category}: {e}")

        # Fallback to default category
        if 'Joias' in self.category_cache:
            return self.category_cache['Joias']

        # Last resort: create default category
        try:
            cat_id = self.execute('product.category', 'create', {
                'name': 'Joias'
            })
            self.category_cache['Joias'] = cat_id
            return cat_id
        except Exception as e:
            _logger.error(f"Failed to create default category: {e}")
            return False

    def process_product(self, row):
        """
        Process single product from CSV row

        Args:
            row (dict): CSV row data

        Returns:
            bool: True if imported successfully
        """
        sku = row.get('Código', '').strip()
        product_name = row.get('Descrição', '')

        try:
            self.stats['total_processed'] += 1

            # Check if this is a variant SKU
            if is_variant_sku(sku):
                # This is a variant - store for later processing
                base_sku = get_base_sku(sku)
                size_value = extract_size_value(sku)

                _logger.info(f"  {sku}: Detected as variant of {base_sku} (size: {size_value})")

                # Get parent product info for complete name and HTML description
                parent_info = get_parent_product_info(row, self.all_csv_products)

                if parent_info:
                    # Use parent's full name and HTML description
                    variant_name = parent_info['name']
                    html_desc = parent_info['html_desc']
                    _logger.info(f"    Using parent name: {variant_name[:50]}...")
                else:
                    # Fallback if parent not found
                    variant_name = product_name
                    html_desc = row.get('Descrição Curta', '')
                    _logger.warning(f"    Parent {base_sku} not found, using row name")

                # Extract barcode from CSV (clean tabs)
                barcode = row.get('GTIN/EAN', '').strip().replace('\t', '').strip()

                # Extract logistics weight from CSV (in Kg)
                logistics_weight_kg = row.get('Peso líquido (Kg)', '0').strip().replace('\t', '')
                try:
                    logistics_weight = float(logistics_weight_kg.replace(',', '.')) if logistics_weight_kg and logistics_weight_kg != '0' else 0.0
                except (ValueError, AttributeError):
                    logistics_weight = 0.0

                # Parse price
                try:
                    price_str = row.get('Preço', '0').strip().replace('\t', '')
                    # Brazilian format: remove thousand separators, replace comma with dot
                    price_str = price_str.replace('.', '').replace(',', '.')
                    price = float(price_str) if price_str and price_str != '0' else 0.0
                except (ValueError, AttributeError):
                    price = 0.0

                # Store variant data with parent name
                if base_sku not in self.variant_data:
                    self.variant_data[base_sku] = []

                self.variant_data[base_sku].append({
                    'size': size_value,
                    'barcode': barcode if barcode else None,
                    'weight': logistics_weight,
                    'price': price,
                    'sku': sku,  # Full variant SKU for reference
                    'parent_name': variant_name,  # Store parent's full name
                    'html_desc': html_desc,  # Store parent's HTML for weight extraction
                })

                _logger.info(f"    Stored variant data for later processing")
                return True  # Variant stored successfully

            # Not a variant - process as regular product

            # Parse HTML description
            html_desc = row.get('Descrição Curta', '')
            parsed_html = html_parser.parse_html_description(html_desc)

            # Extract data from HTML
            weight_grams = parsed_html.get('weight_grams')
            material_info = parsed_html.get('material_info', {})
            material_type = material_info.get('material_type')
            metal_purity = material_info.get('metal_purity')
            temp_indice = material_info.get('temp_indice', 1.0)
            production_days = parsed_html.get('production_days')  # Customer Lead Time

            # Extract barcode from CSV (clean tabs and whitespace)
            barcode = row.get('GTIN/EAN', '').strip().replace('\t', '').strip()

            # Extract logistics weight from CSV (in Kg)
            logistics_weight_kg = row.get('Peso líquido (Kg)', '0').strip().replace('\t', '')
            try:
                logistics_weight = float(logistics_weight_kg.replace(',', '.')) if logistics_weight_kg and logistics_weight_kg != '0' else 0.0
            except (ValueError, AttributeError):
                logistics_weight = 0.0

            # Extract dimensions from CSV for volume calculation (clean 'None' strings and tabs)
            width_str = row.get('Largura do Produto (cm)', '0').strip().replace('\t', '')
            height_str = row.get('Altura do Produto (cm)', '0').strip().replace('\t', '')
            depth_str = row.get('Profundidade do Produto (cm)', '0').strip().replace('\t', '')

            # Handle 'None' string from CSV
            if width_str == 'None': width_str = '0'
            if height_str == 'None': height_str = '0'
            if depth_str == 'None': depth_str = '0'

            # Calculate volume in m³ (W × H × D in cm → m³)
            try:
                width = float(width_str.replace(',', '.')) if width_str and width_str != '0' else 0.0
                height = float(height_str.replace(',', '.')) if height_str and height_str != '0' else 0.0
                depth = float(depth_str.replace(',', '.')) if depth_str and depth_str != '0' else 0.0
                # Convert cm³ to m³: (cm³ / 1,000,000)
                volume = (width * height * depth) / 1000000.0 if (width and height and depth) else 0.0
            except (ValueError, AttributeError):
                volume = 0.0

            # Debug logging for first product
            if sku == 'C790RZ':
                _logger.info(f"  [DEBUG] C790RZ extraction:")
                _logger.info(f"    barcode: '{barcode}' (len={len(barcode) if barcode else 0})")
                _logger.info(f"    logistics_weight: {logistics_weight} kg")
                _logger.info(f"    dimensions: W={width}, H={height}, D={depth}")
                _logger.info(f"    volume: {volume} m3")

            # Build product data
            product_data = {
                'default_code': sku,
                'name': row.get('Descrição', ''),
                'list_price': row.get('Preço', '0'),
                'description': html_desc,
                'description_sale': html_desc,  # Use HTML description for e-commerce
                'barcode': barcode if barcode else None,
                'weight': logistics_weight,  # Odoo standard weight field (Kg)
                'volume': volume,  # Odoo standard volume field (m³)
                'sale_delay': production_days if production_days else 0,  # Customer Lead Time (days)
                'is_jewelry': (material_type in ['gold', 'silver']),
                'material_type': material_type,
                'metal_purity': metal_purity,
                'metal_weight_grams': weight_grams,
                'provider_indice': temp_indice,
            }

            # Get category (pass product_name for fallback if CSV category empty)
            bling_category = row.get('Categoria do produto', '')
            categ_id = self.get_or_create_category(bling_category, product_name)
            if categ_id:
                product_data['categ_id'] = categ_id

            # Validate data
            is_valid, cleaned_data, errors = data_validator.validate_product_data(product_data)

            if not is_valid:
                _logger.error(f"✗ {sku}: Validation failed - {', '.join(errors)}")
                self.stats['skipped'] += 1
                self.stats['errors'].append({
                    'sku': sku,
                    'name': product_data.get('name', ''),
                    'error_type': 'Validation Failed',
                    'details': ', '.join(errors)
                })
                return False

            # Check for duplicates using External ID first, then SKU fallback
            ext_id_name = f'product_template_{self.sanitize_external_id(sku)}'
            existing_id = self.find_by_external_id('product.template', ext_id_name)

            if existing_id:
                if self.skip_updates:
                    # Skip updating existing products (debugging mode)
                    _logger.info(f"  {sku}: Found by External ID, skipping (--skip-updates enabled)")
                    self.stats['duplicates'] += 1
                    return False
                else:
                    # Found by External ID - update with CSV data (CSV always wins)
                    _logger.info(f"  {sku}: Found by External ID, updating")
                    self.update_product(existing_id, cleaned_data)
                    self.stats['duplicates'] += 1
                    return False

            # Fallback: Search by default_code for products without External ID
            existing = self.execute('product.template', 'search', [
                ('default_code', '=', sku)
            ])

            if existing:
                if self.skip_updates:
                    # Skip updating existing products (debugging mode)
                    _logger.info(f"  {sku}: Found by SKU, skipping (--skip-updates enabled)")
                    self.stats['duplicates'] += 1
                    return False
                else:
                    # Found by SKU - register External ID and update
                    _logger.info(f"  {sku}: Found by SKU, registering External ID and updating")
                    self.get_or_create_external_id('product.template', existing[0], ext_id_name)
                    self.update_product(existing[0], cleaned_data)
                    self.stats['duplicates'] += 1
                    return False

            # Create new product
            product_id = self.create_product(cleaned_data)

            if product_id:
                _logger.info(f"✓ {sku}: Imported successfully (ID: {product_id})")
                self.stats['imported'] += 1

                # Update statistics
                if material_type:
                    self.stats['by_material'][material_type] = \
                        self.stats['by_material'].get(material_type, 0) + 1

                odoo_cat = category_mapper.clean_category_name(bling_category, product_name)
                self.stats['by_category'][odoo_cat] = \
                    self.stats['by_category'].get(odoo_cat, 0) + 1

                if weight_grams:
                    self.stats['with_weight'] += 1
                else:
                    self.stats['without_weight'] += 1

                # Track missing data
                if not weight_grams and cleaned_data.get('is_jewelry'):
                    self.stats['missing_weights'].append({
                        'sku': sku,
                        'name': cleaned_data.get('name', ''),
                        'category': odoo_cat,
                        'material': f"{material_type or 'Unknown'} {material_info.get('material_text', '')}",
                        'price': cleaned_data.get('list_price', 0),
                        'indice': temp_indice,
                    })

                # All products need real indices
                self.stats['missing_indices'].append({
                    'sku': sku,
                    'name': cleaned_data.get('name', ''),
                    'material': f"{material_type or 'Unknown'}",
                    'indice': temp_indice,
                    'weight': weight_grams,
                })

                return True
            else:
                self.stats['skipped'] += 1
                return False

        except Exception as e:
            _logger.error(f"✗ {sku}: Import failed - {e}")
            self.stats['skipped'] += 1
            self.stats['errors'].append({
                'sku': sku,
                'name': row.get('Descrição', ''),
                'error_type': 'Import Exception',
                'details': str(e)
            })
            return False

    def create_product(self, product_data):
        """
        Create product in Odoo and jewelry pricing if applicable

        Args:
            product_data (dict): Validated product data

        Returns:
            int or False: Product ID if successful
        """
        try:
            # Create product.template
            product_vals = {
                'name': product_data['name'],
                'default_code': product_data['default_code'],
                'list_price': product_data['list_price'],
                'description': product_data.get('description', ''),
                'description_sale': product_data.get('description_sale', ''),
                # Note: Omit 'type' field - Odoo will use default value
            }

            # Add barcode if available
            if product_data.get('barcode'):
                product_vals['barcode'] = product_data['barcode']
                if product_data['default_code'] == 'C790RZ':
                    _logger.info(f"  [DEBUG] C790RZ: Adding barcode to product_vals: '{product_data['barcode']}'")

            # Add logistics fields (weight and volume)
            if product_data.get('weight'):
                product_vals['weight'] = product_data['weight']
                if product_data['default_code'] == 'C790RZ':
                    _logger.info(f"  [DEBUG] C790RZ: Adding weight to product_vals: {product_data['weight']} kg")
            if product_data.get('volume'):
                product_vals['volume'] = product_data['volume']
                if product_data['default_code'] == 'C790RZ':
                    _logger.info(f"  [DEBUG] C790RZ: Adding volume to product_vals: {product_data['volume']} m3")

            # Add Customer Lead Time (sale_delay)
            if product_data.get('sale_delay'):
                product_vals['sale_delay'] = product_data['sale_delay']

            if product_data.get('categ_id'):
                product_vals['categ_id'] = product_data['categ_id']

            # Add jewelry fields if applicable
            if product_data.get('is_jewelry'):
                product_vals['is_jewelry'] = True
                product_vals['material_type'] = product_data['material_type']
                product_vals['metal_purity'] = product_data['metal_purity']
                if product_data.get('metal_weight_grams'):
                    product_vals['metal_weight_grams'] = product_data['metal_weight_grams']

            product_id = self.execute('product.template', 'create', product_vals)

            # Register External ID for the new product
            if product_id:
                ext_id_name = f'product_template_{self.sanitize_external_id(product_data["default_code"])}'
                self.get_or_create_external_id('product.template', product_id, ext_id_name)
                _logger.debug(f"    Registered External ID: {ext_id_name}")

            # Create jewelry pricing record if jewelry
            if product_data.get('is_jewelry') and product_id:
                pricing_vals = {
                    'product_id': product_id,
                    'provider_indice': product_data.get('provider_indice', 1.0),
                    'markup_percentage': product_data.get('markup_percentage', 200.0),
                }

                # If no weight, use manual override
                if not product_data.get('metal_weight_grams'):
                    pricing_vals['use_manual_override'] = True
                    pricing_vals['manual_override_price_brl'] = product_data['list_price']

                # Create pricing record and capture ID
                pricing_id = self.execute('joiasmax.jewelry.pricing', 'create', pricing_vals)

                # Link pricing record back to product
                if pricing_id:
                    self.execute('product.template', 'write', [product_id], {
                        'jewelry_pricing_id': pricing_id
                    })
                    _logger.debug(f"  ✓ Linked pricing record {pricing_id} to product {product_id}")

            return product_id

        except Exception as e:
            _logger.error(f"Failed to create product {product_data.get('default_code')}: {e}")
            return False

    def update_product(self, product_id, product_data):
        """
        Update existing product in Odoo with CSV data (CSV always wins).

        Args:
            product_id (int): Existing product ID
            product_data (dict): Validated product data from CSV

        Returns:
            bool: True if successful
        """
        try:
            # Build update values (CSV data takes precedence)
            update_vals = {}

            # Update core fields
            if product_data.get('name'):
                update_vals['name'] = product_data['name']
            if product_data.get('list_price') is not None:
                update_vals['list_price'] = product_data['list_price']
            if product_data.get('description'):
                update_vals['description'] = product_data['description']
            if product_data.get('description_sale'):
                update_vals['description_sale'] = product_data['description_sale']

            # Update barcode
            if product_data.get('barcode'):
                update_vals['barcode'] = product_data['barcode']

            # Update logistics fields
            if product_data.get('weight'):
                update_vals['weight'] = product_data['weight']
            if product_data.get('volume'):
                update_vals['volume'] = product_data['volume']
            if product_data.get('sale_delay'):
                update_vals['sale_delay'] = product_data['sale_delay']

            # Update category
            if product_data.get('categ_id'):
                update_vals['categ_id'] = product_data['categ_id']

            # Update jewelry fields
            if product_data.get('is_jewelry'):
                update_vals['is_jewelry'] = True
                if product_data.get('material_type'):
                    update_vals['material_type'] = product_data['material_type']
                if product_data.get('metal_purity'):
                    update_vals['metal_purity'] = product_data['metal_purity']
                if product_data.get('metal_weight_grams'):
                    update_vals['metal_weight_grams'] = product_data['metal_weight_grams']

            # Execute update
            if update_vals:
                self.execute('product.template', 'write', [product_id], update_vals)
                _logger.debug(f"    Updated product with {len(update_vals)} fields from CSV")

            # Update jewelry pricing if applicable
            if product_data.get('is_jewelry'):
                # Check if pricing record exists
                product_read = self.execute('product.template', 'read', [product_id], ['jewelry_pricing_id'])

                if product_read and product_read[0].get('jewelry_pricing_id'):
                    pricing_id = product_read[0]['jewelry_pricing_id'][0]
                    pricing_update = {}

                    if product_data.get('provider_indice'):
                        pricing_update['provider_indice'] = product_data['provider_indice']
                    if product_data.get('markup_percentage'):
                        pricing_update['markup_percentage'] = product_data['markup_percentage']

                    if not product_data.get('metal_weight_grams'):
                        pricing_update['use_manual_override'] = True
                        pricing_update['manual_override_price_brl'] = product_data['list_price']

                    if pricing_update:
                        self.execute('joiasmax.jewelry.pricing', 'write', [pricing_id], pricing_update)

            return True

        except Exception as e:
            _logger.error(f"Failed to update product {product_data.get('default_code')}: {e}")
            return False

    def update_existing_variant(self, variant_product_id, variant_dict):
        """
        Update existing product variant with latest CSV data.
        CSV data always takes precedence over database values.

        Args:
            variant_product_id (int): Existing product.product ID
            variant_dict (dict): Variant data from CSV with keys:
                - sku: Full variant SKU
                - barcode: Product barcode
                - weight: Product weight
                - price: Product price
                - html_desc: HTML description

        Returns:
            bool: True if successful
        """
        try:
            update_vals = {}

            # SKU (CSV always wins)
            if variant_dict.get('sku'):
                update_vals['default_code'] = variant_dict['sku']

            # Barcode (CSV always wins - overwrite even if different)
            if variant_dict.get('barcode'):
                update_vals['barcode'] = variant_dict['barcode']

            # Weight (CSV always wins)
            if variant_dict.get('weight'):
                update_vals['weight'] = variant_dict['weight']

            # Price (CSV always wins)
            if variant_dict.get('price'):
                update_vals['list_price'] = variant_dict['price']

            # Description (CSV always wins)
            if variant_dict.get('html_desc'):
                update_vals['description_sale'] = variant_dict['html_desc']

            if update_vals:
                self.execute('product.product', 'write', [variant_product_id], update_vals)
                _logger.debug(f"      Updated variant {variant_dict.get('size', '')} with {len(update_vals)} fields from CSV")
                return True

            return False

        except Exception as e:
            _logger.error(f"      Failed to update variant {variant_dict.get('sku', '')}: {e}")
            return False

    def get_or_create_attribute(self, attr_name):
        """
        Get or create product attribute (Comprimento or Tamanho)

        Args:
            attr_name (str): "Comprimento" or "Tamanho"

        Returns:
            int: Attribute ID
        """
        try:
            # Search for existing attribute
            existing = self.execute('product.attribute', 'search', [
                ('name', '=', attr_name)
            ])

            if existing:
                return existing[0]

            # Create new attribute
            attr_vals = {
                'name': attr_name,
                'create_variant': 'always',  # Always create variants
                'display_type': 'radio',  # Display as radio buttons
            }

            attr_id = self.execute('product.attribute', 'create', attr_vals)
            _logger.info(f"  ✓ Created attribute: {attr_name} (ID: {attr_id})")
            return attr_id

        except Exception as e:
            _logger.error(f"Failed to create attribute {attr_name}: {e}")
            return False

    def get_or_create_attribute_value(self, attr_id, value_name):
        """
        Get or create product attribute value

        Args:
            attr_id (int): Attribute ID
            value_name (str): Value name (e.g., "20cm", "11")

        Returns:
            int: Attribute value ID
        """
        try:
            # Search for existing value
            existing = self.execute('product.attribute.value', 'search', [
                ('attribute_id', '=', attr_id),
                ('name', '=', value_name)
            ])

            if existing:
                return existing[0]

            # Create new value
            value_vals = {
                'name': value_name,
                'attribute_id': attr_id,
            }

            value_id = self.execute('product.attribute.value', 'create', value_vals)
            _logger.debug(f"    Created value: {value_name} (ID: {value_id})")
            return value_id

        except Exception as e:
            _logger.error(f"Failed to create attribute value {value_name}: {e}")
            return False

    def create_product_variants(self):
        """
        Create product variants for all products with multiple sizes

        This method:
        1. Groups variant data by base SKU
        2. Creates Odoo product attributes (Comprimento/Tamanho)
        3. Links attributes to parent product templates
        4. Odoo auto-generates product.product variants
        5. Updates variant-specific data (barcode, weight, price)

        Returns:
            int: Number of variant groups created
        """
        if not self.variant_data:
            _logger.info("No product variants to create")
            return 0

        _logger.info(f"\nCreating product variants for {len(self.variant_data)} base products...")

        created_count = 0

        for base_sku, variants in self.variant_data.items():
            try:
                # Find base product template using External ID first (same logic as process_product)
                ext_id_name = f'product_template_{self.sanitize_external_id(base_sku)}'
                template_id = self.find_by_external_id('product.template', ext_id_name)

                if not template_id:
                    # Fallback: Search by default_code
                    template_ids = self.execute('product.template', 'search', [
                        ('default_code', '=', base_sku)
                    ])

                    if not template_ids:
                        _logger.warning(f"  Base product not found: {base_sku}, skipping variants")
                        continue

                    template_id = template_ids[0]
                    # Register External ID for future imports
                    self.get_or_create_external_id('product.template', template_id, ext_id_name)
                    _logger.debug(f"    Registered External ID for template: {ext_id_name}")

                # Determine attribute type
                size_values = [v['size'] for v in variants]
                attr_type = detect_attribute_type(size_values)

                # Check which variants already exist
                existing_variants = []
                missing_variants = []
                updated_count = 0

                for variant in variants:
                    variant_sku = variant['sku']
                    variant_ext_id = f'product_variant_{self.sanitize_external_id(variant_sku)}'

                    # Check if variant exists by External ID
                    existing_variant_id = self.find_by_external_id('product.product', variant_ext_id)

                    if existing_variant_id:
                        # Verify this variant belongs to THIS template, not another duplicate
                        variant_data = self.execute('product.product', 'read', [existing_variant_id], ['product_tmpl_id'])
                        if variant_data and variant_data[0]['product_tmpl_id'][0] == template_id:
                            # Variant belongs to this template
                            existing_variants.append(variant_sku)
                            if not self.skip_updates:
                                # Update existing variant (CSV always wins)
                                self.update_existing_variant(existing_variant_id, variant)
                                updated_count += 1
                        else:
                            # Variant belongs to different template - create new one for this template
                            _logger.debug(f"      Variant {variant_sku} exists but belongs to different template, creating new")
                            missing_variants.append(variant)
                    else:
                        # Check by SKU as fallback
                        existing = self.execute('product.product', 'search', [
                            ('default_code', '=', variant_sku)
                        ])

                        if existing:
                            # Verify this variant belongs to THIS template
                            variant_data = self.execute('product.product', 'read', [existing[0]], ['product_tmpl_id'])
                            if variant_data and variant_data[0]['product_tmpl_id'][0] == template_id:
                                # Variant belongs to this template
                                existing_variants.append(variant_sku)
                                if not self.skip_updates:
                                    # Register External ID for existing variant
                                    self.get_or_create_external_id('product.product', existing[0], variant_ext_id)
                                    # Update variant
                                    self.update_existing_variant(existing[0], variant)
                                    updated_count += 1
                            else:
                                # Variant belongs to different template - create new one for this template
                                _logger.debug(f"      Variant {variant_sku} exists but belongs to different template, creating new")
                                missing_variants.append(variant)
                        else:
                            # Variant needs to be created
                            missing_variants.append(variant)

                if self.skip_updates:
                    _logger.info(f"  {base_sku}: {len(existing_variants)} variants exist (skipped), {len(missing_variants)} need creation")
                else:
                    _logger.info(f"  {base_sku}: {len(existing_variants)} variants exist (updating), {len(missing_variants)} need creation")

                # If all variants exist, skip creation
                if len(missing_variants) == 0:
                    if self.skip_updates:
                        _logger.info(f"    ✓ Skipped {len(existing_variants)} existing variants (--skip-updates enabled)")
                    else:
                        _logger.info(f"    ✓ Updated {updated_count} existing variants")
                    created_count += 1
                    continue

                # Create missing variants by linking attributes
                _logger.info(f"    Creating {len(missing_variants)} missing variants...")

                # Get or create attribute
                attr_id = self.get_or_create_attribute(attr_type)
                if not attr_id:
                    continue

                # Create attribute values for missing variants
                value_ids = []
                for variant in missing_variants:
                    value_id = self.get_or_create_attribute_value(attr_id, variant['size'])
                    if value_id:
                        value_ids.append(value_id)

                if not value_ids:
                    _logger.warning(f"    No attribute values created for {base_sku}")
                    continue

                # Link attribute to template (auto-creates variants!)
                self.execute('product.template', 'write', [template_id], {
                    'attribute_line_ids': [(0, 0, {
                        'attribute_id': attr_id,
                        'value_ids': [(6, 0, value_ids)],
                    })]
                })

                _logger.info(f"    ✓ Linked {len(value_ids)} attribute values to template")

                # Wait for Odoo to auto-generate variants
                # Read template to get generated variant IDs
                template_data = self.execute('product.template', 'read', [template_id], ['product_variant_ids'])

                if template_data and len(template_data) > 0 and template_data[0].get('product_variant_ids'):
                    variant_product_ids = template_data[0]['product_variant_ids']

                    # Update newly created variant-specific data (barcode, weight, price, SKU)
                    # Only process the missing_variants that were just created
                    for variant_product_id in variant_product_ids:
                        # Read variant to get attribute value
                        variant_data_read = self.execute('product.product', 'read', [variant_product_id], ['product_template_attribute_value_ids', 'default_code'])

                        if not variant_data_read or len(variant_data_read) == 0:
                            continue

                        variant_info = variant_data_read[0]

                        # Skip variants that already have SKU (existing ones we already updated)
                        if variant_info.get('default_code'):
                            continue

                        # Get attribute value from variant
                        # Find matching size in our missing_variant data
                        for variant_dict in missing_variants:
                            # We need to match the size value to the variant
                            # Read the attribute value name
                            if variant_info.get('product_template_attribute_value_ids'):
                                ptav_ids = variant_info['product_template_attribute_value_ids']
                                ptav_data = self.execute('product.template.attribute.value', 'read', ptav_ids, ['name', 'product_attribute_value_id'])

                                for ptav in ptav_data:
                                    # Read actual attribute value name
                                    pav_id = ptav.get('product_attribute_value_id')
                                    if pav_id:
                                        pav_data = self.execute('product.attribute.value', 'read', [pav_id[0]], ['name'])
                                        if pav_data and len(pav_data) > 0 and pav_data[0]['name'] == variant_dict['size']:
                                            # Found matching newly created variant!
                                            # Update with CSV data
                                            self.update_existing_variant(variant_product_id, variant_dict)

                                            # Register External ID for new variant
                                            variant_ext_id = f'product_variant_{self.sanitize_external_id(variant_dict["sku"])}'
                                            self.get_or_create_external_id('product.product', variant_product_id, variant_ext_id)
                                            _logger.debug(f"      Registered External ID: {variant_ext_id}")

                    _logger.info(f"    ✓ Created and updated {len(missing_variants)} new variant products")

                created_count += 1

            except Exception as e:
                _logger.error(f"  ✗ Failed to create variants for {base_sku}: {e}")
                continue

        _logger.info(f"✓ Created variants for {created_count} base products")
        return created_count

    def import_from_csv(self, csv_path):
        """
        Main import process

        Args:
            csv_path (str): Path to CSV file

        Returns:
            dict: Import statistics
        """
        start_time = time.time()

        _logger.info("="*60)
        _logger.info("JoiasMax Product Import Started")
        _logger.info("="*60)

        try:
            # Read CSV
            products = self.read_csv(csv_path)

            # Store CSV data for parent product lookups
            self.all_csv_products = products

            # Create category hierarchy
            self.create_category_hierarchy()

            # Process products
            _logger.info(f"\nProcessing {len(products)} products...")
            for i, product_row in enumerate(products, 1):
                if i % 10 == 0:
                    _logger.info(f"Progress: {i}/{len(products)} ({i*100//len(products)}%)")

                self.process_product(product_row)

            # Create product variants after all base products are created
            _logger.info("\n" + "="*60)
            _logger.info("Phase 2: Creating Product Variants")
            _logger.info("="*60)
            self.create_product_variants()

            # Calculate duration
            duration = time.time() - start_time
            self.stats['duration_seconds'] = duration
            self.stats['source_csv'] = csv_path
            self.stats['database'] = self.database

            # Print summary
            _logger.info("\n" + "="*60)
            _logger.info("Import Complete!")
            _logger.info("="*60)
            _logger.info(f"Total processed: {self.stats['total_processed']}")
            _logger.info(f"Successfully imported: {self.stats['imported']}")
            _logger.info(f"Duplicates skipped: {self.stats['duplicates']}")
            _logger.info(f"Failed/Skipped: {self.stats['skipped']}")
            _logger.info(f"Duration: {duration:.1f}s")
            _logger.info("="*60)

            return self.stats

        except Exception as e:
            _logger.error(f"Import failed: {e}")
            raise


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Import JoiasMax products from Bling CSV to Odoo')

    parser.add_argument('--csv', required=True, help='Path to Bling CSV export file')
    parser.add_argument('--url', default='http://localhost:8069', help='Odoo server URL')
    parser.add_argument('--database', default='tenant_joiasmax', help='Odoo database name')
    parser.add_argument('--username', default='admin', help='Odoo username')
    parser.add_argument('--password', default=os.environ.get('ODOO_PASSWORD', 'admin'),
                       help='Odoo password (or set ODOO_PASSWORD env var)')
    parser.add_argument('--output-dir', default='reports', help='Output directory for reports')
    parser.add_argument('--skip-updates', action='store_true',
                       help='Skip updating existing products (only create new ones) - useful for debugging')

    args = parser.parse_args()

    try:
        # Create importer
        importer = OdooProductImporter(
            url=args.url,
            database=args.database,
            username=args.username,
            password=args.password,
            skip_updates=args.skip_updates
        )

        # Run import
        stats = importer.import_from_csv(args.csv)

        # Generate reports
        _logger.info("\nGenerating reports...")
        generator = ImportReportGenerator(stats, output_dir=args.output_dir)
        reports = generator.generate_all_reports()

        _logger.info("\nGenerated reports:")
        for report_type, path in reports.items():
            _logger.info(f"  - {report_type}: {path}")

        _logger.info("\n✅ Import completed successfully!")
        return 0

    except Exception as e:
        _logger.error(f"\n❌ Import failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
