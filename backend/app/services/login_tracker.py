"""
Login Tracker Service
Handles login history tracking, session management, and session limits
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import Optional, Dict, List
from loguru import logger

from app.models.user import User, LoginHistory, RefreshToken
from app.utils.device_parser import DeviceParser
from app.utils.ip_geolocation import IPGeolocation


class LoginTracker:
    """Service for tracking login attempts and managing sessions"""
    
    # Session limit per user
    MAX_SESSIONS_PER_USER = 2
    
    @staticmethod
    async def record_login_attempt(
        db: Session,
        user_id: int,
        ip_address: Optional[str],
        user_agent: Optional[str],
        success: bool,
        session_id: Optional[str] = None,
        device_token: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> LoginHistory:
        """
        Record a login attempt (success or failure)
        
        Args:
            db: Database session
            user_id: User ID
            ip_address: Client IP address
            user_agent: User-Agent header
            success: Whether login was successful
            session_id: Session ID if available
            device_token: Device token if available
            failure_reason: Reason for failure if success=False
            
        Returns:
            LoginHistory record
        """
        try:
            # Parse device information
            device_info = DeviceParser.parse_user_agent(user_agent)
            
            # Get geolocation
            location = IPGeolocation.get_location(ip_address) if ip_address else {}
            
            # Create login history record
            login_record = LoginHistory(
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                device_type=device_info.get('device_type'),
                os=device_info.get('os'),
                browser=device_info.get('browser'),
                device_name=device_info.get('device_name'),
                location_city=location.get('city'),
                location_region=location.get('region'),
                location_country=location.get('country'),
                location_lat=location.get('lat'),
                location_lon=location.get('lon'),
                session_id=session_id,
                device_token=device_token,
                login_success=success,
                failure_reason=failure_reason if not success else None
            )
            
            db.add(login_record)
            db.commit()
            db.refresh(login_record)
            
            status = "SUCCESS" if success else f"FAILED ({failure_reason})"
            logger.info(f"[LOGIN_TRACKER] Recorded login attempt for user_id={user_id}: {status} from {device_info['device_name']} ({ip_address})")
            
            return login_record
            
        except Exception as e:
            logger.error(f"[LOGIN_TRACKER] Error recording login attempt: {e}")
            db.rollback()
            raise
    
    @staticmethod
    async def enforce_session_limit(
        db: Session,
        user_id: int,
        current_token_id: Optional[int] = None
    ):
        """
        Enforce session limit by revoking oldest sessions
        
        Args:
            db: Database session
            user_id: User ID
            current_token_id: ID of current token to exclude
        """
        try:
            # Get active sessions
            active_sessions = db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False
            ).order_by(desc(RefreshToken.created_at)).all()
            
            # Count valid (non-expired) sessions
            valid_sessions = [s for s in active_sessions if s.is_valid]
            
            logger.info(f"[LOGIN_TRACKER] User {user_id} has {len(valid_sessions)} active sessions (limit: {LoginTracker.MAX_SESSIONS_PER_USER})")
            
            # If limit exceeded, revoke oldest sessions
            if len(valid_sessions) > LoginTracker.MAX_SESSIONS_PER_USER:
                sessions_to_revoke = valid_sessions[LoginTracker.MAX_SESSIONS_PER_USER:]
                
                for session in sessions_to_revoke:
                    if current_token_id and session.id == current_token_id:
                        continue  # Don't revoke current session
                    
                    session.revoked = True
                    logger.info(f"[LOGIN_TRACKER] Auto-revoked session {session.id} for user {user_id} (limit exceeded)")
                
                db.commit()
                logger.info(f"[LOGIN_TRACKER] Revoked {len(sessions_to_revoke)} old sessions for user {user_id}")
        
        except Exception as e:
            logger.error(f"[LOGIN_TRACKER] Error enforcing session limit: {e}")
            db.rollback()
    
    @staticmethod
    async def update_session_info(
        db: Session,
        token_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Update session information (device info, IP, last_used_at)
        
        Args:
            db: Database session
            token_id: Refresh token ID
            ip_address: Client IP address
            user_agent: User-Agent header
        """
        try:
            token = db.query(RefreshToken).filter(RefreshToken.id == token_id).first()
            if not token:
                return
            
            # Update last_used_at
            token.last_used_at = datetime.utcnow()
            
            # Update IP if provided and different
            if ip_address and token.ip_address != ip_address:
                token.ip_address = ip_address
            
            # Update device info if not set or user_agent changed
            if user_agent and (not token.device_name or token.os is None):
                device_info = DeviceParser.parse_user_agent(user_agent)
                token.device_type = device_info.get('device_type')
                token.os = device_info.get('os')
                token.browser = device_info.get('browser')
                token.device_name = device_info.get('device_name')
            
            db.commit()
            
        except Exception as e:
            logger.error(f"[LOGIN_TRACKER] Error updating session info: {e}")
            db.rollback()
    
    @staticmethod
    async def get_login_history(
        db: Session,
        user_id: int,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get login history for a user
        
        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of records to return
            
        Returns:
            List of login history records as dictionaries
        """
        try:
            records = db.query(LoginHistory).filter(
                LoginHistory.user_id == user_id
            ).order_by(desc(LoginHistory.login_time)).limit(limit).all()
            
            return [record.to_dict() for record in records]
            
        except Exception as e:
            logger.error(f"[LOGIN_TRACKER] Error fetching login history: {e}")
            return []
    
    @staticmethod
    async def get_active_sessions(
        db: Session,
        user_id: int
    ) -> List[Dict]:
        """
        Get active sessions for a user
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of active session records as dictionaries
        """
        try:
            sessions = db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False
            ).order_by(desc(RefreshToken.last_used_at)).all()
            
            # Filter to only valid (non-expired) sessions
            valid_sessions = [s for s in sessions if s.is_valid]
            
            # Add geolocation to each session
            result = []
            for session in valid_sessions:
                session_dict = session.to_dict()
                
                # Get location from IP
                if session.ip_address:
                    location = IPGeolocation.get_location(session.ip_address)
                    session_dict['location'] = IPGeolocation.format_location(location)
                    session_dict['location_country'] = location.get('country')
                else:
                    session_dict['location'] = 'Unknown'
                    session_dict['location_country'] = None
                
                result.append(session_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"[LOGIN_TRACKER] Error fetching active sessions: {e}")
            return []
    
    @staticmethod
    async def revoke_session(
        db: Session,
        user_id: int,
        token_id: int
    ) -> bool:
        """
        Revoke a specific session
        
        Args:
            db: Database session
            user_id: User ID (for security check)
            token_id: Token ID to revoke
            
        Returns:
            True if successful, False otherwise
        """
        try:
            token = db.query(RefreshToken).filter(
                RefreshToken.id == token_id,
                RefreshToken.user_id == user_id
            ).first()
            
            if not token:
                logger.warning(f"[LOGIN_TRACKER] Token {token_id} not found for user {user_id}")
                return False
            
            token.revoked = True
            
            # Update logout_time in login_history if we can find matching session
            # This is best-effort, not critical
            try:
                login_record = db.query(LoginHistory).filter(
                    LoginHistory.user_id == user_id,
                    LoginHistory.device_name == token.device_name,
                    LoginHistory.logout_time == None,
                    LoginHistory.login_success == True
                ).order_by(desc(LoginHistory.login_time)).first()
                
                if login_record:
                    login_record.logout_time = datetime.utcnow()
            except:
                pass
            
            db.commit()
            logger.info(f"[LOGIN_TRACKER] Revoked session {token_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"[LOGIN_TRACKER] Error revoking session: {e}")
            db.rollback()
            return False
    
    @staticmethod
    async def revoke_all_other_sessions(
        db: Session,
        user_id: int,
        current_token_id: int
    ) -> int:
        """
        Revoke all sessions except the current one
        
        Args:
            db: Database session
             user_id: User ID
            current_token_id: Current token ID to keep
            
        Returns:
            Number of sessions revoked
        """
        try:
            sessions = db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.id != current_token_id,
                RefreshToken.revoked == False
            ).all()
            
            count = 0
            for session in sessions:
                session.revoked = True
                count += 1
            
            db.commit()
            logger.info(f"[LOGIN_TRACKER] Revoked {count} sessions for user {user_id} (kept session {current_token_id})")
            return count
            
        except Exception as e:
            logger.error(f"[LOGIN_TRACKER] Error revoking all sessions: {e}")
            db.rollback()
            return 0
