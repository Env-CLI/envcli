import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from cryptography.fernet import Fernet
from envcli.encryption import get_or_create_key, encrypt_file, decrypt_file, KEY_FILE


class TestEncryption:
    @patch('envcli.encryption.CONFIG_DIR')
    @patch('envcli.encryption.KEY_FILE')
    def test_get_or_create_key_existing(self, mock_key_file, mock_config_dir):
        """Test getting existing encryption key."""
        mock_key_file.exists.return_value = True
        mock_key_file.__str__ = lambda x: "/path/to/key"
        expected_key = b"existing_key_data"

        with patch('builtins.open', mock_open(read_data=expected_key)) as mock_file:
            result = get_or_create_key()

            assert result == expected_key
            mock_file.assert_called_with(mock_key_file, 'rb')

    @patch('envcli.encryption.CONFIG_DIR')
    @patch('envcli.encryption.KEY_FILE')
    @patch('cryptography.fernet.Fernet.generate_key')
    def test_get_or_create_key_new(self, mock_generate_key, mock_key_file, mock_config_dir):
        """Test creating new encryption key when none exists."""
        mock_key_file.exists.return_value = False
        mock_key_file.__str__ = lambda x: "/path/to/key"
        new_key = b"new_generated_key"
        mock_generate_key.return_value = new_key

        with patch('builtins.open', mock_open()) as mock_file:
            result = get_or_create_key()

            assert result == new_key
            # Verify key was written to file
            handle = mock_file()
            handle.write.assert_called_with(new_key)

    @patch('envcli.encryption.get_or_create_key')
    def test_encrypt_file_success(self, mock_get_key, temp_config_dir):
        """Test encrypting a file successfully."""
        # Use a valid Fernet key (32 url-safe base64-encoded bytes)
        from cryptography.fernet import Fernet
        valid_key = Fernet.generate_key()
        mock_get_key.return_value = valid_key

        # Create test file
        test_file = temp_config_dir / "test.txt"
        original_content = b"Hello, World!"
        test_file.write_bytes(original_content)

        encrypt_file(str(test_file))

        # Verify file content changed (was encrypted)
        encrypted_content = test_file.read_bytes()
        assert encrypted_content != original_content
        # Verify it can be decrypted back
        fernet = Fernet(valid_key)
        decrypted = fernet.decrypt(encrypted_content)
        assert decrypted == original_content

    def test_encrypt_file_not_found(self, temp_config_dir):
        """Test encrypting a non-existent file raises error."""
        nonexistent_file = temp_config_dir / "nonexistent.txt"

        with pytest.raises(FileNotFoundError, match="File .* not found"):
            encrypt_file(str(nonexistent_file))

    @patch('envcli.encryption.get_or_create_key')
    def test_decrypt_file_success(self, mock_get_key, temp_config_dir):
        """Test decrypting a file successfully."""
        # Use a valid Fernet key
        from cryptography.fernet import Fernet
        valid_key = Fernet.generate_key()
        mock_get_key.return_value = valid_key

        # Create test file with encrypted content
        test_file = temp_config_dir / "test.txt"
        original_content = b"Hello, World!"
        fernet = Fernet(valid_key)
        encrypted_content = fernet.encrypt(original_content)
        test_file.write_bytes(encrypted_content)

        decrypt_file(str(test_file))

        # Verify file contains decrypted content
        assert test_file.read_bytes() == original_content

    def test_decrypt_file_not_found(self, temp_config_dir):
        """Test decrypting a non-existent file raises error."""
        nonexistent_file = temp_config_dir / "nonexistent.txt"

        with pytest.raises(FileNotFoundError, match="File .* not found"):
            decrypt_file(str(nonexistent_file))

    @patch('envcli.encryption.get_or_create_key')
    def test_decrypt_file_invalid_data(self, mock_get_key, temp_config_dir):
        """Test decrypting a file with invalid encrypted data."""
        # Use a valid Fernet key
        from cryptography.fernet import Fernet
        valid_key = Fernet.generate_key()
        mock_get_key.return_value = valid_key

        # Create test file with invalid encrypted content
        test_file = temp_config_dir / "test.txt"
        invalid_content = b"not_encrypted_data"
        test_file.write_bytes(invalid_content)

        with pytest.raises(ValueError, match="Failed to decrypt file"):
            decrypt_file(str(test_file))

    @patch('envcli.encryption.get_or_create_key')
    def test_encrypt_decrypt_round_trip(self, mock_get_key, temp_config_dir):
        """Test that encrypt followed by decrypt returns original data."""
        # Use real Fernet for round-trip test
        real_key = Fernet.generate_key()
        mock_get_key.return_value = real_key

        # Create test file
        test_file = temp_config_dir / "test.txt"
        original_content = b"This is test content for encryption round-trip."
        test_file.write_bytes(original_content)

        # Encrypt
        encrypt_file(str(test_file))

        # Verify file is encrypted (different from original)
        encrypted_content = test_file.read_bytes()
        assert encrypted_content != original_content

        # Decrypt
        decrypt_file(str(test_file))

        # Verify file is back to original
        decrypted_content = test_file.read_bytes()
        assert decrypted_content == original_content

    @patch('envcli.encryption.get_or_create_key')
    def test_multiple_files_same_key(self, mock_get_key, temp_config_dir):
        """Test that multiple files can be encrypted/decrypted with same key."""
        # Use real Fernet for this test
        real_key = Fernet.generate_key()
        mock_get_key.return_value = real_key

        # Create multiple test files
        files_and_content = [
            (temp_config_dir / "file1.txt", b"Content of file 1"),
            (temp_config_dir / "file2.txt", b"Content of file 2"),
            (temp_config_dir / "file3.txt", b"Content of file 3"),
        ]

        # Write original content
        for file_path, content in files_and_content:
            file_path.write_bytes(content)

        # Encrypt all files
        for file_path, _ in files_and_content:
            encrypt_file(str(file_path))

        # Verify all are encrypted (different from original)
        for file_path, original_content in files_and_content:
            encrypted_content = file_path.read_bytes()
            assert encrypted_content != original_content

        # Decrypt all files
        for file_path, _ in files_and_content:
            decrypt_file(str(file_path))

        # Verify all are back to original
        for file_path, original_content in files_and_content:
            decrypted_content = file_path.read_bytes()
            assert decrypted_content == original_content

    def test_key_file_path(self):
        """Test that key file path is constructed correctly."""
        from envcli.encryption import KEY_FILE
        assert str(KEY_FILE).endswith("key")
        assert ".envcli" in str(KEY_FILE)

    @patch('envcli.encryption.get_or_create_key')
    def test_encrypt_file_empty_file(self, mock_get_key, temp_config_dir):
        """Test encrypting an empty file."""
        from cryptography.fernet import Fernet
        valid_key = Fernet.generate_key()
        mock_get_key.return_value = valid_key

        # Create empty test file
        test_file = temp_config_dir / "empty.txt"
        test_file.write_bytes(b"")

        encrypt_file(str(test_file))

        # Verify file was encrypted
        encrypted_content = test_file.read_bytes()
        assert encrypted_content != b""
        # Verify it can be decrypted
        fernet = Fernet(valid_key)
        decrypted = fernet.decrypt(encrypted_content)
        assert decrypted == b""

    @patch('envcli.encryption.get_or_create_key')
    def test_decrypt_file_empty_encrypted(self, mock_get_key, temp_config_dir):
        """Test decrypting an empty encrypted file."""
        from cryptography.fernet import Fernet
        valid_key = Fernet.generate_key()
        mock_get_key.return_value = valid_key

        # Create test file with encrypted empty content
        test_file = temp_config_dir / "empty_encrypted.txt"
        fernet = Fernet(valid_key)
        encrypted_empty = fernet.encrypt(b"")
        test_file.write_bytes(encrypted_empty)

        decrypt_file(str(test_file))

        assert test_file.read_bytes() == b""
