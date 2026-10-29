"""
ImmunoGrid — Database Migration 002: Honeypot Intelligence Tables
Adds honeypot capture and attacker profiling tables.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from datetime import datetime

revision = '002_add_honeypot'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Honeypot Devices ──────────────────────────────────────────────────────
    op.create_table(
        'honeypot_devices',
        sa.Column('honeypot_id',      sa.String(50),   primary_key=True),
        sa.Column('mimics_device_id', sa.String(100),  nullable=False),
        sa.Column('mimics_sector',    sa.String(50),   nullable=False),
        sa.Column('is_active',        sa.Boolean(),    default=True),
        sa.Column('interactions',     sa.Integer(),    default=0),
        sa.Column('attackers_trapped',sa.Integer(),    default=0),
        sa.Column('created_at',       sa.DateTime(),   default=datetime.utcnow),
        sa.Column('last_interaction', sa.DateTime(),   nullable=True),
        sa.Column('deactivated_at',   sa.DateTime(),   nullable=True),
    )
    op.create_index('ix_hp_sector',  'honeypot_devices', ['mimics_sector'])
    op.create_index('ix_hp_active',  'honeypot_devices', ['is_active'])

    # ── Attacker Profiles ─────────────────────────────────────────────────────
    op.create_table(
        'attacker_profiles',
        sa.Column('attacker_id',    sa.String(64),   primary_key=True),   # SHA-256 hash
        sa.Column('first_seen',     sa.DateTime(),   nullable=False),
        sa.Column('last_seen',      sa.DateTime(),   nullable=False),
        sa.Column('attack_types',   JSONB,           nullable=True),      # ["spoofing","ddos"]
        sa.Column('target_sectors', JSONB,           nullable=True),
        sa.Column('total_attempts', sa.Integer(),    default=0),
        sa.Column('behavioral_sig', JSONB,           nullable=True),
        sa.Column('profile_hash',   sa.String(64),   nullable=True),
        sa.Column('is_active',      sa.Boolean(),    default=True),
        sa.Column('reported_by',    sa.String(50),   nullable=True),
    )
    op.create_index('ix_attacker_last_seen', 'attacker_profiles', ['last_seen'])
    op.create_index('ix_attacker_active',    'attacker_profiles', ['is_active'])

    # ── Intelligence Reports ──────────────────────────────────────────────────
    op.create_table(
        'intelligence_reports',
        sa.Column('report_id',           sa.String(36),  primary_key=True),
        sa.Column('honeypot_id',         sa.String(50),  nullable=False),
        sa.Column('attacker_id',         sa.String(64),  nullable=True),
        sa.Column('attack_types',        JSONB,          nullable=True),
        sa.Column('interaction_count',   sa.Integer(),   default=0),
        sa.Column('recommended_defenses',JSONB,          nullable=True),
        sa.Column('ai_samples_generated',sa.Integer(),   default=0),
        sa.Column('blockchain_entry',    JSONB,          nullable=True),
        sa.Column('generated_at',        sa.DateTime(),  default=datetime.utcnow),
    )
    op.create_index('ix_report_honeypot', 'intelligence_reports', ['honeypot_id'])
    op.create_index('ix_report_time',     'intelligence_reports', ['generated_at'])

    # ── Morphogenesis Events ──────────────────────────────────────────────────
    op.create_table(
        'morphogenesis_events',
        sa.Column('id',            sa.Integer(),   primary_key=True, autoincrement=True),
        sa.Column('triggered_by',  sa.String(36),  nullable=True),   # threat_event.id
        sa.Column('action',        sa.String(50),  nullable=False),
        sa.Column('sector',        sa.String(50),  nullable=True),
        sa.Column('device_id',     sa.String(100), nullable=True),
        sa.Column('old_value',     sa.String(100), nullable=True),
        sa.Column('new_value',     sa.String(100), nullable=True),
        sa.Column('blockchain_tx', sa.String(66),  nullable=True),
        sa.Column('timestamp',     sa.DateTime(),  default=datetime.utcnow, nullable=False),
    )
    op.create_index('ix_morph_action', 'morphogenesis_events', ['action'])
    op.create_index('ix_morph_time',   'morphogenesis_events', ['timestamp'])


def downgrade() -> None:
    for table in ['morphogenesis_events','intelligence_reports',
                  'attacker_profiles','honeypot_devices']:
        op.drop_table(table)
