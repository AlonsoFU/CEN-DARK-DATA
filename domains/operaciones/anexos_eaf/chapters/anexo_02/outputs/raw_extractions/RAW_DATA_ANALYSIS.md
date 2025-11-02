# ANEXO 2: Raw Data Analysis - Pattern Differences

## 🔍 Key Discovery: Completely Different Data Structure!

### **ANEXO 1 vs ANEXO 2 Format Comparison**

## 📊 ANEXO 1 Format (Generation Programming)
```
COORDINADOR ELÉCTRICO NACIONAL Programación Diaria del Sistema Eléctrico Nacional
martes, 25 de febrero de 2025 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24

Costos Operación         305 302 286 286 281 280 297 307 193  65  51  55  71  56  71  72  77  80  99 210 272 275 277 273 4.541
Costos Encendido/Det.      2   0   0   0   0   0   0   0  15  31   5   0   0   0   0   0   1  19   8 105  61   2   0   0   321
Costos Totales [kUSD]    307 302 286 286 281 280 297 307 208  95  56  55  71  56  71  72  78  80 197 315 333 277 277 273 4.862
```

**ANEXO 1 Characteristics:**
- **Metric-based rows**: Each row is a system-wide metric (costs, marginal costs, losses)
- **24 hourly values + total**: Standard format with clear column structure
- **Business logic focus**: Financial costs, system-wide calculations
- **Clear labels**: "Costos Operación", "Costo Marginal", etc.

## ⚡ ANEXO 2 Format (Real Generation)
```
RESUMEN DIARIO DE OPERACION DEL SEN
25-02-2025 26-02-2025
1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 TOT.DIA DMAX. DMED.
    MWh MWh/h MWh/h

PFV-ELBOCO                0,0 0,0 0,0 0,0 0,0 0,0 0,0 0,8 3,1 5,0 6,0 6,5 6,8 7,0 3,1 0,0 0,0 0,0 0,0 0,0 0,0 0,0 0,0 0,0  38,3  7,0  1,6
PFV-PUNTABAJASOLAR        0,0 0,0 0,0 0,0 0,0 0,0 0,0 0,0 0,0 0,2 1,1 1,9 1,9 1,9 1,9 1,9 1,9 1,8 1,3 0,4 0,0 0,0 0,0 0,0  16,1  1,9  0,7
PMGD-PFV-QUEBRADA-DE-TALCA 0,0 0,0 0,0 0,0 0,0 0,0 0,0 0,0 0,2 0,9 2,3 7,9 8,0 8,0 8,1 8,1 8,0 7,9 7,0 2,8 0,0 0,0 0,0 0,0  69,2  8,1  2,9
```

**ANEXO 2 Characteristics:**
- **Plant-based rows**: Each row is an individual power plant
- **24 hourly values + 3 summary columns**: TOT.DIA (total day), DMAX (daily max), DMED (daily average)
- **Operational focus**: Real generation values for each plant
- **Plant naming pattern**: PFV- (solar), PMGD-PFV- (small distributed solar)

## 🎯 Why Our Patterns Failed

### **Pattern Mismatch Analysis**

**Our Current Patterns Expected:**
```
CENTRAL HIDROELECTRICA COLBUN
Generación Real: 437 MW
Generación Programada: 450 MW  
Desviación: -13 MW
```

**Actual ANEXO 2 Format:**
```
PFV-PUNTABAJASOLAR  0,0 0,0 0,0 ... 0,0 16,1 1,9 0,7
                    ^^^ 24 hourly values ^^^  ^   ^   ^
                                           TOT DMAX DMED
```

### **Key Differences:**

1. **No "Real vs Programmed" comparison** - Only actual generation values
2. **No MW labels** - Values are implicit MWh (hourly) and summary statistics  
3. **No deviation calculations** - Data is pure operational output
4. **Tabular format** - Not descriptive text with labels
5. **Solar plant focus** - PFV prefix indicates photovoltaic solar plants

## 🔧 Required Pattern Updates

### **New Plant Name Patterns:**
```python
'power_plant': [
    r'(PFV-[A-ZÁÉÍÓÚÑ\-_]+)',              # Solar plants: PFV-ELBOCO
    r'(PMGD-PFV-[A-ZÁÉÍÓÚÑ\-_]+)',        # Distributed solar: PMGD-PFV-QUEBRADA
    r'(PMGD-[A-ZÁÉÍÓÚÑ\-_]+)',            # Other distributed generation
]
```

### **New MW Value Patterns:**
```python
# Extract from tabular format: name + 24 values + 3 summary
'tabular_generation': [
    r'([A-Z\-_]+)\s+((?:\d+,\d+\s+){24})(\d+,\d+)\s+(\d+,\d+)\s+(\d+,\d+)',
    # Group 1: Plant name
    # Group 2: 24 hourly values  
    # Group 3: Total daily (TOT.DIA)
    # Group 4: Daily maximum (DMAX)
    # Group 5: Daily average (DMED)
]
```

### **Data Structure Mapping:**
```json
{
  "plant_name": "PFV-PUNTABAJASOLAR",
  "data": {
    "plant_type": "SOLAR_PV",
    "daily_total_mwh": 16.1,
    "daily_max_mw": 1.9,
    "daily_avg_mw": 0.7,
    "hourly_values": [0.0, 0.0, ..., 0.0],
    "operational_hours": 10,
    "peak_hour": 14
  }
}
```

## 📋 Business Value Insights

### **What ANEXO 2 Actually Contains:**
- **Real-time solar generation patterns** by hour
- **Daily operational summaries** (total, max, average)
- **Individual plant performance** for distributed solar
- **Grid contribution analysis** for renewable sources

### **Different from Expected:**
- **Not real vs programmed comparison** (that might be in different ANEXO)
- **Operational data focus** rather than planning deviation
- **Solar/renewable focus** rather than traditional thermal/hydro
- **Performance monitoring** rather than reliability assessment

## 🎯 Next Steps for Correct Extraction

1. **Update plant name patterns** for PFV- and PMGD- prefixes
2. **Create tabular parsing** for 24-hour + 3-summary format  
3. **Add solar plant business logic** (operational hours, peak analysis)
4. **Revise expectations** - this is pure operational data, not comparison data
5. **Cross-reference** with other ANEXOs to find actual "real vs programmed" data