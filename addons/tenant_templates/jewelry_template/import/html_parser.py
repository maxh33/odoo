# -*- coding: utf-8 -*-
"""
HTML Parser for JoiasMax Product Import
Extracts product information from HTML descriptions (Descrição Curta field)
"""

from bs4 import BeautifulSoup
import re
import logging

_logger = logging.getLogger(__name__)


def parse_html_description(html_text):
    """
    Parse HTML description and extract all relevant data

    Args:
        html_text (str): HTML content from Descrição Curta field

    Returns:
        dict: Extracted product information
    """
    if not html_text:
        return {}

    try:
        soup = BeautifulSoup(html_text, 'html.parser')
        text = soup.get_text()

        return {
            'weight_grams': extract_weight(html_text),
            'material_info': extract_material(html_text),
            'dimensions': extract_dimensions(html_text),
            'production_days': extract_production_time(html_text),
            'is_pair': is_sold_in_pairs(text),
            'raw_text': text,
        }
    except Exception as e:
        _logger.error(f"Error parsing HTML description: {e}")
        return {}


def extract_weight(html_text):
    """
    Extract weight in grams from HTML description

    Patterns:
    - "Peso Aproximado: 32g"
    - "Peso Aproximado no Tamanho 20: 4.4g"
    - "Peso Aproximado: 50cm 78,50g | 60cm 94g" (extracts first/smallest)

    Args:
        html_text (str): HTML content

    Returns:
        float: Weight in grams, or None if not found
    """
    if not html_text:
        return None

    soup = BeautifulSoup(html_text, 'html.parser')
    text = soup.get_text()

    # Pattern 1: Direct weight "Peso Aproximado: 32g"
    match = re.search(r'Peso\s+Aproximado:\s*(\d+(?:[.,]\d+)?)\s*g', text, re.I)
    if match:
        weight_str = match.group(1).replace(',', '.')
        try:
            return float(weight_str)
        except ValueError:
            pass

    # Pattern 2: Size 20 reference "Peso Aproximado no Tamanho 20: 4.4g"
    match = re.search(r'Peso\s+Aproximado\s+no\s+Tamanho\s+20:\s*(\d+(?:[.,]\d+)?)\s*g', text, re.I)
    if match:
        weight_str = match.group(1).replace(',', '.')
        try:
            return float(weight_str)
        except ValueError:
            pass

    # Pattern 3: Multi-size format "40cm 1.30g | 45cm 1.45g"
    # Extract all weights and use the first one (usually smallest size)
    matches = re.findall(r'(\d+)cm\s+(\d+(?:[.,]\d+)?)\s*g', text, re.I)
    if matches:
        try:
            # Convert first match (smallest size usually listed first)
            weight_str = matches[0][1].replace(',', '.')
            return float(weight_str)
        except (ValueError, IndexError):
            pass

    # No weight found
    return None


def extract_material(html_text):
    """
    Extract material type and detect temporary indice

    Args:
        html_text (str): HTML content

    Returns:
        dict: {
            'material_type': 'gold'/'silver'/None,
            'metal_purity': '24k'/'950'/None,
            'temp_indice': 1.10/1.0/None,
            'is_blend': True/False,
            'material_text': 'Original material text'
        }
    """
    if not html_text:
        return {
            'material_type': None,
            'metal_purity': None,
            'temp_indice': None,
            'is_blend': False,
            'material_text': ''
        }

    soup = BeautifulSoup(html_text, 'html.parser')
    text = soup.get_text()

    # Extract material text
    material_match = re.search(r'Material:?\s*([^<\n]+)', text, re.I)
    material_text = material_match.group(1).strip() if material_match else text

    # Check for blend first
    is_blend = bool(re.search(r'blend|mix|mix|misto', material_text, re.I))

    # Gold detection
    if re.search(r'ouro|gold', material_text, re.I):
        material_type = 'gold'
        metal_purity = '24k'  # ALWAYS 24k for gold (regardless of 18k/10k product type)

        # Detect if 18k for temporary indice
        if re.search(r'18k|750', material_text, re.I):
            temp_indice = 1.10  # Temporary simulation value
        else:
            temp_indice = 1.0  # Default

        return {
            'material_type': material_type,
            'metal_purity': metal_purity,
            'temp_indice': temp_indice,
            'is_blend': is_blend,
            'material_text': material_text
        }

    # Silver detection
    elif re.search(r'prata|silver|950', material_text, re.I):
        return {
            'material_type': 'silver',
            'metal_purity': '950',
            'temp_indice': 1.0,
            'is_blend': is_blend,
            'material_text': material_text
        }

    # Stainless steel or non-precious metal
    elif re.search(r'aço|aco|inox|steel', material_text, re.I):
        return {
            'material_type': None,  # Not jewelry-tracked
            'metal_purity': None,
            'temp_indice': None,
            'is_blend': is_blend,
            'material_text': material_text
        }

    # Material not detected
    return {
        'material_type': None,
        'metal_purity': None,
        'temp_indice': None,
        'is_blend': is_blend,
        'material_text': material_text
    }


def extract_dimensions(html_text):
    """
    Extract product dimensions from HTML

    Returns:
        dict: {
            'width_mm': float or None,
            'length_mm': float or None,
            'thickness_mm': float or None,
        }
    """
    if not html_text:
        return {'width_mm': None, 'length_mm': None, 'thickness_mm': None}

    soup = BeautifulSoup(html_text, 'html.parser')
    text = soup.get_text()

    dimensions = {
        'width_mm': None,
        'length_mm': None,
        'thickness_mm': None,
    }

    # Largura (Width)
    width_match = re.search(r'Largura(?:\s+Elo)?:\s*(\d+(?:[.,]\d+)?)\s*(mm|cm)', text, re.I)
    if width_match:
        value = float(width_match.group(1).replace(',', '.'))
        unit = width_match.group(2).lower()
        dimensions['width_mm'] = value * 10 if unit == 'cm' else value

    # Comprimento (Length)
    length_match = re.search(r'Comprimento(?:\s+Elo)?:\s*(\d+(?:[.,]\d+)?)\s*(mm|cm)', text, re.I)
    if length_match:
        value = float(length_match.group(1).replace(',', '.'))
        unit = length_match.group(2).lower()
        dimensions['length_mm'] = value * 10 if unit == 'cm' else value

    # Espessura (Thickness)
    thickness_match = re.search(r'Espessura(?:\s+do\s+Fio)?:\s*(\d+(?:[.,]\d+)?)\s*(mm|cm)', text, re.I)
    if thickness_match:
        value = float(thickness_match.group(1).replace(',', '.'))
        unit = thickness_match.group(2).lower()
        dimensions['thickness_mm'] = value * 10 if unit == 'cm' else value

    return dimensions


def extract_production_time(html_text):
    """
    Extract production time in business days

    Pattern: "Prazo Médio de Produção: 7 DIAS ÚTEIS"

    Returns:
        int: Production days, or None if not found
    """
    if not html_text:
        return None

    soup = BeautifulSoup(html_text, 'html.parser')
    text = soup.get_text()

    match = re.search(r'Prazo\s+(?:M[ée]dio\s+de\s+)?Produ[çc][ãa]o:\s*(\d+)\s*dias?\s+[úu]teis', text, re.I)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass

    return None


def is_sold_in_pairs(text):
    """
    Check if product is sold in pairs (e.g., earrings)

    Returns:
        bool: True if sold in pairs
    """
    if not text:
        return False

    return bool(re.search(r'brincos?\s+aos?\s+pares?|quantidade:?\s*brincos?\s+aos?\s+pares?|par\s+de\s+brincos?', text, re.I))


def detect_indice_from_name(product_name, description):
    """
    Detect temporary provider indice based on product name/description

    Args:
        product_name (str): Product name
        description (str): Product description

    Returns:
        float: Temporary indice (1.10 for 18k, 1.0 default)
    """
    combined_text = f"{product_name or ''} {description or ''}".lower()

    # Detect 18k products
    if re.search(r'18k|750', combined_text, re.I):
        return 1.10  # Temporary simulation value

    # Default
    return 1.0


def clean_html(html_text):
    """
    Strip HTML tags and return clean text

    Args:
        html_text (str): HTML content

    Returns:
        str: Clean text without HTML tags
    """
    if not html_text:
        return ''

    soup = BeautifulSoup(html_text, 'html.parser')
    return soup.get_text().strip()


# Test functions (for development/debugging)
def _test_parser():
    """Test the HTML parser with sample data"""

    test_cases = [
        # Gold ring with size 20 weight
        '<p>Peso Aproximado no Tamanho 20: 4.4g</p><p>Material: Ouro 18k 750</p>',

        # Direct weight
        '<p>Peso Aproximado: 32g</p><p>Material: Ouro Amarelo 18k</p>',

        # Silver chain with multi-size
        '<p>Peso Aproximado: 40cm 1.30g | 45cm 1.45g | 50cm 1,60g</p><p>Material: Prata de Lei 950</p>',

        # Product without weight
        '<p>Largura: 2.5mm</p><p>Material: Ouro 18k</p>',
    ]

    for i, html in enumerate(test_cases, 1):
        print(f"\n=== Test Case {i} ===")
        result = parse_html_description(html)
        print(f"Weight: {result.get('weight_grams')} g")
        material = result.get('material_info', {})
        print(f"Material: {material.get('material_type')}, Purity: {material.get('metal_purity')}, Indice: {material.get('temp_indice')}")


if __name__ == '__main__':
    _test_parser()
