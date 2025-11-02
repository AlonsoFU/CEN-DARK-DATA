#!/usr/bin/env python3
"""
Extractor Universal Integrado - Sistema Eléctrico Chileno
Convierte automáticamente extracciones a esquema universal CON referencias integradas
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from domains.operaciones.anexos_eaf.shared.schemas.esquema_universal_chileno import crear_documento_universal_chile, extraer_entidades_datos_chile

class ExtractorUniversalIntegrado:
    """Convierte automáticamente extracciones a esquema universal con referencias integradas"""

    def __init__(self):
        self.directorio_documentos = self._get_chapter_extractions_path()
        self.directorio_documentos.mkdir(parents=True, exist_ok=True)

    def procesar_extraccion_completa(self, datos_extraccion: dict,
                                   titulo_documento: str,
                                   fecha_documento: str,
                                   tipo_documento: str,
                                   dominio: str = "operaciones") -> dict:
        """
        Procesar extracción completa: documento universal + referencias automáticas

        Args:
            datos_extraccion: Tus datos de extracción existentes
            titulo_documento: Título del documento
            fecha_documento: Fecha YYYY-MM-DD
            tipo_documento: Tipo de documento
            dominio: Dominio del sistema

        Returns:
            Documento universal con referencias cruzadas integradas
        """

        # Paso 1: Crear documento universal base (sin referencias)
        documento_universal = crear_documento_universal_chile(
            datos_extraccion=datos_extraccion,
            titulo_documento=titulo_documento,
            fecha_documento=fecha_documento,
            tipo_documento=tipo_documento,
            dominio=dominio
        )

        # Paso 2: Buscar documentos existentes para referencias
        documentos_existentes = self._buscar_documentos_existentes()

        # Paso 3: Generar referencias cruzadas automáticamente
        referencias_cruzadas = self._generar_referencias_automaticas(
            documento_universal,
            documentos_existentes
        )

        # Paso 4: Integrar referencias en el documento
        documento_universal["referencias_cruzadas"] = referencias_cruzadas

        # Paso 5: Guardar documento con referencias integradas
        ruta_guardado = self._guardar_documento_universal(documento_universal)

        # Paso 6: Actualizar referencias de documentos existentes
        self._actualizar_referencias_documentos_existentes(documento_universal, documentos_existentes)

        print(f"✅ Documento universal procesado: {ruta_guardado}")
        print(f"📊 Referencias generadas: {len(referencias_cruzadas)}")
        print(f"🔄 Documentos actualizados: {len(documentos_existentes)}")

        return documento_universal

    def _buscar_documentos_existentes(self) -> List[Dict]:
        """Buscar todos los documentos universales existentes"""
        documentos = []

        # Buscar en el directorio de extracciones
        for archivo_json in self.directorio_documentos.glob("**/*.json"):
            if archivo_json.name.endswith("_universal.json"):
                try:
                    with open(archivo_json, 'r', encoding='utf-8') as f:
                        documento = json.load(f)
                        # Verificar que es documento universal
                        if "@context" in documento and "@id" in documento:
                            documentos.append(documento)
                except Exception as e:
                    print(f"⚠️ Error leyendo {archivo_json}: {e}")

        return documentos

    def _generar_referencias_automaticas(self, documento: Dict, otros_documentos: List[Dict]) -> List[Dict]:
        """Generar referencias cruzadas automáticamente usando reglas del sistema chileno"""

        referencias = []

        # Aplicar reglas automáticas
        referencias.extend(self._reglas_temporales_chile(documento, otros_documentos))
        referencias.extend(self._reglas_entidades_chile(documento, otros_documentos))
        referencias.extend(self._reglas_dominio_chile(documento, otros_documentos))

        # Remover duplicados y ordenar por confianza
        referencias_unicas = self._limpiar_referencias(referencias)

        return referencias_unicas

    def _reglas_temporales_chile(self, documento: Dict, otros_documentos: List[Dict]) -> List[Dict]:
        """Aplicar reglas temporales del sistema eléctrico chileno"""
        referencias = []
        fecha_doc = documento.get("metadatos_universales", {}).get("fecha_creacion")

        if not fecha_doc:
            return referencias

        for otro_doc in otros_documentos:
            otra_fecha = otro_doc.get("metadatos_universales", {}).get("fecha_creacion")
            otro_dominio = otro_doc.get("metadatos_universales", {}).get("dominio")

            # Misma fecha operativa del SEN
            if fecha_doc == otra_fecha and otro_dominio != documento.get("metadatos_universales", {}).get("dominio"):
                referencias.append({
                    "documento_objetivo": otro_doc.get("@id"),
                    "dominio_objetivo": otro_dominio,
                    "tipo_relacion": "MISMA_FECHA_OPERATIVA_SEN",
                    "confianza": 1.0,
                    "contexto": f"Documentos operativos del SEN de la misma fecha: {fecha_doc}",
                    "sistema": "chileno",
                    "automatico": True
                })

        return referencias

    def _reglas_entidades_chile(self, documento: Dict, otros_documentos: List[Dict]) -> List[Dict]:
        """Aplicar reglas basadas en entidades del sistema chileno"""
        referencias = []
        entidades_doc = self._extraer_nombres_entidades_documento(documento)

        for otro_doc in otros_documentos:
            otras_entidades = self._extraer_nombres_entidades_documento(otro_doc)

            # Centrales eléctricas comunes
            centrales_comunes = set(entidades_doc.get("centrales_electricas", [])) & set(otras_entidades.get("centrales_electricas", []))

            # Empresas comunes
            empresas_comunes = set(entidades_doc.get("empresas", [])) & set(otras_entidades.get("empresas", []))

            if centrales_comunes:
                referencias.append({
                    "documento_objetivo": otro_doc.get("@id"),
                    "dominio_objetivo": otro_doc.get("metadatos_universales", {}).get("dominio"),
                    "tipo_relacion": "REFERENCIA_CENTRAL_SEN",
                    "confianza": 0.85,
                    "contexto": f"Ambos documentos mencionan centrales del SEN: {', '.join(list(centrales_comunes)[:3])}",
                    "entidades_compartidas": list(centrales_comunes),
                    "sistema": "chileno",
                    "automatico": True
                })

            elif empresas_comunes:
                referencias.append({
                    "documento_objetivo": otro_doc.get("@id"),
                    "dominio_objetivo": otro_doc.get("metadatos_universales", {}).get("dominio"),
                    "tipo_relacion": "REFERENCIA_EMPRESA_GENERADORA",
                    "confianza": 0.8,
                    "contexto": f"Ambos documentos mencionan empresas generadoras: {', '.join(list(empresas_comunes)[:3])}",
                    "entidades_compartidas": list(empresas_comunes),
                    "sistema": "chileno",
                    "automatico": True
                })

        return referencias

    def _reglas_dominio_chile(self, documento: Dict, otros_documentos: List[Dict]) -> List[Dict]:
        """Aplicar reglas específicas de dominios del sistema chileno"""
        referencias = []
        dominio_doc = documento.get("metadatos_universales", {}).get("dominio")

        # Reglas específicas por dominio
        reglas_chile = {
            "operaciones": {
                "mercados": self._reglas_operaciones_a_mercados_chile,
                "legal": self._reglas_operaciones_a_legal_chile,
                "planificacion": self._reglas_operaciones_a_planificacion_chile
            },
            "mercados": {
                "planificacion": self._reglas_mercados_a_planificacion_chile
            }
        }

        if dominio_doc in reglas_chile:
            for dominio_objetivo, funcion_reglas in reglas_chile[dominio_doc].items():
                docs_objetivo = [d for d in otros_documentos
                               if d.get("metadatos_universales", {}).get("dominio") == dominio_objetivo]
                referencias.extend(funcion_reglas(documento, docs_objetivo))

        return referencias

    def _reglas_operaciones_a_mercados_chile(self, doc_operaciones: Dict, docs_mercados: List[Dict]) -> List[Dict]:
        """Reglas específicas: operaciones → mercados en sistema chileno"""
        referencias = []
        contenido = self._obtener_contenido_documento(doc_operaciones)

        for doc_mercado in docs_mercados:
            contenido_mercado = self._obtener_contenido_documento(doc_mercado)

            # Solar afecta precios mediodía
            if "solar" in contenido and ("precio" in contenido_mercado or "spot" in contenido_mercado):
                referencias.append({
                    "documento_objetivo": doc_mercado.get("@id"),
                    "dominio_objetivo": "mercados",
                    "tipo_relacion": "IMPACTA_PRECIO_MEDIODIA",
                    "confianza": 0.85,
                    "contexto": "Generación solar afecta precios mediodía en mercado spot chileno",
                    "regla_automatica": "solar_impacta_precios",
                    "sistema": "chileno",
                    "automatico": True
                })

            # Incidentes afectan mercado
            elif any(palabra in contenido for palabra in ["incidente", "falla", "interrupción"]) and "mercado" in contenido_mercado:
                referencias.append({
                    "documento_objetivo": doc_mercado.get("@id"),
                    "dominio_objetivo": "mercados",
                    "tipo_relacion": "CAUSA_ALTERACION_MERCADO",
                    "confianza": 0.9,
                    "contexto": "Incidentes del SEN causan alteraciones en mercado spot",
                    "regla_automatica": "incidentes_alteran_mercado",
                    "sistema": "chileno",
                    "automatico": True
                })

        return referencias

    def _reglas_operaciones_a_legal_chile(self, doc_operaciones: Dict, docs_legal: List[Dict]) -> List[Dict]:
        """Reglas específicas: operaciones → legal en sistema chileno"""
        referencias = []
        contenido = self._obtener_contenido_documento(doc_operaciones)

        for doc_legal in docs_legal:
            contenido_legal = self._obtener_contenido_documento(doc_legal)

            # Centrales ERNC → normativa ERNC
            if any(palabra in contenido for palabra in ["solar", "eólica", "biomasa"]) and "ernc" in contenido_legal:
                referencias.append({
                    "documento_objetivo": doc_legal.get("@id"),
                    "dominio_objetivo": "legal",
                    "tipo_relacion": "DEBE_CUMPLIR_NORMATIVA_ERNC",
                    "confianza": 0.9,
                    "contexto": "Centrales ERNC deben cumplir normativa de energías renovables",
                    "regla_automatica": "ernc_cumple_normativa",
                    "sistema": "chileno",
                    "automatico": True
                })

        return referencias

    def _reglas_operaciones_a_planificacion_chile(self, doc_operaciones: Dict, docs_planificacion: List[Dict]) -> List[Dict]:
        """Reglas específicas: operaciones → planificación en sistema chileno"""
        referencias = []
        # Implementar reglas específicas operaciones → planificación
        return referencias

    def _reglas_mercados_a_planificacion_chile(self, doc_mercados: Dict, docs_planificacion: List[Dict]) -> List[Dict]:
        """Reglas específicas: mercados → planificación en sistema chileno"""
        referencias = []
        # Implementar reglas específicas mercados → planificación
        return referencias

    def _extraer_nombres_entidades_documento(self, documento: Dict) -> Dict[str, List[str]]:
        """Extraer nombres de entidades del documento"""
        entidades = documento.get("entidades", {})
        nombres = {}

        for tipo_entidad, lista_entidades in entidades.items():
            if isinstance(lista_entidades, list):
                nombres[tipo_entidad] = [e.get("nombre", "") for e in lista_entidades if e.get("nombre")]

        return nombres

    def _obtener_contenido_documento(self, documento: Dict) -> str:
        """Obtener contenido de texto para verificación de reglas"""
        contenido = []

        # De metadatos
        metadatos = documento.get("metadatos_universales", {})
        contenido.append(metadatos.get("titulo", ""))

        # De etiquetas semánticas
        etiquetas = documento.get("etiquetas_semanticas", [])
        contenido.extend(etiquetas)

        # De nombres de entidades
        entidades = documento.get("entidades", {})
        for lista_entidades in entidades.values():
            if isinstance(lista_entidades, list):
                for entidad in lista_entidades:
                    contenido.append(entidad.get("nombre", ""))

        return " ".join(contenido).lower()

    def _limpiar_referencias(self, referencias: List[Dict]) -> List[Dict]:
        """Limpiar referencias: remover duplicados, ordenar por confianza"""
        # Remover duplicados por documento_objetivo + tipo_relacion
        referencias_unicas = []
        vistos = set()

        for ref in referencias:
            clave = (ref.get("documento_objetivo"), ref.get("tipo_relacion"))
            if clave not in vistos:
                vistos.add(clave)
                referencias_unicas.append(ref)

        # Ordenar por confianza descendente
        referencias_unicas.sort(key=lambda r: r.get("confianza", 0.0), reverse=True)

        return referencias_unicas

    def _guardar_documento_universal(self, documento: Dict) -> Path:
        """Guardar documento universal con referencias integradas"""
        doc_id = documento.get("@id", "documento_sin_id")
        nombre_archivo = f"{doc_id.replace(':', '_')}_universal.json"
        ruta_archivo = self.directorio_documentos / nombre_archivo

        # Añadir metadatos de guardado
        documento["metadatos_calidad"]["guardado_en"] = datetime.now().isoformat()
        documento["metadatos_calidad"]["ruta_archivo"] = str(ruta_archivo)
        documento["metadatos_calidad"]["referencias_integradas"] = len(documento.get("referencias_cruzadas", []))

        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            json.dump(documento, f, indent=2, ensure_ascii=False)

        return ruta_archivo

    def _actualizar_referencias_documentos_existentes(self, nuevo_documento: Dict, documentos_existentes: List[Dict]):
        """Actualizar referencias de documentos existentes para incluir el nuevo documento"""

        for doc_existente in documentos_existentes:
            referencias_nuevas = self._generar_referencias_hacia_nuevo_documento(doc_existente, nuevo_documento)

            if referencias_nuevas:
                # Añadir nuevas referencias al documento existente
                if "referencias_cruzadas" not in doc_existente:
                    doc_existente["referencias_cruzadas"] = []

                doc_existente["referencias_cruzadas"].extend(referencias_nuevas)

                # Limpiar duplicados
                doc_existente["referencias_cruzadas"] = self._limpiar_referencias(doc_existente["referencias_cruzadas"])

                # Guardar documento actualizado
                self._guardar_documento_universal(doc_existente)

    def _generar_referencias_hacia_nuevo_documento(self, doc_existente: Dict, nuevo_documento: Dict) -> List[Dict]:
        """Generar referencias desde documento existente hacia nuevo documento"""
        # Usar las mismas reglas pero en dirección opuesta
        referencias = self._generar_referencias_automaticas(doc_existente, [nuevo_documento])
        return referencias

# Función de utilidad para integrar fácilmente en tu código existente
def convertir_extraccion_a_universal(datos_extraccion: dict,
                                   titulo: str,
                                   fecha: str,
                                   tipo_doc: str,
                                   dominio: str = "operaciones") -> dict:
    """
    Función simple para convertir tu extracción a esquema universal con referencias automáticas

    Uso en tu código existente:
    ```python
    # Al final de tu función de extracción
    doc_universal = convertir_extraccion_a_universal(
        datos_extraccion=resultados,
        titulo="ANEXO 2 - Generación Real",
        fecha="2025-02-25",
        tipo_doc="anexo_02_generacion_real"
    )
    ```
    """
    extractor = ExtractorUniversalIntegrado()
    return extractor.procesar_extraccion_completa(datos_extraccion, titulo, fecha, tipo_doc, dominio)

# Ejemplo de uso
if __name__ == "__main__":
    print("🇨🇱 Extractor Universal Integrado - Sistema Chileno")
    print("=" * 60)

    # Simular datos de extracción
    datos_ejemplo = {
        "upper_table": {
            "rows": [
                {"central": "Solar Atacama Norte", "empresa": "Enel Chile", "potencia": "245.5"}
            ]
        },
        "system_metrics": {
            "generacion_total": 1245.8
        }
    }

    # Procesar con referencias automáticas
    doc_universal = convertir_extraccion_a_universal(
        datos_extraccion=datos_ejemplo,
        titulo="ANEXO 2 - Generación Real SEN",
        fecha="2025-02-25",
        tipo_doc="anexo_02_generacion_real"
    )

    print(f"✅ Documento procesado: {doc_universal['@id']}")
    print(f"📊 Referencias automáticas: {len(doc_universal.get('referencias_cruzadas', []))}")