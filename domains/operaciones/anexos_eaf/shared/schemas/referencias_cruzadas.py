#!/usr/bin/env python3
"""
Sistema de Referencias Cruzadas - Sistema Eléctrico Chileno
Maneja las referencias cruzadas SEPARADAS de los documentos principales
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class GestorReferenciasCruzadas:
    """Gestiona referencias cruzadas entre documentos del sistema chileno"""

    def __init__(self):
        self.reglas_referencias = self._cargar_reglas_sistema_chileno()

    def _cargar_reglas_sistema_chileno(self) -> Dict:
        """Cargar reglas específicas del sistema eléctrico chileno"""
        return {
            "reglas_temporales": {
                "misma_fecha": {
                    "descripcion": "Vincular documentos de la misma fecha operativa",
                    "relacion": "MISMA_FECHA_OPERATIVA",
                    "confianza": 1.0,
                    "habilitado": True
                },
                "dias_consecutivos": {
                    "descripcion": "Vincular informes diarios consecutivos del SEN",
                    "relacion": "SIGUE_OPERACION",
                    "confianza": 0.9,
                    "habilitado": True
                }
            },

            "reglas_entidades": {
                "misma_central": {
                    "descripcion": "Vincular documentos que mencionan la misma central",
                    "relacion": "REFERENCIA_CENTRAL",
                    "confianza": 0.85,
                    "habilitado": True
                },
                "misma_empresa": {
                    "descripcion": "Vincular documentos de la misma empresa generadora",
                    "relacion": "REFERENCIA_EMPRESA",
                    "confianza": 0.8,
                    "habilitado": True
                }
            },

            "reglas_dominio_chile": {
                "operaciones_a_mercados": [
                    {
                        "condicion": "generacion_solar_mencionada",
                        "tipo_objetivo": "datos_precio_solar",
                        "relacion": "IMPACTA_PRECIO_MEDIODIA",
                        "confianza": 0.85,
                        "contexto": "Generación solar afecta precios mediodía en mercado spot chileno"
                    },
                    {
                        "condicion": "incidente_sistema",
                        "tipo_objetivo": "alteracion_mercado",
                        "relacion": "CAUSA_ALTERACION_MERCADO",
                        "confianza": 0.9,
                        "contexto": "Incidentes SEN causan alteraciones en mercado spot"
                    }
                ],
                "operaciones_a_legal": [
                    {
                        "condicion": "incidente_seguridad",
                        "tipo_objetivo": "normativa_seguridad",
                        "relacion": "DEBE_CUMPLIR_NORMATIVA",
                        "confianza": 0.95,
                        "contexto": "Incidentes de seguridad activan cumplimiento normativo CNE"
                    },
                    {
                        "condicion": "falla_equipo",
                        "tipo_objetivo": "norma_tecnica",
                        "relacion": "VIOLA_NORMA_TECNICA",
                        "confianza": 0.8,
                        "contexto": "Fallas de equipos pueden violar normas técnicas del Coordinador"
                    }
                ],
                "mercados_a_planificacion": [
                    {
                        "condicion": "alta_demanda_pronosticada",
                        "tipo_objetivo": "expansion_capacidad",
                        "relacion": "GATILLA_EXPANSION",
                        "confianza": 0.85,
                        "contexto": "Alta demanda gatilla estudios de expansión de transmisión"
                    }
                ]
            }
        }

    def generar_referencias_cruzadas(self, documento: Dict, todos_documentos: List[Dict] = None) -> Dict:
        """
        Generar archivo de referencias cruzadas separado

        Args:
            documento: Documento principal
            todos_documentos: Lista de todos los documentos para correlacionar

        Returns:
            Diccionario con referencias cruzadas para guardar por separado
        """

        doc_id = documento.get("@id")
        referencias = {
            "@context": "https://coordinador.cl/context/referencias/v1",
            "documento_principal": doc_id,
            "fecha_generacion": datetime.now().isoformat(),
            "sistema": "chileno",
            "referencias_encontradas": [],
            "estadisticas": {
                "total_referencias": 0,
                "por_tipo_relacion": {},
                "por_dominio_objetivo": {}
            }
        }

        if todos_documentos:
            # Referencias temporales
            refs_temporales = self._aplicar_reglas_temporales_chile(documento, todos_documentos)
            referencias["referencias_encontradas"].extend(refs_temporales)

            # Referencias por entidades
            refs_entidades = self._aplicar_reglas_entidades_chile(documento, todos_documentos)
            referencias["referencias_encontradas"].extend(refs_entidades)

            # Referencias específicas del dominio
            refs_dominio = self._aplicar_reglas_dominio_chile(documento, todos_documentos)
            referencias["referencias_encontradas"].extend(refs_dominio)

        # Calcular estadísticas
        referencias["estadisticas"] = self._calcular_estadisticas_referencias(
            referencias["referencias_encontradas"]
        )

        return referencias

    def _aplicar_reglas_temporales_chile(self, documento: Dict, todos_documentos: List[Dict]) -> List[Dict]:
        """Aplicar reglas temporales específicas del sistema chileno"""
        referencias = []
        fecha_doc = self._extraer_fecha_documento(documento)

        if not fecha_doc:
            return referencias

        for otro_doc in todos_documentos:
            if otro_doc.get("@id") == documento.get("@id"):
                continue

            otra_fecha = self._extraer_fecha_documento(otro_doc)
            if not otra_fecha:
                continue

            # Misma fecha operativa (común en informes del Coordinador)
            if (fecha_doc == otra_fecha and
                otro_doc.get("metadatos_universales", {}).get("dominio") !=
                documento.get("metadatos_universales", {}).get("dominio")):

                referencias.append({
                    "documento_objetivo": otro_doc.get("@id"),
                    "dominio_objetivo": otro_doc.get("metadatos_universales", {}).get("dominio"),
                    "tipo_relacion": "MISMA_FECHA_OPERATIVA",
                    "confianza": 1.0,
                    "contexto": f"Documentos operativos del SEN de la misma fecha: {fecha_doc}",
                    "sistema_origen": "chileno",
                    "aplicable_coordinador": True
                })

            # Días consecutivos (para informes diarios del SEN)
            elif abs((fecha_doc - otra_fecha).days) == 1:
                if self._es_informe_diario_sen(documento) and self._es_informe_diario_sen(otro_doc):
                    relacion = "SIGUE_OPERACION_SEN" if fecha_doc > otra_fecha else "PRECEDE_OPERACION_SEN"
                    referencias.append({
                        "documento_objetivo": otro_doc.get("@id"),
                        "dominio_objetivo": otro_doc.get("metadatos_universales", {}).get("dominio"),
                        "tipo_relacion": relacion,
                        "confianza": 0.9,
                        "contexto": "Informes operativos diarios consecutivos del SEN",
                        "sistema_origen": "chileno",
                        "aplicable_coordinador": True
                    })

        return referencias

    def _aplicar_reglas_entidades_chile(self, documento: Dict, todos_documentos: List[Dict]) -> List[Dict]:
        """Aplicar reglas basadas en entidades del sistema chileno"""
        referencias = []
        entidades_doc = self._extraer_nombres_entidades_chile(documento)

        for otro_doc in todos_documentos:
            if otro_doc.get("@id") == documento.get("@id"):
                continue

            otras_entidades = self._extraer_nombres_entidades_chile(otro_doc)

            # Mismas centrales eléctricas
            centrales_comunes = set(entidades_doc.get("centrales_electricas", [])) & set(otras_entidades.get("centrales_electricas", []))
            empresas_comunes = set(entidades_doc.get("empresas", [])) & set(otras_entidades.get("empresas", []))

            if centrales_comunes:
                referencias.append({
                    "documento_objetivo": otro_doc.get("@id"),
                    "dominio_objetivo": otro_doc.get("metadatos_universales", {}).get("dominio"),
                    "tipo_relacion": "REFERENCIA_CENTRAL_SEN",
                    "confianza": 0.85,
                    "contexto": f"Ambos mencionan centrales del SEN: {', '.join(list(centrales_comunes)[:3])}",
                    "entidades_compartidas": list(centrales_comunes),
                    "sistema_origen": "chileno"
                })

            elif empresas_comunes:
                referencias.append({
                    "documento_objetivo": otro_doc.get("@id"),
                    "dominio_objetivo": otro_doc.get("metadatos_universales", {}).get("dominio"),
                    "tipo_relacion": "REFERENCIA_EMPRESA_GENERADORA",
                    "confianza": 0.8,
                    "contexto": f"Ambos mencionan empresas generadoras: {', '.join(list(empresas_comunes)[:3])}",
                    "entidades_compartidas": list(empresas_comunes),
                    "sistema_origen": "chileno"
                })

        return referencias

    def _aplicar_reglas_dominio_chile(self, documento: Dict, todos_documentos: List[Dict]) -> List[Dict]:
        """Aplicar reglas específicas de dominios del sistema chileno"""
        referencias = []
        dominio_doc = documento.get("metadatos_universales", {}).get("dominio")
        contenido_doc = self._obtener_contenido_documento_chile(documento)

        # Obtener reglas aplicables para este dominio
        for clave_regla, reglas in self.reglas_referencias.get("reglas_dominio_chile", {}).items():
            if not clave_regla.startswith(dominio_doc):
                continue

            dominio_objetivo = clave_regla.split("_a_")[1]

            for regla in reglas:
                if self._verificar_condicion_regla_chile(regla["condicion"], contenido_doc):
                    # Encontrar documentos que coincidan en el dominio objetivo
                    documentos_coincidentes = self._encontrar_documentos_coincidentes_chile(
                        regla["tipo_objetivo"],
                        dominio_objetivo,
                        todos_documentos
                    )

                    for doc_objetivo in documentos_coincidentes:
                        referencias.append({
                            "documento_objetivo": doc_objetivo.get("@id"),
                            "dominio_objetivo": dominio_objetivo,
                            "tipo_relacion": regla["relacion"],
                            "confianza": regla["confianza"],
                            "contexto": regla["contexto"],
                            "regla_aplicada": regla["condicion"],
                            "sistema_origen": "chileno",
                            "regulador_aplicable": "Coordinador Eléctrico Nacional"
                        })

        return referencias

    def _extraer_fecha_documento(self, documento: Dict):
        """Extraer fecha del documento"""
        from datetime import datetime
        fecha_str = documento.get("metadatos_universales", {}).get("fecha_creacion")
        if fecha_str:
            try:
                return datetime.fromisoformat(fecha_str)
            except:
                pass
        return None

    def _extraer_nombres_entidades_chile(self, documento: Dict) -> Dict[str, List[str]]:
        """Extraer nombres de entidades chilenas del documento"""
        entidades = documento.get("entidades", {})
        resultado = {}

        for tipo_entidad, lista_entidades in entidades.items():
            if isinstance(lista_entidades, list):
                resultado[tipo_entidad] = [entidad.get("nombre", "") for entidad in lista_entidades if entidad.get("nombre")]

        return resultado

    def _obtener_contenido_documento_chile(self, documento: Dict) -> str:
        """Obtener contenido de texto del documento chileno para verificación de reglas"""
        partes_contenido = []

        # De metadatos universales
        metadatos = documento.get("metadatos_universales", {})
        partes_contenido.append(metadatos.get("titulo", ""))

        # De etiquetas semánticas
        etiquetas = documento.get("etiquetas_semanticas", [])
        partes_contenido.extend(etiquetas)

        # De entidades
        entidades = documento.get("entidades", {})
        for lista_entidades in entidades.values():
            if isinstance(lista_entidades, list):
                for entidad in lista_entidades:
                    partes_contenido.append(entidad.get("nombre", ""))

        return " ".join(partes_contenido).lower()

    def _verificar_condicion_regla_chile(self, condicion: str, contenido: str) -> bool:
        """Verificar si se cumple condición de regla para sistema chileno"""
        mapeo_condiciones = {
            "generacion_solar_mencionada": ["solar", "fotovoltaica", "pv"],
            "incidente_sistema": ["incidente", "falla", "interrupción", "emergencia", "desconexion"],
            "incidente_seguridad": ["seguridad", "accidente", "peligro", "riesgo"],
            "falla_equipo": ["falla", "avería", "defecto", "mal funcionamiento"],
            "alta_demanda_pronosticada": ["alta demanda", "peak", "máximo", "pronóstico alto"]
        }

        palabras_clave = mapeo_condiciones.get(condicion, [])
        return any(palabra_clave in contenido for palabra_clave in palabras_clave)

    def _encontrar_documentos_coincidentes_chile(self, tipo_objetivo: str, dominio_objetivo: str,
                                               todos_documentos: List[Dict]) -> List[Dict]:
        """Encontrar documentos chilenos que coincidan con el tipo objetivo"""
        documentos_coincidentes = []

        for doc in todos_documentos:
            if doc.get("metadatos_universales", {}).get("dominio") != dominio_objetivo:
                continue

            contenido_doc = self._obtener_contenido_documento_chile(doc)

            # Mapeo específico para sistema chileno
            palabras_clave_tipo = {
                "datos_precio_solar": ["solar", "precio", "costo marginal"],
                "alteracion_mercado": ["mercado", "interrupción", "alteración"],
                "normativa_seguridad": ["seguridad", "normativa", "cne"],
                "norma_tecnica": ["norma técnica", "especificación", "coordinador"],
                "expansion_capacidad": ["expansión", "transmisión", "capacidad"]
            }

            palabras_clave = palabras_clave_tipo.get(tipo_objetivo, [])
            if any(palabra_clave in contenido_doc for palabra_clave in palabras_clave):
                documentos_coincidentes.append(doc)

        return documentos_coincidentes[:5]  # Limitar a 5 coincidencias

    def _es_informe_diario_sen(self, documento: Dict) -> bool:
        """Verificar si es informe diario del SEN"""
        tipo_doc = documento.get("metadatos_universales", {}).get("tipo_documento", "").lower()
        titulo = documento.get("metadatos_universales", {}).get("titulo", "").lower()

        return any(palabra_clave in tipo_doc or palabra_clave in titulo
                  for palabra_clave in ["diario", "daily", "informe_diario", "operacion_diaria"])

    def _calcular_estadisticas_referencias(self, referencias: List[Dict]) -> Dict:
        """Calcular estadísticas de las referencias encontradas"""
        estadisticas = {
            "total_referencias": len(referencias),
            "por_tipo_relacion": {},
            "por_dominio_objetivo": {},
            "confianza_promedio": 0.0
        }

        if referencias:
            # Contar por tipo de relación
            for ref in referencias:
                tipo_rel = ref.get("tipo_relacion", "desconocido")
                estadisticas["por_tipo_relacion"][tipo_rel] = estadisticas["por_tipo_relacion"].get(tipo_rel, 0) + 1

                dominio_obj = ref.get("dominio_objetivo", "desconocido")
                estadisticas["por_dominio_objetivo"][dominio_obj] = estadisticas["por_dominio_objetivo"].get(dominio_obj, 0) + 1

            # Confianza promedio
            confianzas = [ref.get("confianza", 0.0) for ref in referencias]
            estadisticas["confianza_promedio"] = sum(confianzas) / len(confianzas)

        return estadisticas

    def guardar_referencias_cruzadas(self, referencias: Dict, documento_principal_id: str,
                                   directorio_salida: Path) -> Path:
        """Guardar referencias cruzadas en archivo separado"""

        # Crear nombre de archivo basado en el documento principal
        nombre_archivo = f"{documento_principal_id.replace(':', '_')}_referencias_cruzadas.json"
        ruta_archivo = directorio_salida / "referencias_cruzadas" / nombre_archivo

        # Asegurar que el directorio existe
        ruta_archivo.parent.mkdir(parents=True, exist_ok=True)

        # Guardar referencias
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            json.dump(referencias, f, indent=2, ensure_ascii=False)

        print(f"✅ Referencias cruzadas guardadas: {ruta_archivo}")
        return ruta_archivo

# Ejemplo de uso
if __name__ == "__main__":
    print("🇨🇱 Sistema de Referencias Cruzadas - Chile")
    print("=" * 50)

    gestor = GestorReferenciasCruzadas()

    # Documento de ejemplo
    documento_ejemplo = {
        "@id": "cen:operaciones:anexo_02:2025-02-25",
        "metadatos_universales": {
            "titulo": "ANEXO 2 - Generación Real SEN",
            "dominio": "operaciones",
            "fecha_creacion": "2025-02-25"
        },
        "entidades": {
            "centrales_electricas": [{"nombre": "Solar Atacama Norte"}]
        },
        "etiquetas_semanticas": ["solar", "generacion_real"]
    }

    referencias = gestor.generar_referencias_cruzadas(documento_ejemplo)
    print(f"📊 Referencias encontradas: {referencias['estadisticas']['total_referencias']}")
    print("✅ Sistema de referencias cruzadas chileno inicializado")