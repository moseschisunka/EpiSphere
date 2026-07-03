"""data governance lineage and interoperability

Revision ID: 0002_data_governance
Revises: 0001_baseline_schema
Create Date: 2026-07-03
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_data_governance"
down_revision = "0001_baseline_schema"
branch_labels = None
depends_on = None


import_status = sa.Enum("PENDING", "VALIDATED", "COMMITTED", "REJECTED", "FAILED", name="importstatus")
quality_severity = sa.Enum("INFO", "WARNING", "ERROR", name="qualityseverity")


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    case_columns = {col["name"] for col in inspector.get_columns("cases")} if "cases" in tables else set()
    facility_columns = {col["name"] for col in inspector.get_columns("facilities")} if "facilities" in tables else set()

    # The baseline migration intentionally creates Base.metadata. On a fresh install,
    # revision 0001 may already include these newer models, so 0002 becomes a no-op.
    if (
        "source_systems" in tables
        and "import_batches" in tables
        and "dhis2_mappings" in tables
        and "source_system_id" in case_columns
        and "facility_code" in facility_columns
    ):
        return

    if dialect == "postgresql":
        import_status.create(bind, checkfirst=True)
        quality_severity.create(bind, checkfirst=True)

    op.create_table(
        "source_systems",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("system_type", sa.String(length=100), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=True),
        sa.Column("system_metadata", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_source_systems_id"), "source_systems", ["id"], unique=False)
    op.create_index(op.f("ix_source_systems_code"), "source_systems", ["code"], unique=False)
    op.create_index(op.f("ix_source_systems_is_active"), "source_systems", ["is_active"], unique=False)

    op.create_table(
        "import_batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("dataset_type", sa.String(length=100), nullable=False),
        sa.Column("status", import_status, nullable=False),
        sa.Column("source_system_id", sa.Integer(), nullable=True),
        sa.Column("country_id", sa.Integer(), nullable=True),
        sa.Column("disease_id", sa.Integer(), nullable=True),
        sa.Column("uploaded_by", sa.Integer(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), nullable=True),
        sa.Column("committed_at", sa.DateTime(), nullable=True),
        sa.Column("rows_total", sa.Integer(), nullable=True),
        sa.Column("rows_valid", sa.Integer(), nullable=True),
        sa.Column("rows_committed", sa.Integer(), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=True),
        sa.Column("warning_count", sa.Integer(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("batch_metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["country_id"], ["countries.id"]),
        sa.ForeignKeyConstraint(["disease_id"], ["diseases.id"]),
        sa.ForeignKeyConstraint(["source_system_id"], ["source_systems.id"]),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_import_batches_id"), "import_batches", ["id"], unique=False)
    op.create_index(op.f("ix_import_batches_status"), "import_batches", ["status"], unique=False)
    op.create_index(op.f("ix_import_batches_uploaded_at"), "import_batches", ["uploaded_at"], unique=False)
    op.create_index("idx_import_batch_status_uploaded", "import_batches", ["status", "uploaded_at"], unique=False)
    op.create_index("idx_import_batch_scope", "import_batches", ["country_id", "disease_id", "dataset_type"], unique=False)

    op.create_table(
        "import_row_errors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("field_name", sa.String(length=100), nullable=True),
        sa.Column("severity", quality_severity, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("raw_value", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["batch_id"], ["import_batches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_import_row_errors_id"), "import_row_errors", ["id"], unique=False)
    op.create_index(op.f("ix_import_row_errors_batch_id"), "import_row_errors", ["batch_id"], unique=False)
    op.create_index(op.f("ix_import_row_errors_severity"), "import_row_errors", ["severity"], unique=False)
    op.create_index("idx_import_row_error_batch_row", "import_row_errors", ["batch_id", "row_number"], unique=False)

    op.create_table(
        "data_quality_checks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("check_name", sa.String(length=100), nullable=False),
        sa.Column("severity", quality_severity, nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=True),
        sa.Column("threshold", sa.Float(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["batch_id"], ["import_batches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_data_quality_checks_id"), "data_quality_checks", ["id"], unique=False)
    op.create_index(op.f("ix_data_quality_checks_batch_id"), "data_quality_checks", ["batch_id"], unique=False)

    op.create_table(
        "code_systems",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("uri", sa.String(length=500), nullable=True),
        sa.Column("version", sa.String(length=100), nullable=True),
        sa.Column("owner", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "version", name="uq_code_system_name_version"),
    )
    op.create_index(op.f("ix_code_systems_id"), "code_systems", ["id"], unique=False)

    op.create_table(
        "standard_concepts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code_system_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("display", sa.String(length=255), nullable=False),
        sa.Column("concept_type", sa.String(length=100), nullable=False),
        sa.Column("concept_metadata", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["code_system_id"], ["code_systems.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code_system_id", "code", name="uq_standard_concept_code"),
    )
    op.create_index(op.f("ix_standard_concepts_id"), "standard_concepts", ["id"], unique=False)
    op.create_index("idx_standard_concept_type_code", "standard_concepts", ["concept_type", "code"], unique=False)

    op.create_table(
        "concept_maps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_system_id", sa.Integer(), nullable=True),
        sa.Column("source_code", sa.String(length=255), nullable=False),
        sa.Column("source_display", sa.String(length=255), nullable=True),
        sa.Column("target_concept_id", sa.Integer(), nullable=False),
        sa.Column("map_type", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["source_system_id"], ["source_systems.id"]),
        sa.ForeignKeyConstraint(["target_concept_id"], ["standard_concepts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_system_id", "source_code", "target_concept_id", name="uq_concept_map_source_target"),
    )
    op.create_index(op.f("ix_concept_maps_id"), "concept_maps", ["id"], unique=False)

    op.create_table(
        "dhis2_mappings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dataset", sa.String(length=100), nullable=False),
        sa.Column("endpoint_path", sa.String(length=255), nullable=False),
        sa.Column("payload_type", sa.String(length=50), nullable=False),
        sa.Column("required_fields", sa.JSON(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dataset"),
    )
    op.create_index(op.f("ix_dhis2_mappings_id"), "dhis2_mappings", ["id"], unique=False)
    op.create_index(op.f("ix_dhis2_mappings_dataset"), "dhis2_mappings", ["dataset"], unique=False)

    with op.batch_alter_table("cases") as batch:
        batch.add_column(sa.Column("source_system_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("import_batch_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("reporting_period_start", sa.Date(), nullable=True))
        batch.add_column(sa.Column("reporting_period_end", sa.Date(), nullable=True))
        batch.add_column(sa.Column("reporting_level", sa.String(length=50), nullable=True))
        batch.add_column(sa.Column("case_definition", sa.String(length=100), nullable=True))
        batch.add_column(sa.Column("confirmation_status", sa.String(length=50), nullable=True))
        batch.add_column(sa.Column("data_quality_score", sa.Float(), nullable=True))
        batch.create_foreign_key("fk_cases_source_system_id", "source_systems", ["source_system_id"], ["id"])
        batch.create_foreign_key("fk_cases_import_batch_id", "import_batches", ["import_batch_id"], ["id"])
    op.create_index("idx_case_lineage", "cases", ["source_system_id", "import_batch_id"], unique=False)

    with op.batch_alter_table("facilities") as batch:
        batch.add_column(sa.Column("facility_code", sa.String(length=100), nullable=True))
        batch.add_column(sa.Column("latitude", sa.Float(), nullable=True))
        batch.add_column(sa.Column("longitude", sa.Float(), nullable=True))
        batch.add_column(sa.Column("admin1_code", sa.String(length=100), nullable=True))
        batch.add_column(sa.Column("admin2_code", sa.String(length=100), nullable=True))
        batch.create_unique_constraint("uq_facility_country_code", ["country_id", "facility_code"])
    op.create_index("idx_facility_admin", "facilities", ["country_id", "admin1_code", "admin2_code"], unique=False)
    op.create_index("idx_facility_geo", "facilities", ["latitude", "longitude"], unique=False)

    with op.batch_alter_table("interop_logs") as batch:
        batch.add_column(sa.Column("external_id", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("mapping_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_interop_logs_mapping_id", "dhis2_mappings", ["mapping_id"], ["id"])
    op.create_index(op.f("ix_interop_logs_external_id"), "interop_logs", ["external_id"], unique=False)
    op.create_index(op.f("ix_interop_logs_mapping_id"), "interop_logs", ["mapping_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("interop_logs") as batch:
        batch.drop_constraint("fk_interop_logs_mapping_id", type_="foreignkey")
        batch.drop_column("mapping_id")
        batch.drop_column("external_id")

    with op.batch_alter_table("facilities") as batch:
        batch.drop_constraint("uq_facility_country_code", type_="unique")
        batch.drop_column("admin2_code")
        batch.drop_column("admin1_code")
        batch.drop_column("longitude")
        batch.drop_column("latitude")
        batch.drop_column("facility_code")

    with op.batch_alter_table("cases") as batch:
        batch.drop_constraint("fk_cases_import_batch_id", type_="foreignkey")
        batch.drop_constraint("fk_cases_source_system_id", type_="foreignkey")
        batch.drop_column("data_quality_score")
        batch.drop_column("confirmation_status")
        batch.drop_column("case_definition")
        batch.drop_column("reporting_level")
        batch.drop_column("reporting_period_end")
        batch.drop_column("reporting_period_start")
        batch.drop_column("import_batch_id")
        batch.drop_column("source_system_id")

    op.drop_table("dhis2_mappings")
    op.drop_table("concept_maps")
    op.drop_table("standard_concepts")
    op.drop_table("code_systems")
    op.drop_table("data_quality_checks")
    op.drop_table("import_row_errors")
    op.drop_table("import_batches")
    op.drop_table("source_systems")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        quality_severity.drop(bind, checkfirst=True)
        import_status.drop(bind, checkfirst=True)
