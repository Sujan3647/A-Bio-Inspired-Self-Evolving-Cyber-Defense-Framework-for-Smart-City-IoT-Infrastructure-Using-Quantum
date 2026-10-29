"""
ImmunoGrid — Database Migration 001: Initial Schema
Creates all base tables for the ImmunoGrid platform.

Run with Alembic:
    alembic upgrade head
    alembic downgrade base
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

# revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all ImmunoGrid tables."""

    # ── Users ────────────────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id',              sa.String(36),   primary_key=True),
        sa.Column('email',           sa.String(255),  nullable=False, unique=True),
        sa.Column('full_name',       sa.String(255),  nullable=False),
        sa.Column('role',            sa.String(50),   nullable=False),
        sa.Column('hashed_password', sa.String(255),  nullable=False),
        sa.Column('ministry',        sa.String(255),  nullable=True),
        sa.Column('department',      sa.String(255),  nullable=True),
        sa.Column('employee_id',     sa.String(50),   nullable=True),
        sa.Column('is_active',       sa.Boolean(),    default=True, nullable=False),
        sa.Column('created_at',      sa.DateTime(),   default=datetime.utcnow, nullable=False),
        sa.Column('last_login',      sa.DateTime(),   nullable=True),
    )
    op.create_index('ix_users_email',       'users', ['email'],      unique=True)
    op.create_index('ix_users_role_active', 'users', ['role','is_active'])

    # ── Devices ───────────────────────────────────────────────────────────────
    op.create_table(
        'devices',
        sa.Column('device_id',        sa.String(100), primary_key=True),
        sa.Column('device_type',      sa.String(50),  nullable=False),
        sa.Column('sector',           sa.String(50),  nullable=False),
        sa.Column('location',         sa.String(100), nullable=False),
        sa.Column('status',           sa.String(20),  default='online', nullable=False),
        sa.Column('message_count',    sa.Integer(),   default=0),
        sa.Column('attack_attempts',  sa.Integer(),   default=0),
        sa.Column('fingerprint_hash', sa.String(64),  nullable=True),
        sa.Column('behavior_profile', JSONB,          nullable=True),
        sa.Column('registered_at',    sa.DateTime(),  default=datetime.utcnow),
        sa.Column('last_seen',        sa.DateTime(),  nullable=True),
    )
    op.create_index('ix_devices_sector_status', 'devices', ['sector','status'])
    op.create_index('ix_devices_type',          'devices', ['device_type'])

    # ── Threat Events ─────────────────────────────────────────────────────────
    op.create_table(
        'threat_events',
        sa.Column('id',              sa.String(36),   primary_key=True),
        sa.Column('attack_type',     sa.String(50),   nullable=False),
        sa.Column('severity',        sa.String(20),   nullable=False),
        sa.Column('target_device',   sa.String(100),  nullable=True),
        sa.Column('target_sector',   sa.String(50),   nullable=False),
        sa.Column('detected_by',     sa.String(50),   nullable=False),
        sa.Column('status',          sa.String(30),   default='detected'),
        sa.Column('confidence',      sa.Float(),      nullable=True),
        sa.Column('morphogenesis',   sa.Boolean(),    default=False),
        sa.Column('blockchain_hash', sa.String(64),   nullable=True),
        sa.Column('attacker_sig',    JSONB,           nullable=True),
        sa.Column('response_actions',JSONB,           nullable=True),
        sa.Column('timestamp',       sa.DateTime(),   default=datetime.utcnow, nullable=False),
    )
    op.create_index('ix_threats_sector_time', 'threat_events', ['target_sector','timestamp'])
    op.create_index('ix_threats_type_time',   'threat_events', ['attack_type','timestamp'])
    op.create_index('ix_threats_severity',    'threat_events', ['severity'])

    # ── Blockchain Records ────────────────────────────────────────────────────
    op.create_table(
        'blockchain_records',
        sa.Column('record_id',     sa.String(30),   primary_key=True),
        sa.Column('block_index',   sa.Integer(),    nullable=False),
        sa.Column('attack_type',   sa.String(50),   nullable=False),
        sa.Column('device_id',     sa.String(100),  nullable=True),
        sa.Column('sector',        sa.String(50),   nullable=False),
        sa.Column('severity',      sa.String(20),   nullable=False),
        sa.Column('data_hash',     sa.String(64),   nullable=False),
        sa.Column('block_hash',    sa.String(64),   nullable=False),
        sa.Column('morphogenesis', sa.Boolean(),    default=False),
        sa.Column('timestamp',     sa.DateTime(),   default=datetime.utcnow, nullable=False),
    )
    op.create_index('ix_bc_block_index', 'blockchain_records', ['block_index'])
    op.create_index('ix_bc_timestamp',   'blockchain_records', ['timestamp'])

    # ── FL Rounds ─────────────────────────────────────────────────────────────
    op.create_table(
        'fl_rounds',
        sa.Column('id',              sa.Integer(),  primary_key=True, autoincrement=True),
        sa.Column('round_number',    sa.Integer(),  unique=True, nullable=False),
        sa.Column('accuracy',        sa.Float(),    nullable=False),
        sa.Column('loss',            sa.Float(),    nullable=False),
        sa.Column('participants',    sa.Integer(),  nullable=False),
        sa.Column('blockchain_hash', sa.String(64), nullable=True),
        sa.Column('imaginations',    sa.Integer(),  default=0),
        sa.Column('timestamp',       sa.DateTime(), default=datetime.utcnow),
    )
    op.create_index('ix_fl_round_number', 'fl_rounds', ['round_number'])

    # ── Key Records ───────────────────────────────────────────────────────────
    op.create_table(
        'key_records',
        sa.Column('key_id',          sa.String(40),   primary_key=True),
        sa.Column('entity_id',       sa.String(100),  nullable=False),
        sa.Column('algorithm',       sa.String(30),   nullable=False),
        sa.Column('key_type',        sa.String(20),   nullable=False),
        sa.Column('public_key_hash', sa.String(64),   nullable=False),
        sa.Column('status',          sa.String(20),   default='active', nullable=False),
        sa.Column('rotated_from',    sa.String(40),   nullable=True),
        sa.Column('created_at',      sa.DateTime(),   default=datetime.utcnow),
        sa.Column('expires_at',      sa.DateTime(),   nullable=False),
    )
    op.create_index('ix_keys_entity_status', 'key_records', ['entity_id','status'])

    # ── Audit Logs ────────────────────────────────────────────────────────────
    op.create_table(
        'audit_logs',
        sa.Column('id',         sa.Integer(),   primary_key=True, autoincrement=True),
        sa.Column('user_id',    sa.String(36),  nullable=True),
        sa.Column('action',     sa.String(100), nullable=False),
        sa.Column('resource',   sa.String(100), nullable=True),
        sa.Column('ip_address', sa.String(45),  nullable=True),
        sa.Column('success',    sa.Boolean(),   default=True),
        sa.Column('details',    JSONB,          nullable=True),
        sa.Column('timestamp',  sa.DateTime(),  default=datetime.utcnow, nullable=False),
    )
    op.create_index('ix_audit_user_time', 'audit_logs', ['user_id','timestamp'])
    op.create_index('ix_audit_action',    'audit_logs', ['action'])


def downgrade() -> None:
    """Drop all ImmunoGrid tables."""
    for table in ['audit_logs','key_records','fl_rounds',
                  'blockchain_records','threat_events','devices','users']:
        op.drop_table(table)
