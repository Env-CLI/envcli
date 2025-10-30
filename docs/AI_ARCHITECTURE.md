# AI Provider Architecture

## System Overview

```bash
┌─────────────────────────────────────────────────────────────┐
│                         EnvCLI User                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ CLI Commands
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      CLI Layer (cli.py)                      │
│  • envcli ai enable --provider <name>                        │
│  • envcli ai config --show                                   │
│  • envcli ai analyze --profile <name>                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │
┌─────────────────────────▼───────────────────────────────────┐
│              AI Assistant (ai_assistant.py)                  │
│  • Manages AI configuration                                  │
│  • Coordinates provider usage                                │
│  • Generates recommendations                                 │
│  • Handles pattern-based analysis                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ Provider Factory
                          │
┌─────────────────────────▼───────────────────────────────────┐
│           Provider Factory (ai_providers.py)                 │
│                                                              │
│  get_provider(name, **kwargs) -> AIProvider                  │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        │                 │                 │
┌───────▼────────┐ ┌──────▼──────┐ ┌───────▼────────┐
│  OpenAI        │ │  Anthropic  │ │    Google      │
│  Provider      │ │  Provider   │ │    Provider    │
│                │ │             │ │                │
│ • GPT-4o       │ │ • Claude 3.5│ │ • Gemini 1.5   │
│ • GPT-4        │ │ • Claude 3  │ │ • Gemini Pro   │
│ • GPT-3.5      │ │ • Opus      │ │ • Flash        │
└────────────────┘ └─────────────┘ └────────────────┘
        │                 │                 │
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                          │ HTTPS API Calls
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼────────┐ ┌──────▼──────┐ ┌───────▼────────┐
│ OpenAI API     │ │Anthropic API│ │  Google API    │
│ api.openai.com │ │api.anthropic│ │generativelang. │
└────────────────┘ └─────────────┘ └────────────────┘


┌────────────────────────────────────────────────────────────┐
│              Local Providers (No API Calls)                 │
│                                                             │
│  ┌──────────────────┐         ┌──────────────────┐        │
│  │     Ollama       │         │ Pattern Matching │        │
│  │    Provider      │         │    Provider      │        │
│  │                  │         │                  │        │
│  │ • Llama 3.2      │         │ • Rule-based     │        │
│  │ • Mistral        │         │ • No AI needed   │        │
│  │ • CodeLlama      │         │ • 100% local     │        │
│  │ • Custom models  │         │ • Always works   │        │
│  └────────┬─────────┘         └──────────────────┘        │
│           │                                                 │
│           │ HTTP (localhost:11434)                         │
│           │                                                 │
│  ┌────────▼─────────┐                                      │
│  │  Ollama Server   │                                      │
│  │  (Local Process) │                                      │
│  └──────────────────┘                                      │
└────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. User Initiates Analysis

```bash
User runs: envcli ai analyze --profile dev
```

### 2. CLI Layer Processing

```python
# cli.py
@ai_app.command("analyze")
def ai_analyze(profile: str):
    ai = AIAssistant()
    recommendations = ai.generate_recommendations(profile)
    # Display results
```

### 3. AI Assistant Coordination

```python
# ai_assistant.py
class AIAssistant:
    def generate_recommendations(self, profile: str):
        # Load environment variables
        env_vars = manager.load_env()
        
        # Create metadata (NO SECRETS!)
        metadata = {
            "variable_count": len(env_vars),
            "variable_names": list(env_vars.keys()),
            "patterns": self._analyze_patterns(env_vars)
        }
        
        # Get AI analysis from provider
        if self.provider:
            ai_analysis = self.provider.analyze_metadata(
                metadata, 
                context=f"Profile: {profile}"
            )
        
        return {
            "pattern_analysis": pattern_results,
            "ai_analysis": ai_analysis,
            "provider": self.provider.get_provider_name()
        }
```

### 4. Provider Processing

```python
# ai_providers.py
class OpenAIProvider(AIProvider):
    def analyze_metadata(self, metadata: Dict, context: str) -> str:
        # Build prompt with metadata only
        prompt = self._build_prompt(metadata, context)
        
        # Call OpenAI API
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "Expert in env vars..."},
                    {"role": "user", "content": prompt}
                ]
            }
        )
        
        return response.json()["choices"][0]["message"]["content"]
```

## Configuration Flow

### Setting Up a Provider

```bash
┌──────────────────────────────────────────────────────────┐
│ 1. User sets API key                                      │
│    export OPENAI_API_KEY="sk-..."                         │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│ 2. User configures provider                               │
│    envcli ai config --provider openai                     │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│ 3. AI Assistant validates provider                        │
│    • Creates provider instance                            │
│    • Checks is_available()                                │
│    • Tests configuration                                  │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│ 4. Configuration saved                                    │
│    ~/.envcli/ai_config.json                               │
│    {                                                      │
│      "enabled": true,                                     │
│      "provider": "openai",                                │
│      "model": "gpt-4o-mini"                               │
│    }                                                      │
└───────────────────────────────────────────────────────────┘
```

## Provider Interface

All providers implement the same interface:

```python
class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def analyze_metadata(self, metadata: Dict[str, Any], context: str) -> str:
        """
        Analyze metadata and return recommendations.
        
        Args:
            metadata: Environment variable metadata (NO SECRETS)
            context: Analysis context (profile name, etc.)
            
        Returns:
            Analysis results as markdown string
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return human-readable provider name."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is properly configured and available."""
        pass
```

## Security Architecture

### What Gets Sent to AI Providers

```bash
┌─────────────────────────────────────────────────────────┐
│              Environment Variables                       │
│                                                          │
│  DATABASE_URL = "postgres://user:pass@host/db"          │
│  API_KEY = "sk-secret123"                               │
│  DEBUG = "true"                                          │
│  PORT = "8080"                                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Metadata Extraction
                     │ (NO VALUES!)
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    Metadata Only                         │
│                                                          │
│  {                                                       │
│    "variable_count": 4,                                  │
│    "variable_names": [                                   │
│      "DATABASE_URL",                                     │
│      "API_KEY",                                          │
│      "DEBUG",                                            │
│      "PORT"                                              │
│    ],                                                    │
│    "patterns": {                                         │
│      "uppercase_ratio": 0.75,                            │
│      "has_secrets": true,                                │
│      "avg_length": 10.5                                  │
│    },                                                    │
│    "prefixes": ["DATABASE", "API"]                       │
│  }                                                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Sent to AI Provider
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  AI Provider API                         │
│                                                          │
│  ✓ Receives: Variable names, counts, patterns           │
│  ✗ Never receives: Actual values, secrets, passwords    │
└─────────────────────────────────────────────────────────┘
```

### Local-Only Options

For maximum privacy:

1. **Pattern Matching**: 100% local, no network calls
2. **Ollama**: 100% local, runs on your machine

```bash
┌─────────────────────────────────────────────────────────┐
│                    Your Machine                          │
│                                                          │
│  ┌──────────────┐         ┌──────────────┐             │
│  │   EnvCLI     │────────▶│   Ollama     │             │
│  │              │         │   Server     │             │
│  └──────────────┘         └──────────────┘             │
│                                                          │
│  No data leaves your machine!                           │
└─────────────────────────────────────────────────────────┘
```

## Provider Selection Logic

```python
def _get_provider(self) -> Optional[AIProvider]:
    """Get the configured AI provider."""
    if not self.enabled:
        return None
    
    provider_name = self.config.get("provider", "pattern-matching")
    model = self.config.get("model")
    
    try:
        # Try to create provider
        if model:
            provider = get_provider(provider_name, model=model)
        else:
            provider = get_provider(provider_name)
        
        # Verify it's available
        if not provider.is_available():
            # Fallback to pattern matching
            return get_provider("pattern-matching")
        
        return provider
    except Exception:
        # Fallback to pattern matching
        return get_provider("pattern-matching")
```

## Error Handling

```bash
┌─────────────────────────────────────────────────────────┐
│ User runs: envcli ai analyze                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ Try configured provider (e.g., OpenAI)                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ├─ Success ──────────────────────────┐
                     │                                     │
                     └─ Failure                            │
                         │                                 │
                         ▼                                 │
                ┌────────────────────┐                     │
                │ Fallback to        │                     │
                │ Pattern Matching   │                     │
                └────────┬───────────┘                     │
                         │                                 │
                         └─────────────────────────────────┤
                                                           │
                                                           ▼
                                              ┌────────────────────┐
                                              │ Return results     │
                                              │ to user            │
                                              └────────────────────┘
```

## Extension Points

To add a new provider:

1. Create a new class inheriting from `AIProvider`
2. Implement the three required methods
3. Add to the provider factory dictionary
4. Update documentation

```python
class MyCustomProvider(AIProvider):
    def get_provider_name(self) -> str:
        return "My Custom Provider"
    
    def is_available(self) -> bool:
        return True  # Check if configured
    
    def analyze_metadata(self, metadata: Dict, context: str) -> str:
        # Your implementation
        return "Analysis results"

# Add to factory
providers = {
    # ... existing providers ...
    "custom": MyCustomProvider
}
```

## Performance Considerations

- **Pattern Matching**: Instant (< 1ms)
- **Ollama**: 1-10 seconds (depends on model size)
- **Cloud APIs**: 1-5 seconds (network latency + processing)

## Caching Strategy (Future)

```bash
┌─────────────────────────────────────────────────────────┐
│ 1. Generate metadata hash                                │
│    hash = sha256(metadata)                               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Check cache                                           │
│    if hash in cache: return cached_result                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Call AI provider                                      │
│    result = provider.analyze_metadata(...)               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 4. Cache result                                          │
│    cache[hash] = result                                  │
└─────────────────────────────────────────────────────────┘
```
