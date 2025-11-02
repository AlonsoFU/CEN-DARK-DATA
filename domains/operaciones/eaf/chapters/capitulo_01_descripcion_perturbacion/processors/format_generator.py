"""
Generador de Formato Específico - EAF
Aplica formato HTML/CSS específico según el tipo de contenido detectado
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any
from content_type_detector import ContentTypeDetector


class FormatGenerator:
    """Genera formato específico para cada tipo de contenido."""

    def __init__(self):
        self.css_styles = self._load_css_styles()

    def _load_css_styles(self) -> Dict:
        """Carga estilos CSS para cada tipo de contenido."""

        return {
            "tables": {
                "css": """
                .eaf-table {
                    border-collapse: collapse;
                    width: 100%;
                    margin: 16px 0;
                    font-family: 'Verdana', sans-serif;
                    font-size: 9pt;
                }
                .eaf-table th {
                    background-color: #f5f5f5;
                    border: 1px solid #ccc;
                    padding: 8px;
                    text-align: left;
                    font-weight: bold;
                }
                .eaf-table td {
                    border: 1px solid #ccc;
                    padding: 8px;
                    text-align: left;
                }
                .eaf-table .numeric {
                    text-align: right;
                }
                """,
                "template": "<table class='eaf-table'>{content}</table>"
            },

            "paragraphs": {
                "css": """
                .eaf-paragraph {
                    font-family: 'Verdana', sans-serif;
                    font-size: 9pt;
                    line-height: 1.6;
                    text-align: justify;
                    margin: 12px 0;
                    color: #333;
                }
                """,
                "template": "<p class='eaf-paragraph'>{content}</p>"
            },

            "headers": {
                "css": """
                .eaf-header-1 {
                    font-family: 'Verdana', sans-serif;
                    font-size: 12pt;
                    font-weight: bold;
                    color: #2c5aa0;
                    margin-top: 24px;
                    margin-bottom: 12px;
                    border-bottom: 2px solid #2c5aa0;
                    padding-bottom: 4px;
                }
                .eaf-header-2 {
                    font-family: 'Verdana', sans-serif;
                    font-size: 11pt;
                    font-weight: bold;
                    color: #4a6fa5;
                    margin-top: 20px;
                    margin-bottom: 10px;
                }
                .eaf-header-3 {
                    font-family: 'Verdana', sans-serif;
                    font-size: 10pt;
                    font-weight: bold;
                    color: #666;
                    margin-top: 16px;
                    margin-bottom: 8px;
                }
                """,
                "template": "<h{level} class='eaf-header-{level}' id='{anchor}'>{content}</h{level}>"
            },

            "formulas": {
                "css": """
                .eaf-formula {
                    font-family: 'Courier New', monospace;
                    background-color: #f9f9f9;
                    border: 1px dashed #999;
                    padding: 12px;
                    margin: 16px 0;
                    text-align: center;
                    border-radius: 4px;
                }
                .eaf-formula .variable {
                    font-style: italic;
                    color: #0066cc;
                }
                .eaf-formula .operator {
                    font-weight: bold;
                    color: #cc0000;
                }
                """,
                "template": "<div class='eaf-formula'>{content}</div>"
            },

            "images": {
                "css": """
                .eaf-figure {
                    margin: 20px auto;
                    text-align: center;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 8px;
                    background-color: #fafafa;
                }
                .eaf-figure img {
                    max-width: 100%;
                    height: auto;
                    display: block;
                    margin: 0 auto;
                }
                .eaf-figure figcaption {
                    font-family: 'Verdana', sans-serif;
                    font-size: 8pt;
                    color: #666;
                    margin-top: 8px;
                    font-style: italic;
                }
                """,
                "template": "<figure class='eaf-figure'><img src='{src}' alt='{alt}'/><figcaption>{caption}</figcaption></figure>"
            },

            "lists": {
                "css": """
                .eaf-list {
                    font-family: 'Verdana', sans-serif;
                    font-size: 9pt;
                    margin: 12px 0;
                    padding-left: 20px;
                }
                .eaf-list li {
                    margin-bottom: 6px;
                    line-height: 1.4;
                }
                .eaf-list.numbered {
                    list-style-type: decimal;
                }
                .eaf-list.bulleted {
                    list-style-type: disc;
                }
                """,
                "template": "<{list_type} class='eaf-list {style_class}'>{content}</{list_type}>"
            }
        }

    def generate_formatted_content(self, analysis: Dict) -> Dict:
        """Genera contenido formateado basándose en el análisis de tipos."""

        formatted_output = {
            "metadata": {
                "format_version": "1.0",
                "generated_css": True,
                "responsive_design": True
            },
            "css_styles": self._compile_all_css(),
            "formatted_content": {},
            "structure_map": []
        }

        # Procesar cada tipo de contenido
        for content_type, items in analysis["content_types"].items():
            if items:
                formatted_items = []

                for item in items:
                    formatted_item = self._format_content_item(item, content_type)
                    formatted_items.append(formatted_item)

                    # Agregar al mapa de estructura
                    formatted_output["structure_map"].append({
                        "type": content_type,
                        "id": item["block_id"],
                        "position": item["bbox"],
                        "formatted": True
                    })

                formatted_output["formatted_content"][content_type] = formatted_items

        return formatted_output

    def _format_content_item(self, item: Dict, content_type: str) -> Dict:
        """Formatea un item específico según su tipo."""

        text = item.get("text", "")

        if content_type == "tables":
            return self._format_table(item)
        elif content_type == "paragraphs":
            return self._format_paragraph(item)
        elif content_type == "headers":
            return self._format_header(item)
        elif content_type == "formulas":
            return self._format_formula(item)
        elif content_type == "images":
            return self._format_image(item)
        elif content_type == "lists":
            return self._format_list(item)
        else:
            return self._format_generic(item)

    def _format_table(self, item: Dict) -> Dict:
        """Formatea una tabla detectada."""

        text = item.get("text", "")
        characteristics = item.get("characteristics", {})

        # Parsear contenido tabular
        lines = text.split('\n')
        table_data = []

        for line in lines:
            if line.strip():
                cells = line.split()  # Simplificado - mejorar con análisis de posición
                if len(cells) >= 2:
                    table_data.append(cells)

        # Generar HTML de tabla
        html_rows = []

        if table_data:
            # Primera fila como header si se detectó
            if characteristics.get("header_detected", False) and table_data:
                header_row = "<tr>" + "".join(f"<th>{cell}</th>" for cell in table_data[0]) + "</tr>"
                html_rows.append(header_row)
                table_data = table_data[1:]  # Resto como datos

            # Filas de datos
            for row in table_data:
                data_row = "<tr>" + "".join(f"<td class='{'numeric' if self._is_numeric(cell) else 'text'}'>{cell}</td>" for cell in row) + "</tr>"
                html_rows.append(data_row)

        table_html = self.css_styles["tables"]["template"].format(
            content="\n".join(html_rows)
        )

        return {
            "original_item": item,
            "formatted_html": table_html,
            "format_type": "table",
            "structure": {
                "rows": len(table_data),
                "columns": max(len(row) for row in table_data) if table_data else 0,
                "has_header": characteristics.get("header_detected", False)
            }
        }

    def _format_paragraph(self, item: Dict) -> Dict:
        """Formatea un párrafo."""

        text = item.get("text", "").strip()

        # Limpiar y formatear texto
        clean_text = self._clean_text_for_html(text)

        paragraph_html = self.css_styles["paragraphs"]["template"].format(
            content=clean_text
        )

        return {
            "original_item": item,
            "formatted_html": paragraph_html,
            "format_type": "paragraph",
            "word_count": len(text.split()),
            "char_count": len(text)
        }

    def _format_header(self, item: Dict) -> Dict:
        """Formatea un encabezado."""

        text = item.get("text", "").strip()
        characteristics = item.get("characteristics", {})

        # Determinar nivel jerárquico
        hierarchy_level = characteristics.get("hierarchy_level", 1)
        if hierarchy_level > 6:
            hierarchy_level = 6  # HTML máximo h6

        # Crear anchor para navegación
        anchor = self._create_anchor_from_text(text)

        # Limpiar texto
        clean_text = self._clean_text_for_html(text)

        header_html = self.css_styles["headers"]["template"].format(
            level=hierarchy_level,
            anchor=anchor,
            content=clean_text
        )

        return {
            "original_item": item,
            "formatted_html": header_html,
            "format_type": "header",
            "hierarchy_level": hierarchy_level,
            "anchor": anchor,
            "numbering": characteristics.get("numbering_style", "none")
        }

    def _format_formula(self, item: Dict) -> Dict:
        """Formatea una fórmula matemática."""

        text = item.get("text", "").strip()
        characteristics = item.get("characteristics", {})

        # Resaltar variables y operadores
        formatted_text = self._highlight_formula_elements(text, characteristics)

        formula_html = self.css_styles["formulas"]["template"].format(
            content=formatted_text
        )

        return {
            "original_item": item,
            "formatted_html": formula_html,
            "format_type": "formula",
            "mathematical_symbols": characteristics.get("mathematical_symbols", []),
            "variables": characteristics.get("variables", [])
        }

    def _format_image(self, item: Dict) -> Dict:
        """Formatea una imagen."""

        characteristics = item.get("characteristics", {})

        # Generar src y caption
        src = f"image_{item['block_id']}.png"  # Placeholder
        alt = f"Imagen {item['block_id']}"
        caption = f"Figura: {characteristics.get('estimated_type', 'Imagen del documento')}"

        image_html = self.css_styles["images"]["template"].format(
            src=src,
            alt=alt,
            caption=caption
        )

        return {
            "original_item": item,
            "formatted_html": image_html,
            "format_type": "image",
            "dimensions": {
                "width": characteristics.get("width", 0),
                "height": characteristics.get("height", 0)
            },
            "image_type": characteristics.get("estimated_type", "unknown")
        }

    def _format_list(self, item: Dict) -> Dict:
        """Formatea una lista."""

        text = item.get("text", "")
        lines = text.split('\n')

        # Detectar tipo de lista
        is_numbered = any(re.match(r'^\s*\d+[\.)]\s+', line) for line in lines)
        list_type = "ol" if is_numbered else "ul"
        style_class = "numbered" if is_numbered else "bulleted"

        # Generar items de lista
        list_items = []
        for line in lines:
            clean_line = re.sub(r'^\s*[-•·\d+\.)]\s*', '', line).strip()
            if clean_line:
                list_items.append(f"<li>{clean_line}</li>")

        list_html = self.css_styles["lists"]["template"].format(
            list_type=list_type,
            style_class=style_class,
            content="\n".join(list_items)
        )

        return {
            "original_item": item,
            "formatted_html": list_html,
            "format_type": "list",
            "list_type": "ordered" if is_numbered else "unordered",
            "item_count": len(list_items)
        }

    def _format_generic(self, item: Dict) -> Dict:
        """Formato genérico para contenido no clasificado."""

        text = item.get("text", "").strip()
        clean_text = self._clean_text_for_html(text)

        generic_html = f"<div class='eaf-content'>{clean_text}</div>"

        return {
            "original_item": item,
            "formatted_html": generic_html,
            "format_type": "generic"
        }

    def _clean_text_for_html(self, text: str) -> str:
        """Limpia texto para HTML."""
        import html

        # Escape HTML
        clean = html.escape(text)

        # Convertir saltos de línea
        clean = clean.replace('\n', '<br>')

        return clean

    def _highlight_formula_elements(self, text: str, characteristics: Dict) -> str:
        """Resalta elementos de fórmula con spans de CSS."""

        # Resaltar variables
        variables = characteristics.get("variables", [])
        for var in variables:
            text = text.replace(var, f"<span class='variable'>{var}</span>")

        # Resaltar operadores
        operators = ['+', '-', '*', '/', '=', '×', '÷']
        for op in operators:
            if op in text:
                text = text.replace(op, f"<span class='operator'>{op}</span>")

        return text

    def _create_anchor_from_text(self, text: str) -> str:
        """Crea un anchor ID desde el texto."""

        # Limpiar y convertir a ID válido
        anchor = re.sub(r'[^\w\s-]', '', text.lower())
        anchor = re.sub(r'[\s_-]+', '-', anchor)
        anchor = anchor.strip('-')

        return anchor[:50]  # Limitar longitud

    def _is_numeric(self, text: str) -> bool:
        """Verifica si el texto es numérico."""

        try:
            float(text.replace(',', '.'))
            return True
        except ValueError:
            return bool(re.search(r'\d+\.\d+|\d+,\d+', text))

    def _compile_all_css(self) -> str:
        """Compila todos los estilos CSS en uno solo."""

        all_css = []

        # CSS base
        base_css = """
        .eaf-document {
            font-family: 'Verdana', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }

        .eaf-content {
            margin: 8px 0;
        }
        """
        all_css.append(base_css)

        # CSS específico por tipo
        for content_type, styles in self.css_styles.items():
            all_css.append(styles["css"])

        return "\n".join(all_css)

    def generate_complete_html_document(self, formatted_content: Dict, title: str = "EAF Document") -> str:
        """Genera un documento HTML completo."""

        html_parts = []

        # HTML header
        html_parts.append(f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
{formatted_content['css_styles']}
    </style>
</head>
<body>
    <div class="eaf-document">
        <h1>{title}</h1>
""")

        # Contenido por orden de lectura
        structure_map = sorted(formatted_content["structure_map"], key=lambda x: x["position"][1])

        for item in structure_map:
            content_type = item["type"]
            item_id = item["id"]

            # Buscar el contenido formateado
            formatted_items = formatted_content["formatted_content"].get(content_type, [])
            for formatted_item in formatted_items:
                if formatted_item["original_item"]["block_id"] == item_id:
                    html_parts.append(formatted_item["formatted_html"])
                    break

        # HTML footer
        html_parts.append("""
    </div>
</body>
</html>
""")

        return "\n".join(html_parts)


def main():
    """Demo del generador de formato."""

    # Rutas
    base_path = Path(__file__).parent
    pdf_path = base_path.parent.parent.parent / "shared" / "source" / "EAF-089-2025.pdf"

    print("🎨 INICIANDO GENERACIÓN DE FORMATO ESPECÍFICO")
    print("=" * 60)

    # Detectar tipos de contenido
    detector = ContentTypeDetector(str(pdf_path))
    analysis = detector.analyze_content_types(2)  # Página 2

    # Generar formato
    formatter = FormatGenerator()
    formatted_result = formatter.generate_formatted_content(analysis)

    # Generar documento HTML completo
    html_document = formatter.generate_complete_html_document(
        formatted_result,
        "EAF 089/2025 - Capítulo 1, Página 2"
    )

    # Guardar resultado
    output_path = base_path.parent / "outputs" / "formatted_content" / "page_2_formatted.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_document)

    print(f"💾 HTML formateado guardado en: {output_path}")

    # Guardar JSON de análisis
    json_path = output_path.with_suffix('.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(formatted_result, f, indent=2, ensure_ascii=False)

    print(f"📊 Análisis JSON guardado en: {json_path}")

    # Mostrar estadísticas
    print("\n📈 ESTADÍSTICAS DE FORMATO:")
    for content_type, items in formatted_result["formatted_content"].items():
        print(f"📝 {content_type}: {len(items)} elementos formateados")

    print("\n" + "=" * 60)
    print("✅ GENERACIÓN DE FORMATO COMPLETADA")


if __name__ == "__main__":
    main()