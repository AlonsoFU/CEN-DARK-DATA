# Shared Schemas - Operaciones Domain

This directory contains universal schema transformations and shared utilities for the operaciones domain, supporting all EAF chapters.

## Components

### `esquema_universal_chileno.py`
- Base definitions for the Chilean electrical system universal schema
- JSON-LD structure optimized for AI consumption
- Standard field mappings and data types

### `extractor_universal_integrado.py`
- Integrated extraction and transformation pipeline
- Converts chapter-specific extractions to universal format
- Handles data validation and quality assurance

### `referencias_cruzadas.py`
- Cross-reference management between documents
- Links related entities across different chapters
- Maintains referential integrity in the universal schema

## Integration with Domain Structure

Used by chapter processors in `../chapters/{chapter}/processors/`:
- **anexo_01_processor.py** - Uses these utilities for universal transformation
- **anexo_02_processor.py** - Transforms solar plant data to universal schema
- **informe_diario_processor.py** - Daily report transformations

## Usage

```python
# Import from shared utilities
from domains.operaciones.anexos_eaf.shared.utilities.extractor_universal_integrado import transform_to_universal

# Transform chapter-specific data to universal format
universal_data = transform_to_universal(
    chapter_data,
    chapter_type="anexo_01",
    source_document="EAF-089-2025"
)
```

## Schema Structure

The universal schema follows JSON-LD format with these key sections:
- **@context**: Semantic definitions and namespaces
- **entities**: Core business entities (companies, facilities, etc.)
- **events**: Operational events and incidents
- **metadata**: Processing metadata and data lineage
- **cross_references**: Links to related documents and entities