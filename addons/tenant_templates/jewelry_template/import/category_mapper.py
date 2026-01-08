# -*- coding: utf-8 -*-
"""
Category Mapper for JoiasMax Product Import
Cleans Bling category names and maps to Odoo category hierarchy
"""

import re
import logging

_logger = logging.getLogger(__name__)


# Category mapping from Bling to Odoo
CATEGORY_MAPPING = {
    # Brincos (Earrings)
    'TRAY BRINCO': ('Brincos', 'Joias'),
    'SHOPEE BRINCO': ('Brincos', 'Joias'),
    'BRINCOS': ('Brincos', 'Joias'),

    # Pulseiras (Bracelets)
    'SHOPEE PULSEIRA': ('Pulseiras', 'Joias'),
    'TRAY PULSEIRA': ('Pulseiras', 'Joias'),
    'PULSEIRAS': ('Pulseiras', 'Joias'),

    # Pingentes (Pendants)
    'TRAY PINGENTES': ('Pingentes', 'Joias'),
    'SHOPEE PINGENTES': ('Pingentes', 'Joias'),
    'PINGENTES': ('Pingentes', 'Joias'),

    # Alianças (Rings/Bands)
    'TRAY ALIANCAS PRATA': ('Alianças Prata', 'Alianças'),
    'TRAY ALIANCAS OURO 18K': ('Alianças Ouro 18k', 'Alianças'),
    'TRAY ALIANCAS BLEND': ('Alianças Blend', 'Alianças'),
    'TRAY ALIANCAS ACO INOX': ('Alianças Aço Inox', 'Alianças'),
    'TRAY ALIANCAS': ('Alianças', 'Joias'),
    'ALIANCAS': ('Alianças', 'Joias'),

    # Anéis (Rings)
    'SHOPEE ANEL': ('Anéis', 'Joias'),
    'TRAY ANEL': ('Anéis', 'Joias'),
    'ANEIS': ('Anéis', 'Joias'),

    # Correntes (Chains)
    'TRAY CORRENTES PRATA': ('Correntes Prata', 'Correntes'),
    'TRAY CORRENTES OURO 18K': ('Correntes Ouro 18k', 'Correntes'),
    'SHOPEE CORRENTES': ('Correntes', 'Joias'),
    'TRAY CORRENTES': ('Correntes', 'Joias'),
    'CORRENTES': ('Correntes', 'Joias'),

    # Berloques (Charms)
    'TRAY BERLOQUES': ('Berloques', 'Joias'),
    'SHOPEE BERLOQUES': ('Berloques', 'Joias'),
    'BERLOQUES': ('Berloques', 'Joias'),

    # Aparadores (Spacers/Separators)
    'TRAY APARADORES': ('Aparadores', 'Joias'),
    'TRAY APARADORES OURO': ('Aparadores', 'Joias'),
    'SHOPEE APARADORES': ('Aparadores', 'Joias'),
    'APARADORES': ('Aparadores', 'Joias'),
}


# Odoo category hierarchy
# Format: category_name: parent_name (None for root)
CATEGORY_HIERARCHY = {
    'Joias': None,  # Root category

    # Level 1 (under Joias)
    'Alianças': 'Joias',
    'Brincos': 'Joias',
    'Pingentes': 'Joias',
    'Pulseiras': 'Joias',
    'Correntes': 'Joias',
    'Anéis': 'Joias',
    'Berloques': 'Joias',
    'Aparadores': 'Joias',

    # Level 2 (under Alianças)
    'Alianças Ouro 18k': 'Alianças',
    'Alianças Prata': 'Alianças',
    'Alianças Blend': 'Alianças',
    'Alianças Aço Inox': 'Alianças',

    # Level 2 (under Correntes)
    'Correntes Ouro 18k': 'Correntes',
    'Correntes Prata': 'Correntes',
}


def extract_category_from_name(product_name):
    """
    Extract category from product description/name
    Used as fallback when CSV category field is empty

    Args:
        product_name (str): Product name/description

    Returns:
        str: Detected category name or 'Joias' if not detected
    """
    if not product_name:
        return 'Joias'

    # Normalize: uppercase, remove accents
    normalized = product_name.upper().strip()
    normalized = _remove_accents(normalized)

    # Keyword detection (order matters - specific before generic)
    # Check for specific keywords in product name
    if 'APARADOR' in normalized:
        return 'Aparadores'
    elif 'PULSEIRA' in normalized:
        return 'Pulseiras'
    elif 'ALIANCA' in normalized:
        return 'Alianças'
    elif 'ANEL' in normalized or 'ANEIS' in normalized:
        return 'Anéis'
    elif 'BRINCO' in normalized:
        return 'Brincos'
    elif 'CORRENTE' in normalized:
        return 'Correntes'
    elif 'PINGENTE' in normalized:
        return 'Pingentes'
    elif 'BERLOQUE' in normalized:
        return 'Berloques'

    # Default fallback
    return 'Joias'


def clean_category_name(bling_category, product_name=None):
    """
    Clean category name from Bling export
    Removes marketplace prefixes (TRAY, SHOPEE, etc.)

    Args:
        bling_category (str): Raw category from Bling CSV
        product_name (str, optional): Product name for fallback analysis

    Returns:
        str: Cleaned Odoo category name
    """
    # Priority 1: Use CSV category if populated
    if not bling_category:
        # Priority 2: Analyze product name if provided
        if product_name:
            _logger.info(f"CSV category empty, analyzing product name: {product_name[:50]}...")
            return extract_category_from_name(product_name)
        # Priority 3: Default fallback
        return 'Joias'  # Default category

    # Normalize: uppercase, remove special chars, normalize encoding
    bling_category = bling_category.upper().strip()

    # Remove accents for matching (ç → c, ã → a)
    normalized = _remove_accents(bling_category)

    # Look for exact match in mapping
    for key, (odoo_cat, _) in CATEGORY_MAPPING.items():
        if normalized == _remove_accents(key):
            return odoo_cat

    # Fallback: Remove marketplace prefixes and common words
    cleaned = re.sub(r'^(TRAY|SHOPEE|MAGALU|MERCADO LIVRE|ML|AMAZON)\s+', '', normalized)

    # Try to match cleaned version
    for key, (odoo_cat, _) in CATEGORY_MAPPING.items():
        if _remove_accents(cleaned) == _remove_accents(key):
            return odoo_cat

    # Last resort: try to detect category type from name
    if 'APARADOR' in cleaned:
        return 'Aparadores'
    elif 'BRINCO' in cleaned:
        return 'Brincos'
    elif 'PULSEIRA' in cleaned:
        return 'Pulseiras'
    elif 'PINGENTE' in cleaned:
        return 'Pingentes'
    elif 'ALIANCA' in cleaned:
        return 'Alianças'
    elif 'ANEL' in cleaned or 'ANEIS' in cleaned:
        return 'Anéis'
    elif 'CORRENTE' in cleaned:
        return 'Correntes'
    elif 'BERLOQUE' in cleaned:
        return 'Berloques'

    _logger.warning(f"Category not mapped: {bling_category} → defaulting to 'Joias'")
    return 'Joias'  # Default fallback


def get_parent_category(category_name):
    """
    Get parent category for a given category

    Args:
        category_name (str): Odoo category name

    Returns:
        str or None: Parent category name, or None if root
    """
    return CATEGORY_HIERARCHY.get(category_name)


def get_category_path(category_name):
    """
    Get full category path from root to category

    Args:
        category_name (str): Category name

    Returns:
        list: Category path from root to current (e.g., ['Joias', 'Alianças', 'Alianças Ouro 18k'])
    """
    path = [category_name]
    current = category_name

    while True:
        parent = get_parent_category(current)
        if parent is None:
            break
        path.insert(0, parent)
        current = parent

    return path


def get_all_categories_ordered():
    """
    Get all categories in creation order (parents before children)

    Returns:
        list: List of (category_name, parent_name) tuples in creation order
    """
    ordered = []

    # Root categories first
    for cat, parent in CATEGORY_HIERARCHY.items():
        if parent is None:
            ordered.append((cat, parent))

    # Then children, level by level
    max_depth = 5  # Safety limit
    for depth in range(max_depth):
        added_any = False
        for cat, parent in CATEGORY_HIERARCHY.items():
            if parent is not None and (cat, parent) not in ordered:
                # Check if parent already in list
                if any(c[0] == parent for c in ordered):
                    ordered.append((cat, parent))
                    added_any = True
        if not added_any:
            break

    return ordered


def _remove_accents(text):
    """
    Remove Portuguese accents for matching

    Args:
        text (str): Text with accents

    Returns:
        str: Text without accents
    """
    if not text:
        return ''

    # Portuguese accent mapping
    accent_map = {
        'Á': 'A', 'À': 'A', 'Â': 'A', 'Ã': 'A',
        'É': 'E', 'Ê': 'E',
        'Í': 'I',
        'Ó': 'O', 'Ô': 'O', 'Õ': 'O',
        'Ú': 'U', 'Ü': 'U',
        'Ç': 'C',
        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a',
        'é': 'e', 'ê': 'e',
        'í': 'i',
        'ó': 'o', 'ô': 'o', 'õ': 'o',
        'ú': 'u', 'ü': 'u',
        'ç': 'c',
    }

    result = ''
    for char in text:
        result += accent_map.get(char, char)

    return result


def normalize_category_name(category_name):
    """
    Normalize category name for display

    Args:
        category_name (str): Raw category name

    Returns:
        str: Normalized name with proper capitalization
    """
    if not category_name:
        return ''

    # Title case with Portuguese rules
    words = category_name.split()
    normalized = []

    for word in words:
        # Keep acronyms uppercase (18k, Aço, etc.)
        if word.upper() in ['18K', '24K', '950', 'AÇO', 'ACO']:
            normalized.append(word.upper())
        # Title case for regular words
        else:
            normalized.append(word.capitalize())

    return ' '.join(normalized)


# Test function
def _test_mapper():
    """Test category mapping with sample data"""

    test_categories = [
        'TRAY BRINCO',
        'SHOPEE PULSEIRA',
        'Tray Aliancas Ouro 18k',
        'TRAY PINGENTES',
        'SHOPEE ANEL',
        'Tray Correntes Prata',
        'UNKNOWN CATEGORY',
    ]

    print("=== Category Mapping Test ===\n")

    for bling_cat in test_categories:
        odoo_cat = clean_category_name(bling_cat)
        parent = get_parent_category(odoo_cat)
        path = get_category_path(odoo_cat)

        print(f"Bling: '{bling_cat}'")
        print(f"  → Odoo: '{odoo_cat}'")
        print(f"  → Parent: '{parent}'")
        print(f"  → Path: {' > '.join(path)}\n")

    print("=== Category Creation Order ===\n")
    for cat, parent in get_all_categories_ordered():
        print(f"{cat} (parent: {parent or 'root'})")


if __name__ == '__main__':
    _test_mapper()
