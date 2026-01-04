"""
Custom Table Extractors

Domain-specific extractors for known table formats in EAF reports.

Extractors:
- costos_horarios: Hourly cost tables (26 cols)
- programacion_diaria: Daily programming tables (26 cols)
- centrales_desvio: Generation deviation tables (5 cols)
- centrales_grandes: Large plant availability tables (3 cols)
- movimientos_despacho: Dispatch movement tables (14+ cols)
- registro_operacion_sen: SEN operation record tables (30 cols)
- reporte_desconexion: Disconnection report tables (26 cols)
- horario_tecnologia: Hourly generation by technology (30 cols)
- indicador_compacto: Compact indicator tables (2-26 cols)
- eventos_hora: Hourly event tables (3-6 cols)
- scada_alarmas: SCADA alarm log tables (4 cols)
"""

from . import (
    costos_horarios,
    programacion_diaria,
    centrales_desvio,
    centrales_grandes,
    movimientos_despacho,
    registro_operacion_sen,
    reporte_desconexion,
    horario_tecnologia,
    indicador_compacto,
    eventos_hora,
    scada_alarmas,
)

__all__ = [
    'costos_horarios',
    'programacion_diaria',
    'centrales_desvio',
    'centrales_grandes',
    'movimientos_despacho',
    'registro_operacion_sen',
    'reporte_desconexion',
    'horario_tecnologia',
    'indicador_compacto',
    'eventos_hora',
    'scada_alarmas',
]
