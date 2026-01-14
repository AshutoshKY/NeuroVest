"""
Enhanced Audit Log Model for Admin Command Center

Captures comprehensive audit trail for all admin actions with:
- Actor context (who, what role, from where)
- Action details (what, on what, changes made)
- Integrity (payload hash for forensics)
- Result tracking (success/failure)
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import hashlib
import json

from app.core.database import Base


class AuditLog(Base):
    """
    Enhanced audit log for tracking admin actions.
    Immutable after creation - for forensic integrity.
    """
    __tablename__ = "audit_logs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Actor information
    actor_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    actor_role = Column(String(15), nullable=False)  # Role at time of action
    actor_email = Column(String(255), nullable=True)  # For quick reference
    
    # Network context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Action details
    action = Column(String(100), nullable=False, index=True)
    action_category = Column(String(50), nullable=True, index=True)  # user_management, security, config
    target_type = Column(String(50), nullable=True)  # user, ip, toggle, system
    target_id = Column(String(255), nullable=True)
    
    # Payload tracking
    payload_hash = Column(String(64), nullable=True)  # SHA256 of payload
    changes_json = Column(Text, nullable=True)  # JSON of changes
    
    # Result
    success = Column(Boolean, default=True, index=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, actor={self.actor_id}, action={self.action}, success={self.success})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "actor_id": self.actor_id,
            "actor_role": self.actor_role,
            "actor_email": self.actor_email,
            "ip_address": self.ip_address,
            "action": self.action,
            "action_category": self.action_category,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "changes": json.loads(self.changes_json) if self.changes_json else None,
            "success": self.success,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def create_log(
        cls,
        actor_id: int,
        actor_role: str,
        action: str,
        ip_address: str = None,
        actor_email: str = None,
        user_agent: str = None,
        action_category: str = None,
        target_type: str = None,
        target_id: str = None,
        changes: dict = None,
        payload: dict = None,
        success: bool = True,
        error_message: str = None
    ) -> "AuditLog":
        """
        Factory method to create an audit log entry.
        Automatically computes payload hash if payload provided.
        """
        payload_hash = None
        if payload:
            payload_str = json.dumps(payload, sort_keys=True, default=str)
            payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()
        
        changes_json = None
        if changes:
            changes_json = json.dumps(changes, default=str)
        
        return cls(
            actor_id=actor_id,
            actor_role=actor_role,
            actor_email=actor_email,
            ip_address=ip_address,
            user_agent=user_agent,
            action=action,
            action_category=action_category,
            target_type=target_type,
            target_id=str(target_id) if target_id else None,
            payload_hash=payload_hash,
            changes_json=changes_json,
            success=success,
            error_message=error_message
        )


# Action categories for organization
class ActionCategory:
    USER_MANAGEMENT = "user_management"
    SECURITY = "security"
    CONFIG = "config"
    SYSTEM = "system"
    AI = "ai"
    MONITORING = "monitoring"


# Predefined actions for consistency
class AuditAction:
    # User management
    DISABLE_USER = "disable_user"
    ENABLE_USER = "enable_user"
    CHANGE_ROLE = "change_role"
    FORCE_LOGOUT_USER = "force_logout_user"
    
    # Security
    BLACKLIST_IP = "blacklist_ip"
    UNBLOCK_IP = "unblock_ip"
    FORCE_LOGOUT_ALL = "force_logout_all"
    
    # Config/Kill switches
    TOGGLE_KILL_SWITCH = "toggle_kill_switch"
    EMERGENCY_SHUTDOWN = "emergency_shutdown"
    ENABLE_KILL_SWITCH = "enable_kill_switch"
    DISABLE_KILL_SWITCH = "disable_kill_switch"
    MODIFY_TOGGLE = "modify_toggle"
    
    # System
    FLUSH_SESSIONS = "flush_sessions"
    MODIFY_CONFIG = "modify_config"
    
    # Monitoring (read actions - only log if needed)
    VIEW_AUDIT_LOGS = "view_audit_logs"
    EXPORT_DATA = "export_data"
