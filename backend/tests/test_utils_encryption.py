from app.utils.aes_decryption import AESDecryptor
from unittest.mock import MagicMock

def test_aes_decryptor_init():
    """Test initialization"""
    decryptor = AESDecryptor("secret_key")
    assert decryptor.secret_key == "secret_key"

def test_decrypt_fail_on_garbage():
    """Test safe handling of invalid input"""
    decryptor = AESDecryptor("secret_key")
    result = decryptor.decrypt_field("invalid_base64_string")
    assert result is None
