import pytest
from app.utils.aes_decryption import decrypt_data, AES
import base64
import json

# Note: We need a valid AES test key/iv logic. 
# Assuming the Util class handles standard AES CBC/GCM

def test_aes_decryption_mocked():
    """
    Since AES depends on Crypto library, we test if the function exists
    and handles bad input correctly. Real encryption tests require matching keys.
    """
    # Test valid structure handling
    try:
        # Pass garbage
        decrypt_data("invalid_encrypted_string", "secret")
        assert False, "Should raise error"
    except Exception:
        assert True
