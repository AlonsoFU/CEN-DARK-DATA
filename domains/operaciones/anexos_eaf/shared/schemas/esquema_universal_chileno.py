#!/usr/bin/env python3
"""
Esquema Universal Chileno - Sistema Eléctrico Nacional
Wrapper functions para convertir extracciones del sistema eléctrico chileno
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

def crear_documento_universal_chile(datos_extraccion: dict,
                                  titulo_documento: str,
                                  fecha_documento: str,
                                  tipo_documento: str,
                                  dominio: str = "operaciones",
                                  puntuacion_confianza: float = 0.85) -> dict:
    """
    Convierte resultados de extracción al formato de esquema universal chileno

    Args:
        datos_extraccion: Tus resultados de extracción existentes
        titulo_documento: Título del documento
        fecha_documento: Fecha en formato YYYY-MM-DD
        tipo_documento: Tipo de documento (anexo_01, anexo_02, etc.)
        dominio: Dominio del sistema (operaciones, mercados, legal, planificacion)
        puntuacion_confianza: Confianza general de la extracción

    Returns:
        Documento en formato de esquema universal chileno (SIN cross-references)
    """

    # Generar ID único del documento
    id_documento = f"cen:{dominio}:{tipo_documento}:{fecha_documento}"

    # Extraer entidades de tus datos existentes
    entidades = extraer_entidades_datos_chile(datos_extraccion)

    # Generar etiquetas semánticas
    etiquetas_semanticas = generar_etiquetas_semanticas_chile(datos_extraccion, dominio)

    documento_universal = {
        "@context": "https://coordinador.cl/context/v1",
        "@id": id_documento,
        "@type": obtener_tipo_documento_chile(dominio),

        "metadatos_universales": {
            "titulo": titulo_documento,
            "dominio": dominio,
            "tipo_documento": tipo_documento,
            "fecha_creacion": fecha_documento,
            "fecha_procesamiento": datetime.now().isoformat(),
            "idioma": "es",
            "version": "1.0",
            "estado": "final",
            "pais": "Chile",
            "regulador": "Coordinador Eléctrico Nacional",
            "sistema_electrico": "SEN"  # Sistema Eléctrico Nacional de Chile
        },

        "entidades": entidades,

        # ✅ SIN cross_references - se manejan por separado

        "etiquetas_semanticas": etiquetas_semanticas,

        "datos_especificos_dominio": {
            dominio: datos_extraccion  # TUS DATOS ORIGINALES SE PRESERVAN AQUÍ
        },

        "metadatos_calidad": {
            "confianza_extraccion": puntuacion_confianza,
            "estado_validacion": "aprobado",
            "metodo_procesamiento": "extraccion_automatizada",
            "puntuacion_calidad": puntuacion_confianza,
            "validado_humano": False,
            "sistema_electrico": "chileno",
            "normativa_aplicable": "Ley General de Servicios Eléctricos DFL N°4/2006"
        }
    }

    return documento_universal

def extraer_entidades_datos_chile(datos: dict) -> dict:
    """Extraer entidades del sistema eléctrico chileno"""

    entidades = {
        "centrales_electricas": [],
        "empresas": [],
        "ubicaciones": [],
        "regulaciones": [],
        "equipos": []
    }

    # Extraer de upper_table (estructura anexo)
    if "upper_table" in datos and "rows" in datos["upper_table"]:
        for fila in datos["upper_table"]["rows"]:
            # Buscar nombres de centrales
            nombre_central = None
            for campo in ["central", "planta", "generador", "unidad", "nombre"]:
                if campo in fila and fila[campo]:
                    nombre_candidato = fila[campo].strip()
                    if es_probable_nombre_central_chile(nombre_candidato):
                        nombre_central = nombre_candidato
                        break

            if nombre_central:
                entidades["centrales_electricas"].append({
                    "@id": f"cen:central:{normalizar_nombre_chile(nombre_central)}",
                    "@type": determinar_tipo_central_chile(nombre_central),
                    "nombre": nombre_central,
                    "confianza": 0.9,
                    "metadatos": {
                        "fuente_anexo": "tabla_superior",
                        "sistema_electrico": "chileno",
                        "region_sistema": determinar_region_chile(nombre_central)
                    }
                })

            # Buscar nombres de empresas chilenas
            nombre_empresa = None
            for campo in ["empresa", "compañia", "operador", "propietario"]:
                if campo in fila and fila[campo]:
                    nombre_candidato = fila[campo].strip()
                    if es_probable_nombre_empresa_chile(nombre_candidato):
                        nombre_empresa = nombre_candidato
                        break

            if nombre_empresa and not any(e["nombre"] == nombre_empresa for e in entidades["empresas"]):
                entidades["empresas"].append({
                    "@id": f"cen:empresa:{normalizar_nombre_chile(nombre_empresa)}",
                    "@type": "EmpresaElectricaChile",
                    "nombre": nombre_empresa,
                    "confianza": 0.85,
                    "metadatos": {
                        "pais": "Chile",
                        "sector": "generacion_electrica",
                        "regulador": "CNE"
                    }
                })

    # Extraer ubicaciones chilenas
    if "upper_table" in datos:
        texto_completo = json.dumps(datos).lower()
        regiones_chile = detectar_regiones_chile(texto_completo)
        for region in regiones_chile:
            entidades["ubicaciones"].append({
                "@id": f"cen:ubicacion:{normalizar_nombre_chile(region)}",
                "@type": "RegionChile",
                "nombre": region,
                "confianza": 0.75,
                "metadatos": {
                    "pais": "Chile",
                    "tipo_division": "region"
                }
            })

    # Remover duplicados
    for tipo_entidad in entidades:
        entidades[tipo_entidad] = remover_entidades_duplicadas(entidades[tipo_entidad])

    return entidades

def determinar_tipo_central_chile(nombre_central: str) -> str:
    """Determinar tipo de central del sistema eléctrico chileno"""
    nombre_lower = nombre_central.lower()

    # Tecnologías del sistema chileno
    if any(palabra in nombre_lower for palabra in ["solar", "fotovoltaica", "fv", "pv"]):
        return "CentralSolarChile"
    elif any(palabra in nombre_lower for palabra in ["eólica", "eolica", "viento"]):
        return "CentralEolicaChile"
    elif any(palabra in nombre_lower for palabra in ["hidro", "agua", "embalse", "pasada"]):
        return "CentralHidroelectricaChile"
    elif any(palabra in nombre_lower for palabra in ["térmica", "termica", "carbón", "carbon", "gas", "ciclo combinado", "petcoke"]):
        return "CentralTermicaChile"
    elif any(palabra in nombre_lower for palabra in ["biomasa", "biogas"]):
        return "CentralBiomasaChile"
    elif any(palabra in nombre_lower for palabra in ["geotermia", "geotermica"]):
        return "CentralGeotermicaChile"
    else:
        return "CentralElectricaChile"

def es_probable_nombre_central_chile(texto: str) -> bool:
    """Verificar si es nombre de central chilena"""
    if not isinstance(texto, str) or len(texto) < 3:
        return False

    # Saltar valores numéricos, fechas, unidades
    import re
    if re.match(r'^[\d\.\,\s]+$', texto.strip()):
        return False
    if texto.strip().upper() in ["MW", "GWH", "KV", "N/A", "SI", "NO"]:
        return False

    # Indicadores de centrales chilenas
    indicadores_central = ["central", "planta", "parque", "complejo"]
    palabras_energia = ["solar", "eólica", "eolica", "hidro", "térmica", "termica", "biomasa", "geotermia"]

    texto_lower = texto.lower()
    tiene_indicador = any(palabra in texto_lower for palabra in indicadores_central)
    tiene_energia = any(palabra in texto_lower for palabra in palabras_energia)

    if tiene_indicador and tiene_energia:
        return True

    # Nombres geográficos chilenos comunes en centrales
    lugares_chile = ["atacama", "antofagasta", "tarapacá", "coquimbo", "valparaíso", "maule", "biobío", "araucanía"]
    if any(lugar in texto_lower for lugar in lugares_chile) and tiene_energia:
        return True

    return False

def es_probable_nombre_empresa_chile(texto: str) -> bool:
    """Verificar si es nombre de empresa chilena del sector eléctrico"""
    if not isinstance(texto, str) or len(texto) < 3:
        return False

    # Empresas conocidas del sector eléctrico chileno
    empresas_chile = ["enel", "colbún", "aes", "engie", "statkraft", "acciona", "solarpack"]

    # Formas societarias chilenas
    formas_societarias = ["s.a.", "spa", "ltda.", "limitada"]

    texto_lower = texto.lower()

    # Verificar empresas conocidas
    if any(empresa in texto_lower for empresa in empresas_chile):
        return True

    # Verificar formas societarias + palabras clave del sector
    if any(forma in texto_lower for forma in formas_societarias):
        if any(palabra in texto_lower for palabra in ["energía", "energia", "eléctrica", "electrica", "generación", "generacion"]):
            return True

    return False

def detectar_regiones_chile(texto: str) -> list:
    """Detectar regiones de Chile mencionadas en el texto"""
    regiones_chile = [
        "Arica y Parinacota", "Tarapacá", "Antofagasta", "Atacama",
        "Coquimbo", "Valparaíso", "Metropolitana", "O'Higgins",
        "Maule", "Ñuble", "Biobío", "Araucanía", "Los Ríos",
        "Los Lagos", "Aysén", "Magallanes"
    ]

    regiones_encontradas = []
    for region in regiones_chile:
        if region.lower() in texto:
            regiones_encontradas.append(region)

    return regiones_encontradas

def determinar_region_chile(nombre_central: str) -> str:
    """Determinar región chilena basada en el nombre de la central"""
    nombre_lower = nombre_central.lower()

    mapeo_regiones = {
        "atacama": "Atacama",
        "antofagasta": "Antofagasta",
        "tarapacá": "Tarapacá",
        "coquimbo": "Coquimbo",
        "valparaíso": "Valparaíso",
        "santiago": "Metropolitana",
        "maule": "Maule",
        "biobío": "Biobío",
        "araucanía": "Araucanía"
    }

    for indicador, region in mapeo_regiones.items():
        if indicador in nombre_lower:
            return region

    return "No determinada"

def normalizar_nombre_chile(nombre: str) -> str:
    """Normalizar nombre chileno para ID de entidad"""
    import re
    # Remover caracteres especiales y normalizar acentos chilenos
    normalizado = re.sub(r'[^a-zA-ZáéíóúñÁÉÍÓÚÑ0-9\s]', '', nombre.lower())
    # Reemplazar acentos para IDs
    normalizado = (normalizado.replace('á', 'a').replace('é', 'e').replace('í', 'i')
                              .replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n'))
    normalizado = re.sub(r'\s+', '_', normalizado.strip())
    return normalizado

def remover_entidades_duplicadas(lista_entidades: list) -> list:
    """Remover entidades duplicadas por nombre"""
    nombres_vistos = set()
    entidades_unicas = []

    for entidad in lista_entidades:
        nombre = entidad.get("nombre", "")
        if nombre not in nombres_vistos:
            nombres_vistos.add(nombre)
            entidades_unicas.append(entidad)

    return entidades_unicas

def generar_etiquetas_semanticas_chile(datos: dict, dominio: str) -> list:
    """Generar etiquetas semánticas para el sistema chileno"""
    etiquetas = {dominio}

    # Añadir etiquetas específicas de Chile
    etiquetas.update(["chile", "sistema_electrico_nacional", "sen"])

    # Añadir etiquetas de tipo de datos
    texto_datos = json.dumps(datos).lower()
    if any(palabra in texto_datos for palabra in ["tiempo real", "actual", "ahora"]):
        etiquetas.add("tiempo_real")
    elif any(palabra in texto_datos for palabra in ["histórico", "pasado", "anterior"]):
        etiquetas.add("historico")

    # Añadir etiquetas específicas del dominio chileno
    if dominio == "operaciones":
        etiquetas.update(["operaciones_sen", "coordinador_electrico", "despacho_economico"])

        # Verificar energías renovables ERNC (Energías Renovables No Convencionales)
        if "solar" in texto_datos:
            etiquetas.add("ernc")
        if "eólica" in texto_datos or "eolica" in texto_datos:
            etiquetas.add("ernc")
        if "biomasa" in texto_datos:
            etiquetas.add("ernc")

    elif dominio == "mercados":
        etiquetas.update(["mercado_spot", "costo_marginal", "licitaciones"])
    elif dominio == "legal":
        etiquetas.update(["ley_electrica", "cne", "seg", "coordinador"])
    elif dominio == "planificacion":
        etiquetas.update(["expansion_transmision", "planificacion_sen", "estudios_transmision"])

    return sorted(list(etiquetas))

def obtener_tipo_documento_chile(dominio: str) -> str:
    """Obtener @type del documento chileno"""
    mapeo_tipos = {
        "operaciones": "DocumentoSistemaElectricoChile",
        "mercados": "InformeMercadoChile",
        "legal": "RegulacionSectorElectricoChile",
        "planificacion": "EstudioPlanificacionSEN"
    }
    return mapeo_tipos.get(dominio, "DocumentoChile")

def guardar_json_esquema_universal_chile(documento: dict, ruta_salida: Path):
    """Guardar documento en formato esquema universal chileno"""

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    documento["metadatos_calidad"]["guardado_en"] = datetime.now().isoformat()
    documento["metadatos_calidad"]["ruta_archivo"] = str(ruta_salida)

    with open(ruta_salida, 'w', encoding='utf-8') as f:
        json.dump(documento, f, indent=2, ensure_ascii=False)

    print(f"✅ Documento esquema universal chileno guardado: {ruta_salida}")
    return ruta_salida

if __name__ == "__main__":
    import re

    print("🇨🇱 Sistema de Esquema Universal Chileno")
    print("=" * 50)

    # Datos de ejemplo del sistema chileno
    datos_ejemplo = {
        "upper_table": {
            "rows": [
                {"central": "Solar Atacama Norte", "empresa": "Enel Green Power Chile S.A.", "potencia": "245.5"},
                {"central": "Parque Eólico Tarapacá", "empresa": "Colbún S.A.", "potencia": "180.0"}
            ]
        }
    }

    doc_universal = crear_documento_universal_chile(
        datos_extraccion=datos_ejemplo,
        titulo_documento="ANEXO 2 - Generación Real SEN",
        fecha_documento="2025-02-25",
        tipo_documento="anexo_02_generacion_real"
    )

    print(f"📄 Documento ID: {doc_universal['@id']}")
    print(f"🏭 Centrales extraídas: {len(doc_universal['entidades']['centrales_electricas'])}")
    print(f"🏢 Empresas extraídas: {len(doc_universal['entidades']['empresas'])}")
    print("✅ Esquema universal chileno creado correctamente")