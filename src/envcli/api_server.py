"""
REST API server for EnvCLI - Programmatic access to all features.
"""

import os
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn

from .env_manager import EnvManager
from .ai_assistant import AIAssistant
from .audit_reporting import AuditReporter
from .policy_engine import PolicyEngine
from .rbac import rbac_manager
from .config import get_current_profile

app = FastAPI(
    title="EnvCLI API",
    description="REST API for EnvCLI - Enterprise Environment Management",
    version="3.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Pydantic models
class EnvVarCreate(BaseModel):
    key: str
    value: str

class ProfileCreate(BaseModel):
    name: str
    source_profile: Optional[str] = None

class SyncRequest(BaseModel):
    service: str
    path: str
    profile: Optional[str] = None

class PolicyCreate(BaseModel):
    type: str
    pattern: Optional[str] = None
    description: str = ""

# Authentication dependency
def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Authenticate user via API token."""
    token = credentials.credentials

    # Simple token validation - in production, use proper JWT/OAuth
    if not token.startswith("envcli_"):
        raise HTTPException(status_code=401, detail="Invalid token")

    # Extract username from token (simplified)
    username = token.replace("envcli_", "").split("_")[0]

    # Check RBAC if enabled
    if rbac_manager.is_enabled():
        # This would validate the token properly in production
        return username

    return username

@app.get("/")
def read_root():
    """API root endpoint."""
    return {
        "name": "EnvCLI API",
        "version": "3.0.0",
        "description": "Enterprise Environment Management API",
        "endpoints": [
            "/profiles",
            "/environments",
            "/sync",
            "/audit",
            "/ai",
            "/policies"
        ]
    }

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0"
    }

# Profile management
@app.get("/profiles")
def list_profiles(current_user: str = Depends(get_current_user)):
    """List all profiles."""
    from .config import list_profiles
    profiles = list_profiles()
    return {"profiles": profiles, "count": len(profiles)}

@app.post("/profiles")
def create_profile(profile: ProfileCreate, current_user: str = Depends(get_current_user)):
    """Create a new profile."""
    from .config import create_profile as create_profile_func

    try:
        create_profile_func(profile.name)
        return {"message": f"Profile '{profile.name}' created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/profiles/{profile_name}")
def get_profile(profile_name: str, current_user: str = Depends(get_current_user)):
    """Get profile details."""
    try:
        manager = EnvManager(profile_name)
        env_vars = manager.load_env()

        # Mask sensitive values
        masked_vars = {}
        for key, value in env_vars.items():
            if any(word in key.lower() for word in ['secret', 'key', 'token', 'password']):
                masked_vars[key] = "***masked***"
            else:
                masked_vars[key] = value

        return {
            "profile": profile_name,
            "variables": masked_vars,
            "count": len(env_vars)
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Profile '{profile_name}' not found")

# Environment variable management
@app.get("/environments/{profile}")
def list_environment_variables(profile: str, current_user: str = Depends(get_current_user)):
    """List environment variables in a profile."""
    try:
        manager = EnvManager(profile)
        env_vars = manager.load_env()

        # Mask sensitive values
        masked_vars = {}
        for key, value in env_vars.items():
            if any(word in key.lower() for word in ['secret', 'key', 'token', 'password']):
                masked_vars[key] = "***masked***"
            else:
                masked_vars[key] = value

        return {
            "profile": profile,
            "variables": masked_vars,
            "count": len(env_vars)
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Profile '{profile}' not found")

@app.post("/environments/{profile}")
def add_environment_variable(profile: str, env_var: EnvVarCreate, current_user: str = Depends(get_current_user)):
    """Add environment variable to profile."""
    try:
        manager = EnvManager(profile)
        manager.add_env(env_var.key, env_var.value)
        return {"message": f"Variable '{env_var.key}' added to profile '{profile}'"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/environments/{profile}/{key}")
def delete_environment_variable(profile: str, key: str, current_user: str = Depends(get_current_user)):
    """Delete environment variable from profile."""
    try:
        manager = EnvManager(profile)
        manager.remove_env(key)
        return {"message": f"Variable '{key}' removed from profile '{profile}'"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Sync operations
@app.post("/sync/push")
def sync_push(request: SyncRequest, current_user: str = Depends(get_current_user)):
    """Push profile to remote service."""
    try:
        from .sync import get_sync_service
        sync_service = get_sync_service(request.service)
        success = sync_service.push(request.profile or get_current_profile(), request.path)

        if success:
            return {"message": f"Successfully pushed to {request.service}"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to push to {request.service}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/sync/pull")
def sync_pull(request: SyncRequest, current_user: str = Depends(get_current_user)):
    """Pull profile from remote service."""
    try:
        from .sync import get_sync_service
        sync_service = get_sync_service(request.service)
        success = sync_service.pull(request.profile or get_current_profile(), request.path)

        if success:
            return {"message": f"Successfully pulled from {request.service}"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to pull from {request.service}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# AI analysis
@app.get("/ai/analyze/{profile}")
def ai_analyze(profile: str, current_user: str = Depends(get_current_user)):
    """Get AI analysis for a profile."""
    try:
        ai = AIAssistant()
        recommendations = ai.generate_recommendations(profile)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Audit reporting
@app.get("/audit/report")
def get_audit_report(format: str = "json", days: int = 30, current_user: str = Depends(get_current_user)):
    """Generate audit report."""
    try:
        reporter = AuditReporter()
        report_path = reporter.generate_compliance_report(format, days)
        return {"report_path": str(report_path), "format": format}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Policy management
@app.post("/policies")
def create_policy(policy: PolicyCreate, current_user: str = Depends(get_current_user)):
    """Create a new policy."""
    try:
        engine = PolicyEngine()

        if policy.type == "required_key":
            engine.add_required_key_policy(policy.pattern, policy.description)
        elif policy.type == "prohibited_pattern":
            engine.add_prohibited_pattern_policy(policy.pattern, policy.description)
        elif policy.type == "naming_convention":
            engine.add_naming_convention_policy(policy.pattern, policy.description)

        return {"message": f"Policy created: {policy.type}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/policies/validate/{profile}")
def validate_profile_policies(profile: str, current_user: str = Depends(get_current_user)):
    """Validate profile against policies."""
    try:
        engine = PolicyEngine()
        result = engine.validate_profile(profile)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def start_api_server(host: str = "127.0.0.1", port: int = 8000):
    """Start the API server."""
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_api_server()
