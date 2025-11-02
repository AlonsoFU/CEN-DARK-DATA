"""
Universal Schema Templates and Base Classes

This module contains the universal schema templates and base classes used by
individual chapter adapters to transform their specific data to universal format.

Components:
- esquema_universal_chileno: Universal schema template definitions
- extractor_universal_integrado: Base extractor classes and utilities
- referencias_cruzadas: Cross-reference management templates
- configuracion_esquema_universal.json: Universal schema configuration

Usage:
Individual chapters import these templates to create their specific adapters:
- anexo_01/universal_schema_adapters/anexo_01_to_universal.py
- anexo_02/universal_schema_adapters/anexo_02_to_universal.py
- informe_diario/universal_schema_adapters/informe_diario_to_universal.py
"""

from .esquema_universal_chileno import *
from .extractor_universal_integrado import *
from .referencias_cruzadas import *

__all__ = [
    'esquema_universal_chileno',
    'extractor_universal_integrado',
    'referencias_cruzadas'
]