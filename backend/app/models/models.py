import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


class SystemSnapshot(Base):
    __tablename__ = "system_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(String(64), nullable=True, index=True, default="local")
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    cpu_percent = Column(Float, nullable=False)
    cpu_count = Column(Integer, nullable=False)
    cpu_freq_current = Column(Float, nullable=True)
    per_cpu_percent = Column(JSON, nullable=True)

    ram_total = Column(Integer, nullable=False)
    ram_used = Column(Integer, nullable=False)
    ram_available = Column(Integer, nullable=False)
    ram_percent = Column(Float, nullable=False)
    swap_total = Column(Integer, nullable=True)
    swap_used = Column(Integer, nullable=True)
    swap_percent = Column(Float, nullable=True)

    disk_total = Column(Integer, nullable=False)
    disk_used = Column(Integer, nullable=False)
    disk_free = Column(Integer, nullable=False)
    disk_percent = Column(Float, nullable=False)
    disk_io = Column(JSON, nullable=True)

    net_bytes_sent = Column(Integer, nullable=True)
    net_bytes_recv = Column(Integer, nullable=True)
    net_io = Column(JSON, nullable=True)

    hostname = Column(String(255), nullable=True)
    os_name = Column(String(255), nullable=True)
    kernel_version = Column(String(255), nullable=True)
    uptime_seconds = Column(Float, nullable=True)
    load_avg = Column(JSON, nullable=True)
    status = Column(String(50), default="healthy")


class ProcessSnapshot(Base):
    __tablename__ = "process_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(String(64), nullable=True, index=True, default="local")
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    pid = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    cpu_percent = Column(Float, nullable=False)
    memory_percent = Column(Float, nullable=False)
    memory_rss = Column(Integer, nullable=True)
    status = Column(String(50), nullable=True)
    username = Column(String(100), nullable=True)
    cmdline = Column(Text, nullable=True)


class ServiceSnapshot(Base):
    __tablename__ = "service_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(String(64), nullable=True, index=True, default="local")
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    name = Column(String(255), nullable=False, index=True)
    load_state = Column(String(50), nullable=True)
    active_state = Column(String(50), nullable=True)
    sub_state = Column(String(50), nullable=True)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=False)
    ports = Column(JSON, nullable=True)


class ContainerSnapshot(Base):
    __tablename__ = "container_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(String(64), nullable=True, index=True, default="local")
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    container_id = Column(String(128), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    image = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    state = Column(String(50), nullable=True)
    health = Column(String(50), nullable=True)
    restart_count = Column(Integer, default=0)
    cpu_percent = Column(Float, default=0.0)
    memory_usage = Column(Integer, default=0)
    memory_limit = Column(Integer, default=0)
    ports = Column(JSON, nullable=True)


class SecurityFinding(Base):
    __tablename__ = "security_findings"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(String(64), nullable=True, index=True, default="local")
    finding_id = Column(String(64), unique=True, index=True)
    severity = Column(String(20), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    affected_component = Column(String(255), nullable=False)
    evidence = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    recommended_fix = Column(Text, nullable=True)
    confidence = Column(Float, default=1.0)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    status = Column(String(50), default="open")


class DiagnosticReport(Base):
    __tablename__ = "diagnostic_reports"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    report_type = Column(String(50), default="performance")
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    metrics_summary = Column(JSON, nullable=True)
    bottlenecks = Column(JSON, nullable=True)
    headroom = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    assumptions = Column(Text, nullable=True)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String(64), unique=True, index=True)
    title = Column(String(255), nullable=False)
    severity = Column(String(20), nullable=False)
    status = Column(String(50), default="open")
    description = Column(Text, nullable=False)
    started_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    ai_analysis = Column(Text, nullable=True)
    context_data = Column(JSON, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    actor = Column(String(100), default="operator")
    action_type = Column(String(100), nullable=False)
    target = Column(String(255), nullable=False)
    parameters = Column(JSON, nullable=True)
    status = Column(String(50), nullable=False)
    output = Column(Text, nullable=True)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    email = Column(String(255), unique=True, nullable=True)
    role = Column(String(50), default="admin")
    is_active = Column(Boolean, default=True)
    pi_user_id = Column(String(100), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    sampling_interval = Column(Integer, default=5)
    ollama_url = Column(String(255), default="http://127.0.0.1:11434")
    ollama_model = Column(String(100), default="qwen3:4b")
    data_retention_hours = Column(Integer, default=72)
    notify_email = Column(Boolean, default=False)
    notify_incidents = Column(Boolean, default=True)


class ApprovedAction(Base):
    __tablename__ = "approved_actions"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(String(64), nullable=True, index=True, default="local")
    action_id = Column(String(64), unique=True, index=True)
    action_type = Column(String(100), nullable=False)
    target = Column(String(255), nullable=False)
    command_preview = Column(Text, nullable=False)
    requested_at = Column(DateTime(timezone=True), default=utc_now)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="pending")
    result_output = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    level = Column(String(20), default="info")
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)


class RegisteredAgent(Base):
    __tablename__ = "registered_agents"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(64), unique=True, index=True)
    hostname = Column(String(255), nullable=False)
    os_info = Column(String(255), nullable=True)
    ip_address = Column(String(100), nullable=True)
    registered_at = Column(DateTime(timezone=True), default=utc_now)
    last_heartbeat = Column(DateTime(timezone=True), default=utc_now)
    status = Column(String(50), default="online")
    capabilities = Column(JSON, nullable=True)
    auth_token_hash = Column(String(255), nullable=False)


class ManagedServer(Base):
    __tablename__ = "managed_servers"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(String(64), unique=True, index=True)
    name = Column(String(255), nullable=False)
    connection_type = Column(String(50), default="ssh")  # "ssh" or "agent"
    hostname = Column(String(255), nullable=False)
    ssh_port = Column(Integer, default=22)
    username = Column(String(100), default="root")
    auth_method = Column(String(50), default="password")  # "password", "private_key", "agent"
    encrypted_credential = Column(Text, nullable=True)  # Fernet encrypted password or private key
    encrypted_passphrase = Column(Text, nullable=True)  # Fernet encrypted passphrase
    timeout_seconds = Column(Integer, default=10)
    environment = Column(String(50), default="production")  # production, staging, development
    organization = Column(String(100), default="default")
    tags = Column(JSON, default=list)

    # Host key verification
    host_key_fingerprint = Column(String(255), nullable=True)
    host_key_type = Column(String(50), nullable=True)
    is_host_key_trusted = Column(Boolean, default=False)

    # Monitoring state
    status = Column(String(50), default="disconnected")  # online, offline, untrusted_host_key, auth_failed, disconnected
    last_connected_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    polling_interval = Column(Integer, default=30)  # seconds

    # Cached discovery details
    system_info = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

