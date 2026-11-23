from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import datetime


class SystemMetrics(BaseModel):
    timestamp: datetime.datetime
    cpu_percent: float
    cpu_count: int
    cpu_freq_current: Optional[float] = None
    per_cpu_percent: List[float] = Field(default_factory=list)

    ram_total: int
    ram_used: int
    ram_available: int
    ram_percent: float
    swap_total: Optional[int] = 0
    swap_used: Optional[int] = 0
    swap_percent: Optional[float] = 0.0

    disk_total: int
    disk_used: int
    disk_free: int
    disk_percent: float
    disk_io: Optional[Dict[str, Any]] = None

    net_bytes_sent: Optional[int] = 0
    net_bytes_recv: Optional[int] = 0
    net_io: Optional[Dict[str, Any]] = None

    hostname: str
    os_name: str
    kernel_version: str
    uptime_seconds: float
    load_avg: List[float] = Field(default_factory=list)
    status: str = "healthy"


class ProcessInfo(BaseModel):
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_rss: Optional[int] = 0
    status: Optional[str] = "running"
    username: Optional[str] = "unknown"
    cmdline: Optional[str] = ""


class ServiceInfo(BaseModel):
    name: str
    load_state: Optional[str] = "unknown"
    active_state: Optional[str] = "unknown"
    sub_state: Optional[str] = "unknown"
    description: Optional[str] = ""
    is_active: bool = False
    ports: List[int] = Field(default_factory=list)


class PortInfo(BaseModel):
    protocol: str
    local_address: str
    local_port: int
    status: str
    pid: Optional[int] = None
    process_name: Optional[str] = None


class ContainerInfo(BaseModel):
    id: str
    name: str
    image: str
    status: str
    state: Optional[str] = "running"
    health: Optional[str] = "none"
    restart_count: int = 0
    cpu_percent: float = 0.0
    memory_usage: int = 0
    memory_limit: int = 0
    ports: Dict[str, Any] = Field(default_factory=dict)


class SecurityFindingSchema(BaseModel):
    finding_id: str
    severity: str
    category: str
    title: str
    description: str
    affected_component: str
    evidence: Optional[str] = None
    explanation: Optional[str] = None
    recommended_fix: Optional[str] = None
    confidence: float = 1.0
    timestamp: datetime.datetime
    status: str = "open"


class AIChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    include_system_context: bool = True
    server_id: Optional[str] = None
    server_ids: Optional[List[str]] = None
    all_servers: bool = False


class AIChatResponse(BaseModel):
    response: str
    model: str
    evidence: List[str] = Field(default_factory=list)
    suggested_commands: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    is_fallback: bool = False


class ActionPreviewRequest(BaseModel):
    action_type: str
    target: str


class ActionPreviewResponse(BaseModel):
    action_id: str
    action_type: str
    target: str
    command_preview: str
    risk_level: str
    description: str
    expires_at: Optional[str] = None
    requires_approval: bool = True


class ActionApproveRequest(BaseModel):
    action_id: str
    confirmed: bool = True


class ActionExecutionResult(BaseModel):
    action_id: str
    status: str
    output: Optional[str] = None
    error: Optional[str] = None
    executed_at: datetime.datetime


ActionApproveResponse = ActionExecutionResult


class AgentRegisterRequest(BaseModel):
    hostname: str
    os_info: Optional[str] = None
    ip_address: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    shared_secret: str


class AgentRegisterResponse(BaseModel):
    agent_id: str
    token: str
    status: str = "registered"


class AgentHeartbeatRequest(BaseModel):
    agent_id: str
    token: str
    metrics: Optional[Dict[str, Any]] = None


class ReportGenerateRequest(BaseModel):
    report_type: str = "comprehensive"
    format: str = "json"


class CapacityReport(BaseModel):
    timestamp: datetime.datetime
    cpu_headroom_percent: float
    ram_headroom_bytes: int
    ram_headroom_percent: float
    disk_headroom_bytes: int
    disk_headroom_percent: float
    bottlenecks: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    assumptions: str


# --- Managed Remote Server Schemas ---

class ServerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    connection_type: str = Field(default="ssh", pattern="^(ssh|agent)$")
    hostname: str = Field(..., min_length=1, max_length=255)
    ssh_port: int = Field(default=22, ge=1, le=65535)
    username: str = Field(default="root", min_length=1, max_length=100)
    auth_method: str = Field(default="password", pattern="^(password|private_key|agent)$")
    credential: Optional[str] = None  # Password or Private Key in plaintext (will be encrypted immediately)
    passphrase: Optional[str] = None  # Key passphrase
    timeout_seconds: int = Field(default=10, ge=2, le=60)
    environment: str = Field(default="production", max_length=50)
    organization: str = Field(default="default", max_length=100)
    tags: List[str] = Field(default_factory=list)
    auto_trust_host_key: bool = Field(default=False)


class ServerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    hostname: Optional[str] = Field(None, min_length=1, max_length=255)
    ssh_port: Optional[int] = Field(None, ge=1, le=65535)
    username: Optional[str] = Field(None, min_length=1, max_length=100)
    auth_method: Optional[str] = Field(None, pattern="^(password|private_key|agent)$")
    credential: Optional[str] = None
    passphrase: Optional[str] = None
    timeout_seconds: Optional[int] = Field(None, ge=2, le=60)
    environment: Optional[str] = None
    organization: Optional[str] = None
    tags: Optional[List[str]] = None
    polling_interval: Optional[int] = Field(None, ge=5, le=3600)


class ServerResponse(BaseModel):
    server_id: str
    name: str
    connection_type: str
    hostname: str
    ssh_port: int
    username: str
    auth_method: str
    has_credential: bool
    has_passphrase: bool
    timeout_seconds: int
    environment: str
    organization: str
    tags: List[str]
    host_key_fingerprint: Optional[str] = None
    host_key_type: Optional[str] = None
    is_host_key_trusted: bool
    status: str
    last_connected_at: Optional[datetime.datetime] = None
    last_error: Optional[str] = None
    polling_interval: int
    system_info: Optional[Dict[str, Any]] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class ServerTestRequest(BaseModel):
    hostname: str
    ssh_port: int = Field(default=22, ge=1, le=65535)
    username: str = Field(default="root")
    auth_method: str = Field(default="password", pattern="^(password|private_key|agent)$")
    credential: Optional[str] = None
    passphrase: Optional[str] = None
    timeout_seconds: int = Field(default=10, ge=2, le=60)


class ServerTestResponse(BaseModel):
    success: bool
    message: str
    host_key_fingerprint: Optional[str] = None
    host_key_type: Optional[str] = None
    is_host_key_trusted: bool = False
    latency_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


class ServerTrustHostKeyRequest(BaseModel):
    fingerprint: Optional[str] = None

