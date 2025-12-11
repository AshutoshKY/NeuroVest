"""
Encryption service for sensitive data
Uses RSA for asymmetric encryption of user credentials and personal data
"""
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import base64
from typing import Optional
from loguru import logger
import os


class EncryptionService:
    """Service for encrypting/decrypting sensitive user data"""
    
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self._load_or_generate_keys()
    
    def _load_or_generate_keys(self):
        """Load existing keys or generate new ones"""
        private_key_path = os.getenv("ENCRYPTION_PRIVATE_KEY_PATH", "keys/private_key.pem")
        public_key_path = os.getenv("ENCRYPTION_PUBLIC_KEY_PATH", "keys/public_key.pem")
        
        # Try to load existing keys
        try:
            if os.path.exists(private_key_path):
                with open(private_key_path, "rb") as f:
                    self.private_key = serialization.load_pem_private_key(
                        f.read(),
                        password=None,
                        backend=default_backend()
                    )
                logger.info("[ENCRYPTION] Loaded existing private key")
            
            if os.path.exists(public_key_path):
                with open(public_key_path, "rb") as f:
                    self.public_key = serialization.load_pem_public_key(
                        f.read(),
                        backend=default_backend()
                    )
                logger.info("[ENCRYPTION] Loaded existing public key")
        except Exception as e:
            logger.warning(f"[ENCRYPTION] Could not load keys: {e}")
        
        # Generate new keys if not loaded
        if not self.private_key or not self.public_key:
            self._generate_new_keys()
            self._save_keys(private_key_path, public_key_path)
    
    def _generate_new_keys(self):
        """Generate new RSA key pair"""
        logger.info("[ENCRYPTION] Generating new RSA key pair (2048-bit)")
        
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
    
    def _save_keys(self, private_path: str, public_path: str):
        """Save keys to files"""
        try:
            os.makedirs(os.path.dirname(private_path), exist_ok=True)
            
            # Save private key
            with open(private_path, "wb") as f:
                f.write(
                    self.private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    )
                )
            
            # Save public key
            with open(public_path, "wb") as f:
                f.write(
                    self.public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    )
                )
            
            logger.info(f"[ENCRYPTION] Saved keys to {private_path} and {public_path}")
        except Exception as e:
            logger.error(f"[ENCRYPTION] Could not save keys: {e}")
    
    def get_public_key_pem(self) -> str:
        """Get public key in PEM format for frontend"""
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')
    
    def decrypt(self, encrypted_data_b64: str) -> Optional[str]:
        """
        Decrypt data that was encrypted with public key
        
        Args:
            encrypted_data_b64: Base64-encoded encrypted data from frontend
            
        Returns:
            Decrypted plaintext string, or None if decryption fails
        """
        try:
            # Decode from base64
            encrypted_data = base64.b64decode(encrypted_data_b64)
            
            # Decrypt with private key
            decrypted = self.private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"[ENCRYPTION] Decryption failed: {e}")
            return None
    
    def encrypt_for_frontend(self, plaintext: str) -> str:
        """
        Encrypt data to send to frontend
        (Frontend will decrypt with private key - NOT RECOMMENDED for production)
        This is mainly for demonstration. In practice, backend shouldn't encrypt for frontend.
        """
        try:
            encrypted = self.public_key.encrypt(
                plaintext.encode('utf-8'),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"[ENCRYPTION] Encryption failed: {e}")
            return plaintext  # Fallback to plaintext


# Singleton instance
_encryption_service = EncryptionService()


def get_encryption_service() -> EncryptionService:
    """Get encryption service instance"""
    return _encryption_service
