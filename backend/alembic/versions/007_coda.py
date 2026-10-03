"""007: tabelle, tipi e funzioni della coda Procrastinate."""
from alembic import op
from procrastinate.schema import SchemaManager

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Lo schema è quello della versione di Procrastinate in requirements.txt.
    # Va al driver così com'è: i `%` si raddoppiano perché non sono parametri.
    op.get_bind().exec_driver_sql(SchemaManager.get_schema().replace("%", "%%"))


def downgrade() -> None:
    op.execute(
        "DROP TABLE procrastinate_events, procrastinate_periodic_defers, "
        "procrastinate_jobs, procrastinate_workers CASCADE"
    )
    op.execute(
        """
        DO $$
        DECLARE funzione regprocedure;
        BEGIN
            FOR funzione IN
                SELECT oid FROM pg_proc
                WHERE proname LIKE 'procrastinate\\_%'
                  AND pronamespace = current_schema()::regnamespace
            LOOP
                EXECUTE 'DROP FUNCTION ' || funzione || ' CASCADE';
            END LOOP;
        END $$
        """
    )
    op.execute(
        "DROP TYPE procrastinate_job_to_defer_v1, procrastinate_job_event_type, "
        "procrastinate_job_status CASCADE"
    )
