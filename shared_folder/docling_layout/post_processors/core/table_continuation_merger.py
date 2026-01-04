"""
Table Continuation Merger

Merges table continuations that span multiple pages into single consolidated tables.

In EAF reports, detailed tables (DETALLE) often continue across pages:
- Table N: Technology header (e.g., "Hidroeléctricas de Pasada")
- Table N+1: Continuation with "Concepto" header (same columns)
- Table N+2: Another continuation (same columns)

This post-processor:
1. Detects continuation patterns
2. Merges rows from continuation tables into base table
3. Marks continuation tables with "is_continuation": true flag
4. Preserves validation and metadata from base table
"""


def apply_table_continuation_merger_to_document(document):
    """
    Merge table continuations in a Docling document.

    Args:
        document: The Docling document object

    Returns:
        int: Number of continuation tables merged
    """
    print("\n" + "=" * 80)
    print("🔧 [TABLE CONTINUATION MERGER] Starting...")
    print("=" * 80)

    tables = document.tables
    if not tables:
        print("⚠️  No tables found in document")
        print("=" * 80 + "\n")
        return 0

    merge_count = 0
    i = 0

    while i < len(tables):
        base_table = tables[i]

        # Skip if already marked as continuation
        if base_table.data.get("is_continuation"):
            i += 1
            continue

        # Look for continuations
        continuations = []
        j = i + 1

        while j < len(tables):
            candidate = tables[j]

            if _is_continuation(candidate, base_table):
                continuations.append(candidate)
                j += 1
            else:
                # Not a continuation, stop looking
                break

        # Merge continuations if found
        if continuations:
            print(f"\n  Table {i}:")
            print(f"    Base: {_get_table_description(base_table)}")

            for cont in continuations:
                print(f"    + Continuation: {_get_table_description(cont)} ({len(cont.data.get('rows', []))} rows)")

            _merge_continuations(base_table, continuations)
            merge_count += len(continuations)

            print(f"    → Merged table: {len(base_table.data.get('rows', []))} total rows")

        i += 1

    print(f"\n✅ [TABLE CONTINUATION MERGER] Merged {merge_count} continuation tables")
    print("=" * 80 + "\n")

    return merge_count


def _is_continuation(candidate, base_table):
    """
    Check if candidate table is a continuation of base table.

    Args:
        candidate: Table to check
        base_table: Base table to compare against

    Returns:
        bool: True if candidate is a continuation
    """
    # Must have data
    if not candidate.data or not base_table.data:
        return False

    # Skip if already marked as continuation
    if candidate.data.get("is_continuation"):
        return False

    # Must have same number of columns
    base_cols = base_table.data.get("num_cols", 0)
    cand_cols = candidate.data.get("num_cols", 0)
    if base_cols != cand_cols or base_cols == 0:
        return False

    # Must have matching headers
    base_headers = base_table.data.get("headers", [])
    cand_headers = candidate.data.get("headers", [])
    if base_headers != cand_headers:
        return False

    # Must be on same or consecutive pages
    if candidate.prov and base_table.prov:
        base_page = base_table.prov[0].page_no
        cand_page = candidate.prov[0].page_no

        # Allow same page or next page only
        if cand_page - base_page > 1:
            return False

    # Must be from same extractor (if specified)
    base_extractor = base_table.data.get("extractor")
    cand_extractor = candidate.data.get("extractor")
    if base_extractor and cand_extractor and base_extractor != cand_extractor:
        return False

    # Candidate should have "Concepto" header (continuation marker)
    # OR have same technology header as base
    if cand_headers and cand_headers[0] not in ["Concepto", base_headers[0]]:
        return False

    return True


def _merge_continuations(base_table, continuations):
    """
    Merge continuation tables into base table.

    Args:
        base_table: Base table to merge into
        continuations: List of continuation tables to merge
    """
    if not continuations:
        return

    base_rows = base_table.data.get("rows", [])

    for cont_table in continuations:
        cont_rows = cont_table.data.get("rows", [])

        # Filter out metadata/header rows
        filtered_rows = []
        for row in cont_rows:
            if not _is_metadata_row(row):
                filtered_rows.append(row)

        # Append to base table
        base_rows.extend(filtered_rows)

        # Mark continuation table
        cont_table.data["is_continuation"] = True
        cont_table.data["merged_into_table"] = base_table.self_ref

    # Update base table metadata
    base_table.data["rows"] = base_rows
    base_table.data["num_rows"] = len(base_rows)

    # Update validation if present
    if "validation" in base_table.data:
        validation = base_table.data["validation"]
        # Add note about merged continuations
        if "warnings" not in validation:
            validation["warnings"] = []
        validation["warnings"].append(f"Merged {len(continuations)} continuation tables")


def _is_metadata_row(row):
    """
    Check if row is a metadata/header row that should be skipped during merge.

    Args:
        row: Table row (list of cell values)

    Returns:
        bool: True if row is metadata
    """
    if not row or len(row) == 0:
        return True

    first_cell = str(row[0]).strip().lower()

    # Metadata patterns
    metadata_patterns = [
        "periodo desde:",
        "fecha:",
        "coordinador eléctrico",
        "programación diaria",
        "sistema eléctrico",
    ]

    for pattern in metadata_patterns:
        if pattern in first_cell:
            return True

    # Empty first cell
    if not first_cell:
        return True

    return False


def _get_table_description(table):
    """
    Get a short description of a table for logging.

    Args:
        table: Table object

    Returns:
        str: Description string
    """
    if not table.data:
        return "No data"

    headers = table.data.get("headers", [])
    rows = table.data.get("rows", [])
    extractor = table.data.get("extractor", "unknown")
    page_no = table.prov[0].page_no if table.prov else "?"

    tech_name = headers[0] if headers else "Unknown"

    # Try to get technology from first data row if header is "Concepto"
    if tech_name == "Concepto" and rows:
        # Look for technology marker in first few rows
        for row in rows[:3]:
            if row and row[0]:
                first_cell = str(row[0]).strip()
                if first_cell and not _is_metadata_row(row):
                    tech_name = first_cell[:30]  # Truncate long names
                    break

    return f"'{tech_name}' (page {page_no}, {len(rows)} rows, {extractor})"
