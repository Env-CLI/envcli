"""
Google Cloud Secret Manager integration for EnvCLI.
"""

from google.cloud import secretmanager
from typing import Dict, Optional
from .env_manager import EnvManager

class GCPSecretManagerSync:
    """Google Cloud Secret Manager synchronization."""

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or self._get_project_id()
        if not self.project_id:
            raise ValueError("GCP Project ID required. Set GOOGLE_CLOUD_PROJECT environment variable.")

        try:
            self.client = secretmanager.SecretManagerServiceClient()
            self.parent = f"projects/{self.project_id}"
        except Exception as e:
            raise Exception(f"Failed to initialize GCP Secret Manager client: {e}")

    def push(self, profile: str, prefix: str = "") -> bool:
        """Push profile to GCP Secret Manager."""
        manager = EnvManager(profile)
        env_vars = manager.load_env()

        try:
            for key, value in env_vars.items():
                secret_id = f"{prefix}{key}" if prefix else key

                # Create or update secret
                secret_name = self.client.secret_path(self.project_id, secret_id)

                try:
                    # Try to create the secret
                    secret = self.client.create_secret(
                        request={
                            "parent": self.parent,
                            "secret_id": secret_id,
                            "secret": {"replication": {"automatic": {}}}
                        }
                    )
                except Exception:
                    # Secret already exists, get its name
                    pass

                # Add a new version
                self.client.add_secret_version(
                    request={
                        "parent": secret_name,
                        "payload": {"data": value.encode("UTF-8")}
                    }
                )

            return True
        except Exception as e:
            print(f"GCP Secret Manager push failed: {e}")
            return False

    def pull(self, profile: str, prefix: str = "") -> bool:
        """Pull from GCP Secret Manager to profile."""
        try:
            env_vars = {}

            # List all secrets
            for secret in self.client.list_secrets(request={"parent": self.parent}):
                secret_id = secret.name.split('/')[-1]

                # Apply prefix filter
                if prefix and not secret_id.startswith(prefix):
                    continue

                # Remove prefix from key name
                key = secret_id[len(prefix):] if prefix else secret_id

                # Get the latest version
                try:
                    version = self.client.access_secret_version(
                        request={"name": f"{secret.name}/versions/latest"}
                    )
                    env_vars[key] = version.payload.data.decode("UTF-8")
                except Exception:
                    # Skip secrets that can't be accessed
                    continue

            if env_vars:
                manager = EnvManager(profile)
                manager.save_env(env_vars)
                return True
            return False

        except Exception as e:
            print(f"GCP Secret Manager pull failed: {e}")
            return False

    def status(self, profile: str, prefix: str = "") -> Dict[str, str]:
        """Get GCP Secret Manager sync status."""
        try:
            manager = EnvManager(profile)
            local_vars = manager.load_env()

            # Count remote secrets
            secrets = list(self.client.list_secrets(request={"parent": self.parent}))
            remote_count = len([s for s in secrets if not prefix or s.name.split('/')[-1].startswith(prefix)])

            return {
                "local_count": str(len(local_vars)),
                "remote_count": str(remote_count),
                "sync_status": "synced" if len(local_vars) == remote_count else "out_of_sync",
                "project_id": self.project_id
            }

        except Exception as e:
            return {"error": str(e)}

    def _get_project_id(self) -> Optional[str]:
        """Get GCP Project ID from environment."""
        import os
        return os.getenv('GOOGLE_CLOUD_PROJECT')
