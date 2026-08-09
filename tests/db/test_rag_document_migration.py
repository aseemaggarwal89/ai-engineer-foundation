import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect


MIGRATION_PATH = Path(__file__).resolve().parents[2].joinpath(
    "app",
    "alembic",
    "versions",
    "1d9b86e3e5c4_create_rag_document_and_chunk_metadata.py",
)


def load_migration_module():
    spec = importlib.util.spec_from_file_location("rag_document_migration", MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def run_migration(fn_name: str, connection):
    module = load_migration_module()
    context = MigrationContext.configure(connection)
    module.op = Operations(context)
    getattr(module, fn_name)()


def test_rag_document_migration_upgrade_creates_expected_schema():
    engine = create_engine("sqlite:///:memory:")

    with engine.begin() as connection:
        run_migration("upgrade", connection)
        inspector = inspect(connection)

        assert {"rag_documents", "rag_document_chunks"} <= set(inspector.get_table_names())

        document_columns = {
            column["name"]: column
            for column in inspector.get_columns("rag_documents")
        }
        chunk_columns = {
            column["name"]: column
            for column in inspector.get_columns("rag_document_chunks")
        }

        assert {
            "id",
            "document_id",
            "title",
            "source",
            "content_type",
            "document_version",
            "checksum",
            "status",
            "chunking_version",
            "embedding_provider",
            "embedding_model",
            "embedding_version",
            "index_version",
            "failure_reason",
            "created_at",
            "updated_at",
            "indexed_at",
            "deleted_at",
        } <= set(document_columns)
        assert document_columns["status"]["nullable"] is False

        assert {
            "id",
            "chunk_id",
            "document_pk",
            "document_id",
            "document_version",
            "chunk_index",
            "text",
            "chunking_version",
            "embedding_provider",
            "embedding_model",
            "embedding_version",
            "index_version",
            "section",
            "page_number",
            "source",
            "created_at",
        } <= set(chunk_columns)
        assert chunk_columns["text"]["nullable"] is False
        assert "embedding" not in chunk_columns
        assert "vector" not in chunk_columns

        document_uniques = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints("rag_documents")
        }
        chunk_uniques = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints("rag_document_chunks")
        }
        chunk_checks = {
            constraint["name"]
            for constraint in inspector.get_check_constraints("rag_document_chunks")
        }

        assert "uq_rag_documents_document_version" in document_uniques
        assert "uq_rag_document_chunks_chunk_id" in chunk_uniques
        assert "uq_rag_document_chunks_position" in chunk_uniques
        assert "ck_rag_document_chunks_index_nonnegative" in chunk_checks
        assert "ck_rag_document_chunks_page_positive" in chunk_checks

        chunk_fks = inspector.get_foreign_keys("rag_document_chunks")
        assert len(chunk_fks) == 1
        assert chunk_fks[0]["referred_table"] == "rag_documents"
        assert chunk_fks[0]["constrained_columns"] == ["document_pk"]
        assert chunk_fks[0]["referred_columns"] == ["id"]

        document_indexes = {
            index["name"]
            for index in inspector.get_indexes("rag_documents")
        }
        chunk_indexes = {
            index["name"]
            for index in inspector.get_indexes("rag_document_chunks")
        }

        assert "ix_rag_documents_document_id" in document_indexes
        assert "ix_rag_documents_document_version" in document_indexes
        assert "ix_rag_documents_checksum" in document_indexes
        assert "ix_rag_documents_status" in document_indexes
        assert "ix_rag_document_chunks_document_pk" in chunk_indexes
        assert "ix_rag_document_chunks_document_version" in chunk_indexes


def test_rag_document_migration_downgrade_removes_rag_schema():
    engine = create_engine("sqlite:///:memory:")

    with engine.begin() as connection:
        run_migration("upgrade", connection)
        run_migration("downgrade", connection)

        inspector = inspect(connection)

        assert "rag_document_chunks" not in inspector.get_table_names()
        assert "rag_documents" not in inspector.get_table_names()
