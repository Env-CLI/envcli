# AI Provider Quick Reference Card

## 🚀 Quick Setup

### Pattern Matching (Default - No Setup)

```bash
envcli ai enable
envcli ai analyze
```

### OpenAI

```bash
export OPENAI_API_KEY="sk-..."
envcli ai enable --provider openai
envcli ai analyze
```

### Anthropic

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
envcli ai enable --provider anthropic
envcli ai analyze
```

### Google

```bash
export GOOGLE_API_KEY="AIza..."
envcli ai enable --provider google
envcli ai analyze
```

### Ollama

```bash
ollama serve
envcli ai enable --provider ollama
envcli ai analyze
```

## 📋 Common Commands

| Command | Description |
|---------|-------------|
| `envcli ai config --show` | View current configuration |
| `envcli ai config --provider <name>` | Switch provider |
| `envcli ai enable --provider <name>` | Enable with provider |
| `envcli ai disable` | Disable AI features |
| `envcli ai analyze` | Analyze current profile |
| `envcli ai analyze --profile <name>` | Analyze specific profile |

## 🔑 API Keys

| Provider | Environment Variable | Get Key From |
|----------|---------------------|--------------|
| OpenAI | `OPENAI_API_KEY` | <https://platform.openai.com/api-keys> |
| Anthropic | `ANTHROPIC_API_KEY` | <https://console.anthropic.com/> |
| Google | `GOOGLE_API_KEY` | <https://makersuite.google.com/app/apikey> |
| Ollama | None (local) | <https://ollama.com/> |
| Pattern | None (local) | Built-in |

## 🎯 Provider Comparison

| Provider | Cost | Privacy | Quality | Speed |
|----------|------|---------|---------|-------|
| Pattern Matching | Free | 100% | Basic | ⚡⚡⚡ |
| Ollama | Free | 100% | Good | ⚡⚡ |
| Google | Free tier | Metadata | Good | ⚡⚡⚡ |
| OpenAI | ~$0.01 | Metadata | Excellent | ⚡⚡⚡ |
| Anthropic | ~$0.02 | Metadata | Excellent | ⚡⚡ |

## 🔐 Security

### ✅ Sent to AI

- Variable names
- Variable count
- Naming patterns
- Prefixes

### ❌ NEVER Sent

- Actual values
- Secrets
- Passwords
- API keys

## 🎨 Models

### OpenAI

```bash
envcli ai config --provider openai --model gpt-4o
envcli ai config --provider openai --model gpt-4o-mini
envcli ai config --provider openai --model gpt-3.5-turbo
```

### Anthropic

```bash
envcli ai config --provider anthropic --model claude-3-5-sonnet-20241022
envcli ai config --provider anthropic --model claude-3-opus-20240229
```

### Google

```bash
envcli ai config --provider google --model gemini-1.5-flash
envcli ai config --provider google --model gemini-1.5-pro
```

### Ollama

```bash
envcli ai config --provider ollama --model llama3.2
envcli ai config --provider ollama --model mistral
envcli ai config --provider ollama --model codellama
```

## 🛠️ Troubleshooting

### Provider Not Available

```bash
# Check status
envcli ai config --show

# Verify API key
echo $OPENAI_API_KEY

# Switch to fallback
envcli ai config --provider pattern-matching
```

### Ollama Not Running

```bash
# Start Ollama
ollama serve

# Verify
curl http://localhost:11434/api/tags

# Pull model
ollama pull llama3.2
```

### API Error

```bash
# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Use local provider
envcli ai config --provider pattern-matching
```

## 📚 Documentation

- **Full Guide**: [docs/AI_PROVIDERS.md](AI_PROVIDERS.md)
- **Quick Start**: [docs/AI_QUICKSTART.md](AI_QUICKSTART.md)
- **Architecture**: [docs/AI_ARCHITECTURE.md](AI_ARCHITECTURE.md)

## 💡 Use Cases

### Development

```bash
envcli ai enable --provider openai
envcli ai analyze --profile dev
```

### Production

```bash
envcli ai enable --provider anthropic --model claude-3-opus-20240229
envcli ai analyze --profile prod
```

### CI/CD

```bash
envcli ai enable --provider pattern-matching
envcli ai analyze --profile staging
```

### Privacy

```bash
ollama serve
envcli ai enable --provider ollama
envcli ai analyze
```

## 🔄 Switching Providers

```bash
# Start with pattern matching
envcli ai enable

# Try OpenAI
envcli ai config --provider openai
envcli ai analyze

# Try Anthropic
envcli ai config --provider anthropic
envcli ai analyze

# Back to local
envcli ai config --provider pattern-matching
```

## 📊 Example Output

```
🤖 AI Analysis for Profile 'dev'
Provider: OpenAI (gpt-4o-mini)

📝 Pattern Analysis:
  ⚠️ Secret variable 'api_key' should be uppercase
    💡 Rename to: API_KEY

🧠 AI-Powered Analysis:

## Recommendations
1. Standardize naming to UPPER_SNAKE_CASE
2. Add prefixes for organization (DB_*, API_*)
3. Ensure secrets are encrypted
```

## ⚡ Quick Tips

1. **Start Free**: Use pattern matching first
2. **Go Local**: Use Ollama for privacy
3. **Best Quality**: Use OpenAI or Anthropic
4. **Free Tier**: Try Google Gemini
5. **Switch Anytime**: No lock-in

## 🎯 Cheat Sheet

```bash
# Setup
export OPENAI_API_KEY="sk-..."
envcli ai enable --provider openai

# Use
envcli ai analyze
envcli ai analyze --profile prod

# Configure
envcli ai config --show
envcli ai config --provider anthropic

# Switch
envcli ai config --provider google
envcli ai config --provider ollama
envcli ai config --provider pattern-matching

# Disable
envcli ai disable
```

---

**Print this card and keep it handy! 📄**
