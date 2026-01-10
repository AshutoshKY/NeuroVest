"""
Utility for decrypting AES-encrypted auth payloads from frontend
Matches the frontend encryption in api.ts
"""
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
from loguru import logger
from typing import Optional, Dict, Any


class AESDecryptor:
    """Decrypt AES payloads encrypted by frontend"""
    
    def __init__(self, secret_key: str):
        """
        Initialize with secret key (same as frontend's publicKey)
        
        Args:
            secret_key: The secret used for AES encryption (from frontend's publicKey)
        """
        self.secret_key = secret_key
    
    def decrypt_field(self, encrypted_value: str) -> Optional[str]:
        """
        Decrypt a single AES-encrypted field
        Frontend uses CryptoJS.AES.encrypt which outputs base64
        
        Args:
            encrypted_value: Base64-encoded encrypted string from frontend
            
        Returns:
            Decrypted plaintext or None if decryption fails
        """
        try:
            # CryptoJS outputs: "Salted__" + salt (8 bytes) + ciphertext
            # Format: base64(Salted__ + salt + ciphertext)
            import hashlib
            from Crypto.Protocol.KDF import PBKDF2
            
            # Decode base64
            encrypted_bytes = base64.b64decode(encrypted_value)
            
            # Check for "Salted__" prefix (CryptoJS format)
            if encrypted_bytes[:8] != b'Salted__':
                logger.warning("[DECRYPT] Missing 'Salted__' prefix")
                return None
            
            # Extract salt (next 8 bytes)
            salt = encrypted_bytes[8:16]
            ciphertext = encrypted_bytes[16:]
            
            # Derive key and IV from password + salt (OpenSSL EVP_BytesToKey compatible)
            key_iv = self._derive_key_and_iv(self.secret_key.encode(), salt)
            key = key_iv[:32]  # 256-bit key
            iv = key_iv[32:48]  # 128-bit IV
            
            # Decrypt with AES-256-CBC
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
            
            return decrypted.decode('utf-8')
            
        except Exception as e:
            logger.error(f"[DECRYPT] AES decryption failed: {e}")
            return None
    
    def _derive_key_and_iv(self, password: bytes, salt: bytes, key_length: int = 32, iv_length: int = 16) -> bytes:
        """
        Derive key and IV using MD5 (OpenSSL EVP_BytesToKey compatible)
        This matches CryptoJS behavior
        """
        d = d_i = b''
        while len(d) < key_length + iv_length:
            d_i = hashlib.md5(d_i + password + salt).digest()  # nosec
            d += d_i
        return d[:key_length + iv_length]
    
    def decrypt_auth_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt all encrypted fields in auth payload
        
        Args:
            payload: Dict with encrypted fields and *_encrypted flags
            
        Returns:
            Dict with decrypted plaintext fields
        """
        decrypted_payload = {}
        
        # Fields that might be encrypted
        sensitive_fields = ['email', 'password', 'current_password', 'new_password', 'full_name', 'display_name']
        
        for field in sensitive_fields:
            if f"{field}_encrypted" in payload and payload.get(f"{field}_encrypted"):
                # Field is encrypted, decrypt it
                encrypted_value = payload.get(field)
                if encrypted_value:
                    decrypted_value = self.decrypt_field(encrypted_value)
                    if decrypted_value:
                        decrypted_payload[field] = decrypted_value
                        logger.debug(f"[DECRYPT] Decrypted {field}")
                    else:
                        logger.error(f"[DECRYPT] Failed to decrypt {field}")
                        # Keep encrypted value for debugging
                        decrypted_payload[field] = encrypted_value
            else:
                # Field is not encrypted, pass through
                if field in payload:
                    decrypted_payload[field] = payload[field]
        
        # Pass through non-sensitive fields
        for key, value in payload.items():
            if not key.endswith('_encrypted') and key not in sensitive_fields:
                decrypted_payload[key] = value
        
        return decrypted_payload


# Create singleton with key from encryption service
from app.services.encryption_service import get_encryption_service

def get_aes_decryptor() -> AESDecryptor:
    """Get AES decryptor instance using the public key as secret"""
    encryption_service = get_encryption_service()
    # Use the full PEM as the passphrase (same as frontend)
    public_key_pem = encryption_service.get_public_key_pem()
    
    return AESDecryptor(public_key_pem)
