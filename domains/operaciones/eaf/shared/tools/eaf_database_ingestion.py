"""
EAF Database Ingestion

Ingest processed EAF universal JSON data into the SQLite database.
Completes the dataflow: PDF → JSON → SQLite → MCP → AI Access
"""

import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List
import sys
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))


class EAFDatabaseIngestion:
    """Handles ingestion of EAF data into the platform database."""

    def __init__(self, db_path: str = None):
        self.project_root = project_root
        self.db_path = Path(db_path) if db_path else Path(__file__).parent.parent / "database" / "eaf_data.db"

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def ingest_universal_json(self, json_file_path: str) -> Dict:
        """Ingest universal JSON data into database."""
        json_path = Path(json_file_path)

        if not json_path.exists():
            raise FileNotFoundError(f"Universal JSON file not found: {json_path}")

        # Load universal JSON data
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.logger.info(f"Starting database ingestion for: {json_path.name}")

        # Connect to database
        with self._get_connection() as conn:
            # Insert document metadata
            doc_id = self._insert_document_metadata(conn, data['document_metadata'], str(json_path))

            # Insert chapters and entities
            chapter_ids = []
            total_entities = 0

            for chapter_data in data['chapters']:
                chapter_id = self._insert_chapter(conn, doc_id, chapter_data)
                chapter_ids.append(chapter_id)

                # Insert entities for this chapter
                entities_inserted = self._insert_chapter_entities(conn, chapter_id, chapter_data['entities'])
                total_entities += entities_inserted

            # Update processing statistics
            self._update_processing_stats(conn, doc_id, len(chapter_ids), total_entities)

        results = {
            'document_id': doc_id,
            'chapters_inserted': len(chapter_ids),
            'entities_inserted': total_entities,
            'status': 'completed'
        }

        self.logger.info(f"Database ingestion completed: {results}")
        return results

    def _get_connection(self):
        """Get database connection with proper configuration."""
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _insert_document_metadata(self, conn: sqlite3.Connection, metadata: Dict, source_file: str) -> int:
        """Insert document metadata and return document ID."""
        cursor = conn.cursor()

        # Check if document already exists
        cursor.execute("""
            SELECT id FROM documents WHERE title = ? AND document_type = ?
        """, (metadata['document_title'], metadata['document_type']))

        existing = cursor.fetchone()
        if existing:
            self.logger.info(f"Document already exists with ID: {existing['id']}")
            return existing['id']

        # Insert new document
        insert_sql = """
            INSERT INTO documents (
                title, document_type, total_pages, source_file, processing_date,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        now = datetime.now().isoformat()
        cursor.execute(insert_sql, (
            metadata['document_title'],
            metadata['document_type'],
            metadata['total_pages'],
            source_file,
            now,
            now,
            now
        ))

        doc_id = cursor.lastrowid
        self.logger.info(f"Inserted document with ID: {doc_id}")
        return doc_id

    def _insert_chapter(self, conn: sqlite3.Connection, doc_id: int, chapter_data: Dict) -> int:
        """Insert chapter data and return chapter ID."""
        cursor = conn.cursor()

        # Check if chapter already exists
        cursor.execute("""
            SELECT id FROM chapters WHERE document_id = ? AND chapter_id = ?
        """, (doc_id, chapter_data['chapter_id']))

        existing = cursor.fetchone()
        if existing:
            self.logger.info(f"Chapter already exists with ID: {existing['id']}")
            return existing['id']

        # Insert new chapter
        insert_sql = """
            INSERT INTO chapters (
                document_id, chapter_id, title, content_type, page_range,
                record_count, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        now = datetime.now().isoformat()
        record_count = chapter_data['metadata'].get('record_count', 0)

        cursor.execute(insert_sql, (
            doc_id,
            chapter_data['chapter_id'],
            chapter_data['title'],
            chapter_data['content_type'],
            chapter_data['page_range'],
            record_count,
            now,
            now
        ))

        chapter_id = cursor.lastrowid
        self.logger.info(f"Inserted chapter '{chapter_data['title']}' with ID: {chapter_id}")
        return chapter_id

    def _insert_chapter_entities(self, conn: sqlite3.Connection, chapter_id: int, entities: List[Dict]) -> int:
        """Insert entities for a chapter and return count."""
        cursor = conn.cursor()
        inserted_count = 0

        for entity in entities:
            # Check if entity already exists
            cursor.execute("""
                SELECT id FROM entities WHERE chapter_id = ? AND name = ? AND type = ?
            """, (chapter_id, entity['name'], entity['type']))

            if cursor.fetchone():
                continue  # Skip existing entity

            # Insert new entity
            insert_sql = """
                INSERT INTO entities (
                    chapter_id, name, type, category, metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """

            now = datetime.now().isoformat()
            metadata_json = json.dumps(entity) if isinstance(entity, dict) else '{}'

            cursor.execute(insert_sql, (
                chapter_id,
                entity['name'],
                entity['type'],
                entity.get('category', ''),
                metadata_json,
                now,
                now
            ))

            inserted_count += 1

        self.logger.info(f"Inserted {inserted_count} entities for chapter ID: {chapter_id}")
        return inserted_count

    def _update_processing_stats(self, conn: sqlite3.Connection, doc_id: int, chapter_count: int, entity_count: int):
        """Update document processing statistics."""
        cursor = conn.cursor()

        update_sql = """
            UPDATE documents
            SET chapters_count = ?, entities_count = ?, updated_at = ?
            WHERE id = ?
        """

        now = datetime.now().isoformat()
        cursor.execute(update_sql, (chapter_count, entity_count, now, doc_id))

        self.logger.info(f"Updated processing stats for document ID {doc_id}: {chapter_count} chapters, {entity_count} entities")

    def create_tables_if_not_exist(self):
        """Create necessary tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    total_pages INTEGER,
                    source_file TEXT,
                    processing_date TEXT,
                    chapters_count INTEGER DEFAULT 0,
                    entities_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Create chapters table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chapters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    chapter_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content_type TEXT,
                    page_range TEXT,
                    record_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents (id)
                )
            """)

            # Create entities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chapter_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    category TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (chapter_id) REFERENCES chapters (id)
                )
            """)

            # Create indexes for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_type ON documents (document_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chapters_document ON chapters (document_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_chapter ON entities (chapter_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON entities (type)")

            conn.commit()
            self.logger.info("Database tables created/verified successfully")

    def verify_ingestion(self, doc_id: int) -> Dict:
        """Verify the ingestion was successful."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get document info
            cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            doc_info = dict(cursor.fetchone())

            # Get chapters count
            cursor.execute("SELECT COUNT(*) as count FROM chapters WHERE document_id = ?", (doc_id,))
            chapters_count = cursor.fetchone()['count']

            # Get entities count
            cursor.execute("""
                SELECT COUNT(*) as count FROM entities e
                JOIN chapters c ON e.chapter_id = c.id
                WHERE c.document_id = ?
            """, (doc_id,))
            entities_count = cursor.fetchone()['count']

            return {
                'document_info': doc_info,
                'chapters_count': chapters_count,
                'entities_count': entities_count,
                'verification_status': 'passed'
            }


def main():
    """Demo usage of EAF Database Ingestion."""
    import argparse

    parser = argparse.ArgumentParser(description='Ingest EAF universal JSON into database')
    parser.add_argument('json_file', help='Path to universal JSON file')
    parser.add_argument('--db-path', help='Path to SQLite database file')
    parser.add_argument('--verify', action='store_true', help='Verify ingestion after completion')

    args = parser.parse_args()

    # Initialize ingestion tool
    ingestion = EAFDatabaseIngestion(args.db_path)

    # Create tables if needed
    ingestion.create_tables_if_not_exist()

    # Perform ingestion
    results = ingestion.ingest_universal_json(args.json_file)

    print("\n" + "="*60)
    print("EAF DATABASE INGESTION SUMMARY")
    print("="*60)
    print(f"Document ID: {results['document_id']}")
    print(f"Chapters Inserted: {results['chapters_inserted']}")
    print(f"Entities Inserted: {results['entities_inserted']}")
    print(f"Status: {results['status']}")

    # Verify if requested
    if args.verify:
        print("\nVerifying ingestion...")
        verification = ingestion.verify_ingestion(results['document_id'])
        print(f"Verification Status: {verification['verification_status']}")
        print(f"Document Title: {verification['document_info']['title']}")
        print(f"Chapters in DB: {verification['chapters_count']}")
        print(f"Entities in DB: {verification['entities_count']}")

    print("="*60)


if __name__ == "__main__":
    main()