"""
Azure Key Vault integration for EnvCLI.
"""

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from typing import Dict, Optional
from .env_manager import EnvManager

class AzureKeyVaultSync:
    """Azure Key Vault secrets synchronization."""

    def __init__(self, vault_url: Optional[str] = None):
        self.vault_url = vault_url or self._get_vault_url()
        if not self.vault_url:
            raise ValueError("Azure Key Vault URL required. Set AZURE_KEYVAULT_URL environment variable.")

        try:
            credential = DefaultAzureCredential()
            self.client = SecretClient(vault_url=self.vault_url, credential=credential)
        except Exception as e:
            raise Exception(f"Failed to initialize Azure Key Vault client: {e}")

    def push(self, profile: str, prefix: str = "") -> bool:
        """Push profile to Azure Key Vault."""
        manager = EnvManager(profile)
        env_vars = manager.load_env()

        try:
            for key, value in env_vars.items():
                secret_name = f"{prefix}{key}" if prefix else key
                # Azure Key Vault secret names have restrictions
                secret_name = secret_name.replace('_', '-').lower()[:63]

                self.client.set_secret(secret_name, value)
            return True
        except Exception as e:
            print(f"Azure Key Vault push failed: {e}")
            return False

    def pull(self, profile: str, prefix: str = "") -> bool:
        """Pull from Azure Key Vault to profile."""
        try:
            env_vars = {}

            # List all secrets
            secrets = self.client.list_properties_of_secrets()

            for secret_property in secrets:
                secret_name = secret_property.name

                # Apply prefix filter
                if prefix and not secret_name.startswith(prefix):
                    continue

                # Remove prefix from key name
                key = secret_name[len(prefix):] if prefix else secret_name

                # Get the secret value
                secret = self.client.get_secret(secret_name)
                env_vars[key] = secret.value

            if env_vars:
                manager = EnvManager(profile)
                manager.save_env(env_vars)
                return True
            return False

        except Exception as e:
            print(f"Azure Key Vault pull failed: {e}")
            return False

    def status(self, profile: str, prefix: str = "") -> Dict[str, str]:
        """Get Azure Key Vault sync status."""
        try:
            manager = EnvManager(profile)
            local_vars = manager.load_env()

            # Count remote secrets
            secrets = list(self.client.list_properties_of_secrets())
            remote_count = len([s for s in secrets if not prefix or s.name.startswith(prefix)])

            return {
                "local_count": str(len(local_vars)),
                "remote_count": str(remote_count),
                "sync_status": "synced" if len(local_vars) == remote_count else "out_of_sync",
                "vault_url": self.vault_url
            }

        except Exception as e:
            return {"error": str(e)}

    def _get_vault_url(self) -> Optional[str]:
        """Get Azure Key Vault URL from environment."""
        import os
        return os.getenv('AZURE_KEYVAULT_URL')
