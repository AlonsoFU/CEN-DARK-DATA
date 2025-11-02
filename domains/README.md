# Domains - Document Processing Architecture

This directory contains domain-specific document processing pipelines for the Dark Data Platform. Each domain represents a specialized area of Chilean electrical system documentation.

## Domain Structure

### Active Domains
- **operaciones/** - Grid operations and EAF document processing (✅ Implemented)

### Planned Domains
- **legal/** - Legal compliance documents (🚧 Planned)
- **mercados/** - Energy market data (🚧 Planned)
- **planificacion/** - Planning and development (🚧 Planned)

## Document Processing Structure

Each processing unit can represent either a complete document or a chapter within a larger document. The architecture adapts to document complexity through a flexible structure:

```
domains/{domain}/
├── chapters/{unit}/                   # Processing unit (document or chapter)
│   ├── docs/                         # Unit documentation
│   │   ├── extraction_rules_and_validators.json # Extraction rules and code validators
│   │   ├── cross_references.json     # Reference mappings
│   │   └── processing_notes.md       # Processing documentation
│   │
│   ├── processors/                   # Processing code
│   │   └── {unit}_processor.py       # Main processor
│   │
│   ├── outputs/                      # Processing outputs
│   │   ├── raw_extractions/          # Raw extracted data
│   │   ├── validated_extractions/    # Validated data
│   │   └── universal_json/           # Universal schema output
│   │
│   └── universal_schema_adapters/    # Schema transformation utilities
│
└── shared/                           # Domain-wide shared resources
    ├── chapter_detection/            # Chapter identification utilities
    ├── schemas/                      # Shared schemas and patterns
    ├── scrapers/                     # Web scraping utilities
    ├── utilities/                    # Common processing utilities
    ├── tools/                        # Domain-specific tools
    └── source/                       # Source documents and references
```

**Note**: Processing units can be nested (chapters within chapters) when dealing with complex document hierarchies. The `shared/` folder is critical as it contains domain-wide utilities that work across all processing units, enabling consistent processing regardless of document structure.

**Key File**: `extraction_rules_and_validators.json` contains extraction rules and automated code validators that ensure processor quality and consistency. This file serves as the "quality control brain" for each processing unit, defining both what to extract and how to validate the extraction code.

## Universal Schema Format

All processed documents are transformed into a standardized universal JSON schema for AI consumption:

```json
{
  "document_metadata": {
    "document_id": "string",
    "document_type": "string",
    "source_file": "string",
    "processing_date": "ISO-8601",
    "extraction_version": "string",
    "domain": "string",
    "chapter": "string"
  },
  "content_structure": {
    "title": "string",
    "sections": [
      {
        "section_id": "string",
        "title": "string",
        "page_range": [start_page, end_page],
        "content_type": "string",
        "subsections": [
          {
            "subsection_id": "string",
            "title": "string",
            "content": "string",
            "tables": [],
            "figures": [],
            "references": []
          }
        ]
      }
    ]
  },
  "extracted_entities": {
    "companies": [
      {
        "name": "string",
        "rut": "string",
        "type": "string",
        "sector": "string"
      }
    ],
    "technical_data": {
      "installations": [],
      "equipment": [],
      "measurements": [],
      "coordinates": []
    },
    "temporal_data": {
      "dates": [],
      "periods": [],
      "schedules": []
    },
    "regulatory_references": {
      "laws": [],
      "regulations": [],
      "procedures": []
    }
  },
  "cross_references": {
    "internal_references": [],
    "external_documents": [],
    "related_entities": []
  },
  "quality_metrics": {
    "extraction_confidence": "float",
    "validation_status": "string",
    "processing_warnings": [],
    "manual_review_flags": []
  }
}
```

## Processing Workflow

1. **Raw Extraction** - PDF → structured data extraction
2. **Validation** - Data quality checks and cleaning
3. **Universal Transform** - Convert to universal schema
4. **Database Ingestion** - Load into SQLite database
5. **MCP Integration** - Make available via MCP servers

## Shared Components

### Domain Shared Resources (`{domain}/shared/`)
Each domain contains shared utilities and resources:
- **universal_schema_adapters/** - Transform domain-specific extractions to universal JSON
- **chapter_detection/** - Automatic chapter and section identification
- **scrapers/** - Web scraping utilities for live data
- **utilities/** - Common processing functions and helpers
- **schemas/** - Shared patterns and validation rules
- **tools/** - Domain-specific analysis and migration tools
- **source/** - Reference documents and source materials

### Cross-Domain References
The platform maintains cross-references between documents and entities across domains for comprehensive AI analysis.

## Adding New Domains

To add a new domain:

1. Create domain directory: `domains/{new_domain}/`
2. Implement chapter structure for each document type
3. Create domain-specific processors
4. Implement universal schema adapters
5. Add MCP server integration in `ai_platform/mcp_servers/`

## Chilean Electrical System Context

This platform specializes in Chilean electrical system (SEN) documents:
- **Regulator**: Coordinador Eléctrico Nacional
- **Document Types**: EAF reports, operational reports, market data, legal compliance
- **Key Entities**: Generation companies, transmission operators, distribution companies
- **Standards**: Chilean electrical regulations and international standards