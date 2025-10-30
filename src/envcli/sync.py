import boto3
import requests
from typing import Dict, List, Optional
from .env_manager import EnvManager
from .config import CONFIG_DIR

class RemoteSync:
    """Base class for remote sync services."""

    def push(self, profile: str, path: str) -> bool:
        """Push profile to remote service."""
        raise NotImplementedError

    def pull(self, profile: str, path: str) -> bool:
        """Pull profile from remote service."""
        raise NotImplementedError

    def status(self, profile: str, path: str) -> Dict[str, str]:
        """Get sync status."""
        raise NotImplementedError

class AWSSSMSync(RemoteSync):
    """AWS Systems Manager Parameter Store sync."""

    def __init__(self):
        self.client = boto3.client('ssm')

    def push(self, profile: str, path: str) -> bool:
        """Push profile to SSM Parameter Store."""
        manager = EnvManager(profile)
        env_vars = manager.load_env()

        try:
            # Delete existing parameters first
            self._delete_parameters_recursive(path)

            # Put new parameters
            for key, value in env_vars.items():
                param_name = f"{path}/{key}"
                self.client.put_parameter(
                    Name=param_name,
                    Value=value,
                    Type='SecureString',
                    Overwrite=True
                )
            return True
        except Exception as e:
            print(f"AWS SSM push failed: {e}")
            return False

    def pull(self, profile: str, path: str) -> bool:
        """Pull profile from SSM Parameter Store."""
        try:
            # Get all parameters under the path
            paginator = self.client.get_paginator('get_parameters_by_path')
            page_iterator = paginator.paginate(
                Path=path,
                Recursive=True,
                WithDecryption=True
            )

            env_vars = {}
            for page in page_iterator:
                for param in page['Parameters']:
                    # Extract key from parameter name
                    key = param['Name'].replace(f"{path}/", "", 1)
                    env_vars[key] = param['Value']

            if env_vars:
                manager = EnvManager(profile)
                manager.save_env(env_vars)
                return True
            return False
        except Exception as e:
            print(f"AWS SSM pull failed: {e}")
            return False

    def status(self, profile: str, path: str) -> Dict[str, str]:
        """Get SSM sync status."""
        try:
            # Check local profile
            manager = EnvManager(profile)
            local_vars = manager.load_env()

            # Check remote parameters
            paginator = self.client.get_paginator('get_parameters_by_path')
            page_iterator = paginator.paginate(
                Path=path,
                Recursive=True,
                WithDecryption=True
            )

            remote_vars = {}
            for page in page_iterator:
                for param in page['Parameters']:
                    key = param['Name'].replace(f"{path}/", "", 1)
                    remote_vars[key] = param['Value']

            # Compare
            added = set(remote_vars.keys()) - set(local_vars.keys())
            removed = set(local_vars.keys()) - set(remote_vars.keys())
            changed = {k for k in local_vars.keys() & remote_vars.keys()
                      if local_vars[k] != remote_vars[k]}

            status = {
                "local_count": str(len(local_vars)),
                "remote_count": str(len(remote_vars)),
                "sync_status": "synced" if not (added or removed or changed) else "out_of_sync"
            }

            if added or removed or changed:
                status["differences"] = f"Added: {len(added)}, Removed: {len(removed)}, Changed: {len(changed)}"

            return status

        except Exception as e:
            return {"error": str(e)}

    def _delete_parameters_recursive(self, path: str):
        """Delete all parameters under a path."""
        try:
            paginator = self.client.get_paginator('get_parameters_by_path')
            page_iterator = paginator.paginate(Path=path, Recursive=True)

            param_names = []
            for page in page_iterator:
                for param in page['Parameters']:
                    param_names.append(param['Name'])

            # Delete in batches of 10 (AWS limit)
            for i in range(0, len(param_names), 10):
                batch = param_names[i:i+10]
                self.client.delete_parameters(Names=batch)
        except Exception:
            pass  # Parameters might not exist

class GitHubSecretsSync(RemoteSync):
    """GitHub Actions Secrets sync with proper libsodium encryption."""

    def __init__(self, token: Optional[str] = None, repo: Optional[str] = None):
        try:
            from nacl import encoding, public
        except ImportError:
            raise ImportError("PyNaCl is required for GitHub secrets encryption. Install with: pip install PyNaCl")

        self.token = token or self._get_token()
        self.repo = repo or self._get_repo()
        if not self.token or not self.repo:
            raise ValueError("GitHub token and repository required. Set GITHUB_TOKEN and GITHUB_REPOSITORY environment variables.")

        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        # Get repository public key for encryption
        self.public_key_data = self._get_public_key()
        self.public_key = public.PublicKey(self.public_key_data['key'], encoding.Base64Encoder)

    def push(self, profile: str, path: str) -> bool:
        """Push profile to GitHub secrets with proper encryption."""
        from nacl import encoding, public

        manager = EnvManager(profile)
        env_vars = manager.load_env()

        try:
            for key, value in env_vars.items():
                # Encrypt the secret value
                encrypted = self._encrypt_secret(value)

                response = requests.put(
                    f'https://api.github.com/repos/{self.repo}/actions/secrets/{key}',
                    headers=self.headers,
                    json={
                        'encrypted_value': encrypted,
                        'key_id': self.public_key_data['key_id']
                    }
                )
                response.raise_for_status()
            return True
        except Exception as e:
            print(f"GitHub secrets push failed: {e}")
            return False

    def pull(self, profile: str, path: str) -> bool:
        """Pull is not supported for GitHub secrets (one-way)."""
        print("Pull not supported for GitHub secrets")
        return False

    def status(self, profile: str, path: str) -> Dict[str, str]:
        """Get GitHub secrets status."""
        try:
            response = requests.get(
                f'https://api.github.com/repos/{self.repo}/actions/secrets',
                headers=self.headers
            )
            response.raise_for_status()
            secrets = response.json()['secrets']

            manager = EnvManager(profile)
            local_vars = manager.load_env()

            return {
                "local_count": str(len(local_vars)),
                "remote_count": str(len(secrets)),
                "sync_status": "encrypted_sync",  # Values are encrypted, can't compare
                "encryption": "libsodium"
            }
        except Exception as e:
            return {"error": str(e)}

    def _encrypt_secret(self, secret_value: str) -> str:
        """Encrypt a secret value using libsodium."""
        from nacl import encoding, public

        # Create a new ephemeral keypair for each secret
        ephemeral_private_key = public.PrivateKey.generate()
        ephemeral_public_key = ephemeral_private_key.public_key

        # Combine repository public key with ephemeral public key
        encrypted_key = ephemeral_private_key.seal(self.public_key, encoding.Base64Encoder)

        # Encrypt the secret value
        box = public.SealedBox(ephemeral_public_key)
        encrypted_value = box.encrypt(secret_value.encode(), encoding.Base64Encoder)

        # Combine encrypted key and encrypted value
        return encrypted_key.decode() + encrypted_value.decode()

    def _get_public_key(self) -> Dict[str, str]:
        """Get repository public key for secret encryption."""
        response = requests.get(
            f'https://api.github.com/repos/{self.repo}/actions/secrets/public-key',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def _get_token(self) -> str:
        """Get GitHub token from environment."""
        import os
        return os.getenv('GITHUB_TOKEN', '')

    def _get_repo(self) -> str:
        """Get GitHub repo from environment."""
        import os
        return os.getenv('GITHUB_REPOSITORY', '')

class HashiCorpVaultSync(RemoteSync):
    """HashiCorp Vault KV secrets sync."""

    def __init__(self, url: str = None, token: str = None, mount_point: str = "secret"):
        import hvac
        self.url = url or self._get_url()
        self.token = token or self._get_token()
        self.mount_point = mount_point

        if not self.url or not self.token:
            raise ValueError("Vault URL and token required. Set VAULT_ADDR and VAULT_TOKEN environment variables.")

        self.client = hvac.Client(url=self.url, token=self.token)

        if not self.client.is_authenticated():
            raise ValueError("Failed to authenticate with Vault")

    def push(self, profile: str, path: str) -> bool:
        """Push profile to Vault KV secrets."""
        manager = EnvManager(profile)
        env_vars = manager.load_env()

        try:
            # Write to Vault
            full_path = f"{self.mount_point}/data/{path}"
            self.client.secrets.kv.v2.create_or_update_secret_version(
                path=path,
                secret=env_vars,
                mount_point=self.mount_point
            )
            return True
        except Exception as e:
            print(f"Vault push failed: {e}")
            return False

    def pull(self, profile: str, path: str) -> bool:
        """Pull profile from Vault KV secrets."""
        try:
            # Read from Vault
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.mount_point
            )

            if 'data' in response and 'data' in response['data']:
                env_vars = response['data']['data']
                manager = EnvManager(profile)
                manager.save_env(env_vars)
                return True
            return False
        except Exception as e:
            print(f"Vault pull failed: {e}")
            return False

    def status(self, profile: str, path: str) -> Dict[str, str]:
        """Get Vault sync status."""
        try:
            manager = EnvManager(profile)
            local_vars = manager.load_env()

            # Check if secret exists in Vault
            try:
                response = self.client.secrets.kv.v2.read_secret_version(
                    path=path,
                    mount_point=self.mount_point
                )
                remote_vars = response['data']['data'] if 'data' in response and 'data' in response['data'] else {}

                return {
                    "local_count": str(len(local_vars)),
                    "remote_count": str(len(remote_vars)),
                    "sync_status": "synced" if local_vars == remote_vars else "out_of_sync"
                }
            except Exception:
                return {
                    "local_count": str(len(local_vars)),
                    "remote_count": "0",
                    "sync_status": "not_found_in_vault"
                }
        except Exception as e:
            return {"error": str(e)}

    def _get_url(self) -> str:
        """Get Vault URL from environment."""
        import os
        return os.getenv('VAULT_ADDR', '')

    def _get_token(self) -> str:
        """Get Vault token from environment."""
        import os
        return os.getenv('VAULT_TOKEN', '')

def get_sync_service(service: str, **kwargs) -> RemoteSync:
    """Factory function for sync services."""
    if service.lower() == 'aws_ssm':
        return AWSSSMSync()
    elif service.lower() == 'github_secrets':
        return GitHubSecretsSync(**kwargs)
    elif service.lower() == 'vault':
        return HashiCorpVaultSync(**kwargs)
    elif service.lower() == 'k8s_secret':
        from .kubernetes_integration import KubernetesSecretSync
        return KubernetesSecretSync(**kwargs)
    elif service.lower() == 'k8s_configmap':
        from .kubernetes_integration import KubernetesConfigMapSync
        return KubernetesConfigMapSync(**kwargs)
    elif service.lower() == 'azure_kv':
        from .azure_integration import AzureKeyVaultSync
        return AzureKeyVaultSync(**kwargs)
    elif service.lower() == 'gcp_sm':
        from .gcp_integration import GCPSecretManagerSync
        return GCPSecretManagerSync(**kwargs)
    else:
        raise ValueError(f"Unsupported sync service: {service}")
