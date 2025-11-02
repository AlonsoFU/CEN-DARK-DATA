# ANEXO 2: Real Generation Data - Patterns and Rules

## Document Overview

**ANEXO 2** contains **real-time operational data** comparing actual vs programmed generation for Chilean power system plants.

**Target Pages**: 63-95 (33 pages)
**Data Type**: Real generation vs programmed generation comparison
**Business Value**: System performance analysis, reliability assessment
**Key Difference from ANEXO 1**: Shows what ACTUALLY happened vs what was PLANNED

## Data Structure

### Real Generation Records
```json
{
  "plant_name": "COLBUN",
  "data": {
    "plant_type": "HIDROELECTRICA",
    "programmed_generation_mw": 450,
    "real_generation_mw": 437,
    "deviation_mw": -13,
    "timestamp": "15:16",
    "operational_status": "OPERATIONAL"
  }
}
```

## Plant Name Patterns (UPDATED ✅)

### Tabular Format Recognition
- **PFV-[NAME]** - Solar photovoltaic plants (primary format)
- **PMGD-PFV-[NAME]** - Distributed solar PV plants (small-scale)
- **PMGD-[NAME]** - Other distributed generation
- **[NAME]** - Various plant types (fallback pattern)

### Actual Plants Discovered (185+ plants)
- ✅ **PFV-GUANCHOI**: 730.8 MWh daily (largest solar contributor)
- ✅ **PFV-PUNTABAJASOLAR**: 16.1 MWh daily (11 operational hours)
- ✅ **PMGD-PFV-GABRIELA**: 92.7 MWh daily (distributed solar)
- ✅ **PFV-CHIMBARONGO-NIEBLA**: 53.2 MWh daily (8.6 MW peak)

## Tabular Data Extraction (CORRECTED FORMAT ✅)

### MW Value Extraction from Tabular Format
```
PFV-PUNTABAJASOLAR  0,0 0,0 0,0 ... 1,9 0,0  16,1  1,9  0,7
                    ^^^^^^^ 24 hourly MWh ^^^^^ TOT  MAX  AVG
```

### Value Patterns
- **24 Hourly Values**: `(\d+,\d+)` - Comma decimal format (Chilean standard)
- **Daily Total (TOT.DIA)**: Total MWh generated per day
- **Daily Maximum (DMAX)**: Peak MW capacity reached
- **Daily Average (DMED)**: Average MW throughout day

### Business Logic Rules
- **Operational Hours**: Count of hours with generation > 0.0 MW
- **Peak Hour**: Hour with maximum generation (1-24)
- **Capacity Factor**: Daily total / (max capacity × 24 hours)
- **Plant Type**: Auto-classify based on name prefix

## Operational Status Patterns

### Status Indicators
- **OPERATIONAL** (default if no status mentioned)
- **FUERA DE SERVICIO** - Plant offline/out of service
- **MANTENIMIENTO** - Under maintenance
- **FALLA** - Equipment failure

### Business Logic
- **Operational Plants**: Contributing to system generation
- **Offline Plants**: Zero real generation, full negative deviation
- **System Performance**: Total real vs programmed comparison

## Timestamp Patterns

### Time Format Detection  
- **HH:MM** - Standard format (15:16)
- **Hora: HH:MM** - With label
- **HHhMM** - Alternative format

## Quality Validation

### Data Completeness Requirements
- **Required**: Plant name, real generation MW
- **Optional**: Programmed generation, deviation, timestamp, status
- **Completeness Score**: 40% for required + 20% for optional fields

### Known Plant Validation
- **Hydroelectric**: COLBUN, EL TORO, CANUTILLAR, LOMA ALTA, etc.
- **Thermal**: SANTA MARIA, GUACOLDA, BOCAMINA, CAMPICHE, etc.
- **Solar**: Pattern matching for *SOLAR suffix
- **Wind**: TOTORAL, PUNTA COLORADA, etc.

## System Performance Metrics

### Performance Assessment
- **UNDERPERFORMING**: Total deviation < 0 (actual < programmed)
- **OVERPERFORMING**: Total deviation > 0 (actual > programmed)
- **Deviation Percentage**: (Total Real - Total Programmed) / Total Programmed * 100

### Business Intelligence Insights
- **Grid Reliability**: Compare planning accuracy
- **Plant Efficiency**: Individual performance metrics
- **Outage Impact**: Generation losses from failures
- **Operational Patterns**: Time-series performance trends

## Extraction Confidence Levels

### HIGH Confidence (20+ patterns found)
- Multiple plants with complete data
- MW values and deviations properly extracted
- Operational status identified

### MEDIUM Confidence (5-19 patterns found)  
- Plant names identified but incomplete MW data
- Some generation values missing
- Requires pattern refinement

### LOW Confidence (<5 patterns found)
- Minimal data extracted
- May be wrong page or different data structure
- Needs manual review

## Chapter Integration

### Cross-Reference with Other ANEXOs
- **ANEXO 1**: Compare planning vs reality accuracy
- **ANEXO 5**: Link plant failures to company impacts
- **ANEXO 6**: Operational performance vs compliance requirements

### Data Relationships
- **Plant Performance**: Individual efficiency metrics
- **System Reliability**: Grid-wide performance indicators
- **Operational Analysis**: Real-time vs planning deviations