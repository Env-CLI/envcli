"""
Kubernetes integration for EnvCLI.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from .env_manager import EnvManager

class KubernetesSecretSync:
    """Kubernetes Secrets synchronization."""

    def __init__(self, namespace: str = "default", config_path: Optional[str] = None):
        try:
            if config_path:
                config.load_kube_config(config_path)
            else:
                config.load_kube_config()  # Load default config

            self.v1 = client.CoreV1Api()
            self.namespace = namespace
        except Exception as e:
            raise Exception(f"Failed to initialize Kubernetes client: {e}")

    def push(self, profile: str, secret_name: str) -> bool:
        """Push profile to Kubernetes secret."""
        manager = EnvManager(profile)
        env_vars = manager.load_env()

        # Convert env vars to secret data (base64 encoded automatically by k8s client)
        secret_data = {}
        for key, value in env_vars.items():
            secret_data[key] = value

        secret = client.V1Secret(
            api_version="v1",
            kind="Secret",
            metadata=client.V1ObjectMeta(name=secret_name),
            type="Opaque",
            data=secret_data
        )

        try:
            # Try to create, if exists, update
            try:
                self.v1.create_namespaced_secret(self.namespace, secret)
            except ApiException as e:
                if e.status == 409:  # Already exists
                    self.v1.replace_namespaced_secret(secret_name, self.namespace, secret)
                else:
                    raise
            return True
        except ApiException as e:
            print(f"Kubernetes secret push failed: {e}")
            return False

    def pull(self, profile: str, secret_name: str) -> bool:
        """Pull from Kubernetes secret to profile."""
        try:
            secret = self.v1.read_namespaced_secret(secret_name, self.namespace)

            if not secret.data:
                return False

            # Decode secret data
            env_vars = {}
            for key, value in secret.data.items():
                # Kubernetes returns bytes, decode to string
                if isinstance(value, bytes):
                    env_vars[key] = value.decode('utf-8')
                else:
                    env_vars[key] = value

            manager = EnvManager(profile)
            manager.save_env(env_vars)
            return True

        except ApiException as e:
            print(f"Kubernetes secret pull failed: {e}")
            return False

    def status(self, profile: str, secret_name: str) -> Dict[str, str]:
        """Get Kubernetes secret sync status."""
        try:
            manager = EnvManager(profile)
            local_vars = manager.load_env()

            try:
                secret = self.v1.read_namespaced_secret(secret_name, self.namespace)
                remote_count = len(secret.data) if secret.data else 0

                return {
                    "local_count": str(len(local_vars)),
                    "remote_count": str(remote_count),
                    "sync_status": "synced" if len(local_vars) == remote_count else "out_of_sync",
                    "namespace": self.namespace
                }
            except ApiException:
                return {
                    "local_count": str(len(local_vars)),
                    "remote_count": "0",
                    "sync_status": "not_found_in_k8s",
                    "namespace": self.namespace
                }

        except Exception as e:
            return {"error": str(e)}

    def list_secrets(self) -> List[str]:
        """List all secrets in namespace."""
        try:
            secrets = self.v1.list_namespaced_secret(self.namespace)
            return [secret.metadata.name for secret in secrets.items]
        except ApiException as e:
            print(f"Failed to list secrets: {e}")
            return []

class KubernetesConfigMapSync:
    """Kubernetes ConfigMap synchronization for non-sensitive data."""

    def __init__(self, namespace: str = "default", config_path: Optional[str] = None):
        try:
            if config_path:
                config.load_kube_config(config_path)
            else:
                config.load_kube_config()

            self.v1 = client.CoreV1Api()
            self.namespace = namespace
        except Exception as e:
            raise Exception(f"Failed to initialize Kubernetes client: {e}")

    def push(self, profile: str, configmap_name: str, exclude_secrets: bool = True) -> bool:
        """Push profile to Kubernetes ConfigMap (non-sensitive vars only)."""
        manager = EnvManager(profile)
        env_vars = manager.load_env()

        # Filter out sensitive variables if requested
        if exclude_secrets:
            filtered_vars = {}
            for key, value in env_vars.items():
                if not self._is_sensitive_key(key):
                    filtered_vars[key] = value
            env_vars = filtered_vars

        configmap = client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            metadata=client.V1ObjectMeta(name=configmap_name),
            data=env_vars
        )

        try:
            try:
                self.v1.create_namespaced_config_map(self.namespace, configmap)
            except ApiException as e:
                if e.status == 409:  # Already exists
                    self.v1.replace_namespaced_config_map(configmap_name, self.namespace, configmap)
                else:
                    raise
            return True
        except ApiException as e:
            print(f"Kubernetes ConfigMap push failed: {e}")
            return False

    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key contains sensitive information."""
        sensitive_keywords = ['secret', 'key', 'token', 'password', 'auth', 'credential']
        return any(keyword in key.lower() for keyword in sensitive_keywords)
