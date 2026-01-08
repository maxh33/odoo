# -*- coding: utf-8 -*-
"""
Data Validator for JoiasMax Product Import
Validates and cleans product data before import
"""

import re
import logging

_logger = logging.getLogger(__name__)


def parse_brazilian_price(price_str):
    """
    Parse Brazilian price format to float

    Examples:
        '1.003,52' → 1003.52
        'R$ 2.456,76' → 2456.76
        '835,72' → 835.72

    Args:
        price_str (str): Price string in Brazilian format

    Returns:
        float: Price value, or 0.0 if invalid
    """
    if not price_str:
        return 0.0

    try:
        # Remove BRL symbol and whitespace
        price_str = str(price_str).replace('R$', '').strip()

        # Brazilian format: . for thousands, , for decimals
        # Remove thousand separators
        price_str = price_str.replace('.', '')
        # Replace decimal comma with dot
        price_str = price_str.replace(',', '.')

        return float(price_str)
    except (ValueError, AttributeError) as e:
        _logger.warning(f"Could not parse price: {price_str} - {e}")
        return 0.0


def validate_sku(sku):
    """
    Validate and clean SKU

    Args:
        sku (str): Product SKU

    Returns:
        str: Cleaned SKU, or None if invalid
    """
    if not sku:
        return None

    # Clean whitespace and tabs
    sku = str(sku).strip()

    # Remove excessive whitespace
    sku = re.sub(r'\s+', ' ', sku)

    # SKU should not be empty
    if not sku or len(sku) < 1:
        return None

    return sku


def validate_product_name(name):
    """
    Validate and clean product name

    Args:
        name (str): Product name

    Returns:
        str: Cleaned name, or None if invalid
    """
    if not name:
        return None

    # Clean whitespace
    name = str(name).strip()

    # Remove excessive whitespace
    name = re.sub(r'\s+', ' ', name)

    # Name should not be empty
    if not name or len(name) < 3:
        _logger.warning(f"Product name too short: {name}")
        return None

    return name


def validate_weight(weight_grams):
    """
    Validate weight value

    Args:
        weight_grams (float or None): Weight in grams

    Returns:
        float or None: Validated weight, or None if invalid
    """
    if weight_grams is None:
        return None

    try:
        weight = float(weight_grams)

        # Weight should be positive
        if weight <= 0:
            _logger.warning(f"Invalid weight: {weight} (must be positive)")
            return None

        # Sanity check: weight should be reasonable (0.01g to 1000g for jewelry)
        if weight < 0.01 or weight > 1000:
            _logger.warning(f"Weight out of reasonable range: {weight}g")
            # Don't reject, but warn
            pass

        return weight

    except (ValueError, TypeError) as e:
        _logger.warning(f"Could not validate weight: {weight_grams} - {e}")
        return None


def validate_material_type(material_type):
    """
    Validate material type

    Args:
        material_type (str): Material type ('gold', 'silver', or None)

    Returns:
        str or None: Validated material type
    """
    if material_type not in ['gold', 'silver', None]:
        _logger.warning(f"Invalid material type: {material_type}")
        return None

    return material_type


def validate_metal_purity(metal_purity, material_type):
    """
    Validate metal purity for material type

    Args:
        metal_purity (str): Metal purity ('24k', '950', or None)
        material_type (str): Material type

    Returns:
        str or None: Validated purity
    """
    if material_type == 'gold':
        if metal_purity != '24k':
            _logger.warning(f"Invalid gold purity: {metal_purity} (should be '24k')")
            return '24k'  # Auto-correct to 24k for gold
        return '24k'

    elif material_type == 'silver':
        if metal_purity != '950':
            _logger.warning(f"Invalid silver purity: {metal_purity} (should be '950')")
            return '950'  # Auto-correct to 950 for silver
        return '950'

    else:
        # No material type = no purity
        return None


def validate_provider_indice(indice):
    """
    Validate provider indice value

    Args:
        indice (float): Provider indice factor

    Returns:
        float: Validated indice (defaults to 1.0 if invalid)
    """
    if indice is None:
        return 1.0  # Default

    try:
        indice = float(indice)

        # Indice should be positive and reasonable (0.5 to 5.0)
        if indice <= 0 or indice > 5.0:
            _logger.warning(f"Provider indice out of range: {indice} (using default 1.0)")
            return 1.0

        return indice

    except (ValueError, TypeError):
        _logger.warning(f"Could not validate provider indice: {indice} (using default 1.0)")
        return 1.0


def validate_markup_percentage(markup):
    """
    Validate markup percentage

    Args:
        markup (float): Markup percentage

    Returns:
        float: Validated markup (defaults to 200.0 if invalid)
    """
    if markup is None:
        return 200.0  # Default

    try:
        markup = float(markup)

        # Markup should be non-negative
        if markup < 0:
            _logger.warning(f"Negative markup: {markup} (using default 200.0)")
            return 200.0

        # Warn if markup seems unreasonable
        if markup > 1000:
            _logger.warning(f"Very high markup: {markup}%")

        return markup

    except (ValueError, TypeError):
        _logger.warning(f"Could not validate markup: {markup} (using default 200.0)")
        return 200.0


def validate_sale_delay(days):
    """
    Validate customer lead time (sale_delay field)

    Args:
        days (int or float or None): Production/delivery days

    Returns:
        int: Validated days (0-365), defaults to 0 if invalid
    """
    if days is None:
        return 0

    try:
        days = int(days)

        # Days should be non-negative and reasonable (0-365)
        if days < 0 or days > 365:
            _logger.warning(f"Sale delay out of range: {days} (clamping to 0-365)")
            return max(0, min(365, days))

        return days

    except (ValueError, TypeError):
        _logger.warning(f"Could not validate sale_delay: {days} (using default 0)")
        return 0


def clean_html_for_description(html_text):
    """
    Clean HTML for storage in Odoo description field

    Args:
        html_text (str): HTML content

    Returns:
        str: Cleaned HTML (preserves basic formatting)
    """
    if not html_text:
        return ''

    # Just return as-is for now (Odoo handles HTML fields)
    # Could add sanitization here if needed
    return html_text.strip()


def validate_product_data(product_data):
    """
    Validate complete product data dictionary

    Args:
        product_data (dict): Product data to validate

    Returns:
        tuple: (is_valid, cleaned_data, errors)
    """
    errors = []
    cleaned = {}

    # SKU (required)
    sku = validate_sku(product_data.get('default_code'))
    if not sku:
        errors.append('Missing or invalid SKU')
        return (False, None, errors)
    cleaned['default_code'] = sku

    # Product name (required)
    name = validate_product_name(product_data.get('name'))
    if not name:
        errors.append('Missing or invalid product name')
        return (False, None, errors)
    cleaned['name'] = name

    # Price (required)
    price = parse_brazilian_price(product_data.get('list_price', 0))
    if price <= 0:
        errors.append('Missing or invalid price')
        # Don't reject, but warn
        _logger.warning(f"Product {sku} has invalid price: {product_data.get('list_price')}")
    cleaned['list_price'] = price

    # Material type (optional)
    material_type = validate_material_type(product_data.get('material_type'))
    cleaned['material_type'] = material_type
    cleaned['is_jewelry'] = (material_type in ['gold', 'silver'])

    # Metal purity (conditional)
    if material_type:
        metal_purity = validate_metal_purity(product_data.get('metal_purity'), material_type)
        cleaned['metal_purity'] = metal_purity
    else:
        cleaned['metal_purity'] = None

    # Weight (optional)
    weight = validate_weight(product_data.get('metal_weight_grams'))
    cleaned['metal_weight_grams'] = weight

    # Provider indice (optional)
    indice = validate_provider_indice(product_data.get('provider_indice', 1.0))
    cleaned['provider_indice'] = indice

    # Markup (optional)
    markup = validate_markup_percentage(product_data.get('markup_percentage', 200.0))
    cleaned['markup_percentage'] = markup

    # Description (optional)
    description = clean_html_for_description(product_data.get('description', ''))
    cleaned['description'] = description

    # Description for e-commerce (optional)
    description_sale = clean_html_for_description(product_data.get('description_sale', ''))
    cleaned['description_sale'] = description_sale

    # Category (optional)
    if 'categ_id' in product_data:
        cleaned['categ_id'] = product_data['categ_id']

    # Barcode (optional) - GTIN/EAN for fiscal/inventory tracking
    barcode = product_data.get('barcode')
    if barcode:
        cleaned['barcode'] = str(barcode).strip()

    # Logistics weight in Kg (optional) - for shipping calculation
    weight_kg = product_data.get('weight', 0.0)
    if weight_kg and float(weight_kg) > 0:
        cleaned['weight'] = float(weight_kg)

    # Package volume in m³ (optional) - for shipping calculation
    volume_m3 = product_data.get('volume', 0.0)
    if volume_m3 and float(volume_m3) > 0:
        cleaned['volume'] = float(volume_m3)

    # Customer Lead Time (optional) - production/delivery days
    if 'sale_delay' in product_data:
        cleaned['sale_delay'] = validate_sale_delay(product_data['sale_delay'])

    # Manual override fields
    cleaned['use_manual_override'] = product_data.get('use_manual_override', False)
    cleaned['manual_override_price_brl'] = product_data.get('manual_override_price_brl', 0.0)

    return (True, cleaned, errors)


def sanitize_csv_value(value):
    """
    Sanitize value for CSV export

    Args:
        value: Any value

    Returns:
        str: Sanitized string safe for CSV
    """
    if value is None:
        return ''

    # Convert to string
    value = str(value).strip()

    # Remove problematic characters
    value = value.replace('\n', ' ').replace('\r', ' ')

    # Remove excess whitespace
    value = re.sub(r'\s+', ' ', value)

    return value


# Test function
def _test_validator():
    """Test data validation with sample data"""

    test_products = [
        {
            'default_code': 'B191\t',  # Has tab
            'name': 'Brinco Argola 9mm Ouro 18k',
            'list_price': '1.003,52',
            'material_type': 'gold',
            'metal_purity': '24k',
            'metal_weight_grams': 1.5,
        },
        {
            'default_code': '',  # Empty SKU (invalid)
            'name': 'Test Product',
            'list_price': '100,00',
        },
        {
            'default_code': '2601',
            'name': 'Aliança Prata 950',
            'list_price': 'R$ 102,12',
            'material_type': 'silver',
            'metal_purity': '950',
            'metal_weight_grams': None,  # Missing weight
        },
    ]

    print("=== Data Validation Test ===\n")

    for i, product in enumerate(test_products, 1):
        print(f"Test {i}: {product.get('name', 'UNNAMED')}")
        is_valid, cleaned, errors = validate_product_data(product)

        if is_valid:
            print(f"  ✓ Valid")
            print(f"  Cleaned SKU: {cleaned['default_code']}")
            print(f"  Price: R$ {cleaned['list_price']:.2f}")
            print(f"  Material: {cleaned.get('material_type', 'None')}")
            print(f"  Weight: {cleaned.get('metal_weight_grams', 'None')} g")
        else:
            print(f"  ✗ Invalid")
            print(f"  Errors: {', '.join(errors)}")

        print()


if __name__ == '__main__':
    _test_validator()
