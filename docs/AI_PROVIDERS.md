# AI Provider Configuration Guide

EnvCLI supports multiple AI providers for intelligent environment variable analysis. Choose the provider that best fits your needs!

## 🤖 Available Providers

### 1. **Pattern Matching (Default)**

- ✅ **No API key required**
- ✅ **Works offline**
- ✅ **Privacy-first** - all analysis happens locally
- ⚠️ Limited to rule-based pattern matching

**Setup:**

```bash
envcli ai enable
# or explicitly
envcli ai enable --provider pattern-matching
```

### 2. **OpenAI (GPT-4, GPT-3.5)**

- 🚀 **Most popular**
- 🎯 **High quality analysis**
- 💰 **Pay-per-use pricing**

**Setup:**

```bash
# Set your API key
export OPENAI_API_KEY="sk-..."

# Enable with default model (gpt-4o-mini)
envcli ai enable --provider openai

# Or specify a model
envcli ai enable --provider openai --model gpt-4o
envcli ai config --provider openai --model gpt-3.5-turbo
```

**Get API Key:** <https://platform.openai.com/api-keys>

### 3. **Anthropic (Claude)**

- 🧠 **Advanced reasoning**
- 🔒 **Strong safety features**
- 📝 **Excellent for detailed analysis**

**Setup:**

```bash
# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Enable with default model (claude-3-5-sonnet)
envcli ai enable --provider anthropic

# Or specify a model
envcli ai config --provider anthropic --model claude-3-5-sonnet-20241022
envcli ai config --provider anthropic --model claude-3-opus-20240229
```

**Get API Key:** <https://console.anthropic.com/>

### 4. **Google (Gemini)**

- ⚡ **Fast responses**
- 💵 **Generous free tier**
- 🌐 **Google's latest AI**

**Setup:**

```bash
# Set your API key
export GOOGLE_API_KEY="AIza..."

# Enable with default model (gemini-1.5-flash)
envcli ai enable --provider google

# Or specify a model
envcli ai config --provider google --model gemini-1.5-pro
envcli ai config --provider google --model gemini-1.5-flash
```

**Get API Key:** <https://makersuite.google.com/app/apikey>

### 5. **Ollama (Local LLMs)** ⭐ Auto-Detects Models

- 🏠 **100% local and private**
- 🆓 **Completely free**
- 🔒 **No data leaves your machine**
- ✨ **Auto-detects available models**
- ⚠️ Requires local setup

**Setup:**

```bash
# Install Ollama (if not already installed)
# macOS/Linux:
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama server
ollama serve

# Pull a model (in another terminal)
ollama pull llama3.2
ollama pull mistral
ollama pull codellama

# Configure EnvCLI (auto-detects best model!)
envcli ai enable --provider ollama

# Or specify a model manually
envcli ai config --provider ollama --model llama3.2

# See available models
envcli ai config --show
```

**✨ New Feature:** Ollama now automatically detects available models! Just enable it and it will pick the best model for you.

**Learn more:** <https://ollama.com/>

## 📋 Quick Start

### Check Current Configuration

```bash
envcli ai config --show
```

Output:

```bash
🤖 AI Configuration

Status: Enabled
Current Provider: openai
Current Model: gpt-4o-mini

Available Providers:
  ✓ openai: OpenAI (gpt-4o-mini) (current)
  ✓ anthropic: Anthropic (claude-3-5-sonnet-20241022)
  ✓ google: Google (gemini-1.5-flash)
  ✗ ollama: Ollama (llama3.2)
  ✓ pattern-matching: Pattern Matching (Local)
```

### Switch Providers

```bash
# Switch to Anthropic
envcli ai config --provider anthropic

# Switch to Google with specific model
envcli ai config --provider google --model gemini-1.5-pro

# Switch back to local pattern matching
envcli ai config --provider pattern-matching
```

### Analyze Environment Variables

```bash
# Analyze current profile
envcli ai analyze

# Analyze specific profile
envcli ai analyze --profile production
```

## 🔐 Security & Privacy

### What Data is Sent?

EnvCLI **NEVER** sends your actual secret values to AI providers. Only metadata is analyzed:

**Sent to AI:**

- Variable names (e.g., `DATABASE_URL`, `API_KEY`)
- Variable count
- Naming patterns
- Prefixes and structure

**NEVER sent:**

- Actual secret values
- Passwords
- API keys
- Tokens
- Any sensitive data

### Example Metadata

```json
{
  "variable_count": 15,
  "variable_names": ["DATABASE_URL", "API_KEY", "DEBUG_MODE"],
  "naming_patterns": {
    "uppercase_ratio": 0.8,
    "has_secrets": true,
    "avg_length": 12.5
  },
  "prefixes": ["DATABASE", "API", "DEBUG"]
}
```

## 💡 Use Cases

### Development Teams

```bash
# Use OpenAI for quick, high-quality analysis
export OPENAI_API_KEY="sk-..."
envcli ai enable --provider openai
envcli ai analyze --profile dev
```

### Enterprise/Compliance

```bash
# Use Anthropic for detailed security analysis
export ANTHROPIC_API_KEY="sk-ant-..."
envcli ai enable --provider anthropic --model claude-3-opus-20240229
envcli ai analyze --profile production
```

### Privacy-Conscious/Offline

```bash
# Use Ollama for 100% local analysis
ollama serve
envcli ai enable --provider ollama --model llama3.2
envcli ai analyze
```

### CI/CD Pipelines

```bash
# Use pattern matching (no API keys needed)
envcli ai enable --provider pattern-matching
envcli ai analyze --profile staging
```

## 🎯 Best Practices

1. **Start with Pattern Matching**: Test the feature without API costs
2. **Use Ollama for Sensitive Projects**: Keep everything local
3. **OpenAI for Speed**: Best balance of speed and quality
4. **Anthropic for Depth**: When you need detailed analysis
5. **Google for Scale**: Generous free tier for high volume

## 🔧 Troubleshooting

### Provider Not Available

```bash
# Check configuration
envcli ai config --show

# Verify API key is set
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY
echo $GOOGLE_API_KEY

# Test Ollama connection
curl http://localhost:11434/api/tags
```

### API Errors

```bash
# Check API key validity
# OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Anthropic
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

### Switch to Fallback

```bash
# If a provider fails, switch to pattern matching
envcli ai config --provider pattern-matching
```

## 📊 Cost Comparison

| Provider | Free Tier | Typical Cost | Speed |
|----------|-----------|--------------|-------|
| Pattern Matching | ✅ Unlimited | $0 | ⚡⚡⚡ |
| Ollama | ✅ Unlimited | $0 | ⚡⚡ |
| Google Gemini | ✅ Generous | ~$0.001/analysis | ⚡⚡⚡ |
| OpenAI GPT-4o-mini | ❌ | ~$0.01/analysis | ⚡⚡⚡ |
| OpenAI GPT-4o | ❌ | ~$0.05/analysis | ⚡⚡ |
| Anthropic Claude | ❌ | ~$0.02/analysis | ⚡⚡ |

## 🚀 Advanced Configuration

### Custom Ollama Models

```bash
# Use specialized models
ollama pull codellama:13b
envcli ai config --provider ollama --model codellama:13b

# Use larger models for better quality
ollama pull llama3.1:70b
envcli ai config --provider ollama --model llama3.1:70b
```

### Environment-Specific Providers

```bash
# Development: Fast and cheap
export OPENAI_API_KEY="sk-..."
envcli ai config --provider openai --model gpt-3.5-turbo

# Production: High quality analysis
export ANTHROPIC_API_KEY="sk-ant-..."
envcli ai config --provider anthropic --model claude-3-opus-20240229
```

## 📚 Additional Resources

- [OpenAI Documentation](https://platform.openai.com/docs)
- [Anthropic Documentation](https://docs.anthropic.com)
- [Google AI Documentation](https://ai.google.dev/docs)
- [Ollama Documentation](https://github.com/ollama/ollama)

## 🤝 Contributing

Want to add support for more providers? Check out `src/envcli/ai_providers.py` and submit a PR!

Potential providers to add:

- Azure OpenAI
- AWS Bedrock
- Cohere
- Hugging Face Inference API
- Local transformers
