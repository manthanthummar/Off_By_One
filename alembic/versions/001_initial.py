"""001_initial

Revision ID: 001_initial
Revises: 
Create Date: 2026-09-19 09:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JSONType = sa.JSON().with_variant(postgresql.JSONB, "postgresql")


def upgrade() -> None:
    op.create_table(
        "farms",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("owner", sa.String(255), server_default="", nullable=False),
        sa.Column("phone", sa.String(64), server_default="", nullable=False),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lon", sa.Float(), nullable=True),
        sa.Column("budget_inr", sa.Float(), server_default="5000.0", nullable=False),
        sa.Column("plots", JSONType, nullable=False),
    )

    op.create_table(
        "soil_readings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("farm_id", sa.String(64), index=True, nullable=False),
        sa.Column("plot_id", sa.String(64), server_default="plot-1", nullable=False),
        sa.Column("moisture_pct", sa.Float(), nullable=False),
        sa.Column("nitrogen_ppm", sa.Float(), nullable=True),
        sa.Column("ph", sa.Float(), nullable=True),
        sa.Column("temp_c", sa.Float(), nullable=True),
        sa.Column("ts", sa.DateTime(timezone=True), index=True, nullable=False),
    )

    op.create_table(
        "weather_readings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("farm_id", sa.String(64), index=True, nullable=False),
        sa.Column("temp_c", sa.Float(), nullable=True),
        sa.Column("humidity_pct", sa.Float(), nullable=False),
        sa.Column("canopy_wet", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("rain_24h_mm", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("wind_kph", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("evaporation_mm", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("forecast", JSONType, nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), index=True, nullable=False),
    )

    op.create_table(
        "drone_readings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("farm_id", sa.String(64), index=True, nullable=False),
        sa.Column("plot_id", sa.String(64), server_default="plot-1", nullable=False),
        sa.Column("ndvi", sa.Float(), nullable=False),
        sa.Column("ndvi_prev", sa.Float(), nullable=True),
        sa.Column("anomaly_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("anomaly_signature", sa.String(255), server_default="", nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), index=True, nullable=False),
    )

    op.create_table(
        "risks",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("farm_id", sa.String(64), index=True, nullable=False),
        sa.Column("plot_id", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("evidence", JSONType, nullable=False),
        sa.Column("status", sa.String(32), server_default="open", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "plans",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("farm_id", sa.String(64), index=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_cost_inr", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("budget_inr", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("weather_rationale", JSONType, nullable=False),
        sa.Column("advice", sa.Text(), server_default="", nullable=False),
        sa.Column("advice_source", sa.String(32), server_default="offline", nullable=False),
    )

    op.create_table(
        "actions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("plan_id", sa.String(64), index=True, server_default="", nullable=False),
        sa.Column("farm_id", sa.String(64), index=True, nullable=False),
        sa.Column("plot_id", sa.String(64), nullable=False),
        sa.Column("risk_id", sa.String(64), index=True, nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("what", sa.Text(), nullable=False),
        sa.Column("when", sa.DateTime(timezone=True), nullable=False),
        sa.Column("where_text", sa.String(255), server_default="", nullable=False),
        sa.Column("cost_inr", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("status", sa.String(32), server_default="planned", nullable=False),
        sa.Column("requires_expert_approval", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("rationale", sa.Text(), server_default="", nullable=False),
        sa.Column("safety_notes", JSONType, nullable=False),
        sa.Column("hold_reason", sa.String(64), nullable=True),
        sa.Column("hold_notified", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("deferred_until", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("farm_id", sa.String(64), index=True, nullable=False),
        sa.Column("action_id", sa.String(64), index=True, nullable=False),
        sa.Column("plot_id", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), server_default="pending", nullable=False),
        sa.Column("due", sa.DateTime(timezone=True), nullable=False),
        sa.Column("requires_expert_approval", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "escalations",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("farm_id", sa.String(64), index=True, nullable=False),
        sa.Column("action_id", sa.String(64), index=True, nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), server_default="pending", nullable=False),
        sa.Column("advice", sa.Text(), server_default="", nullable=False),
        sa.Column("resolved_by", sa.String(128), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "sms_alerts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("farm_id", sa.String(64), index=True, nullable=False),
        sa.Column("action_id", sa.String(64), nullable=True),
        sa.Column("to_phone", sa.String(64), server_default="", nullable=False),
        sa.Column("message", sa.String(160), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), index=True, nullable=False),
    )

    op.create_table(
        "trace_entries",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("run_id", sa.String(64), index=True, nullable=False),
        sa.Column("farm_id", sa.String(64), index=True, nullable=False),
        sa.Column("agent", sa.String(64), nullable=False),
        sa.Column("input_summary", sa.Text(), server_default="", nullable=False),
        sa.Column("output_summary", sa.Text(), server_default="", nullable=False),
        sa.Column("latency_ms", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("output_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), index=True, nullable=False),
    )


def downgrade() -> None:
    for table in (
        "trace_entries", "sms_alerts", "escalations", "tasks",
        "actions", "plans", "risks", "drone_readings",
        "weather_readings", "soil_readings", "farms"
    ):
        op.drop_table(table)
