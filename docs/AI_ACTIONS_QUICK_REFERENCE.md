# AI Safe Actions - Quick Reference Card

## 🚀 Commands

### Get Suggestions

```bash
envcli ai suggest [--profile PROFILE]
```

Analyzes your environment variables and generates actionable improvement suggestions.

**Example:**

```bash
$ envcli ai suggest --profile demo

💡 Found 7 actionable suggestion(s):

1. Rename 'api_key' to 'API_KEY' (uppercase for secrets)
2. Add 'REDIS_' prefix to 'redis_host'
...
```

---

### Preview Changes

```bash
envcli ai apply --preview [--profile PROFILE]
```

Shows exactly what will change **without making any modifications**.

**Example:**

```bash
$ envcli ai apply --preview

1. Rename 'api_key' to 'API_KEY'
   - api_key
   + API_KEY
   Value: [PRESERVED - NOT SHOWN]
```

---

### Apply Changes

```bash
envcli ai apply [--profile PROFILE] [--yes]
```

Applies all AI-suggested improvements. Use `--yes` to skip confirmation.

**Example:**

```bash
$ envcli ai apply --yes

✓ Successfully applied 7 change(s)
💡 Changes have been logged for audit purposes
```

---

### View History

```bash
envcli ai history [--profile PROFILE] [--limit N]
```

Shows audit trail of all applied AI actions.

**Example:**

```bash
$ envcli ai history --limit 5

📜 AI Action History for 'demo'

• Rename 'api_key' to 'API_KEY'
  Applied: 2025-10-28T13:15:53
  Type: rename
```

---

## 🔒 Security

| Feature | Protection |
|---------|-----------|
| **Values** | Never shown in output |
| **AI Analysis** | Only sees variable names |
| **Logs** | No sensitive data recorded |
| **Preview** | Shows `[PRESERVED - NOT SHOWN]` |

---

## 📋 Action Types

### Rename

Standardizes variable naming.

```bash
api_key → API_KEY
DatabasePassword → DATABASE_PASSWORD
```

### Add Prefix

Groups related variables.

```bash
redis_host → REDIS_HOST
smtp_server → EMAIL_SMTP_SERVER
```

---

## 💡 Workflow

```bash
# 1. Get suggestions
envcli ai suggest

# 2. Preview (safe, no changes)
envcli ai apply --preview

# 3. Apply changes
envcli ai apply --yes

# 4. Verify
envcli env list
envcli ai history
```

---

## ⚠️ Best Practices

### Before Applying

```bash
# Export backup
envcli env export backup.env

# Preview changes
envcli ai apply --preview
```

### After Applying

```bash
# Verify values preserved
envcli env list

# Check history
envcli ai history

# Update application code to use new variable names
```

---

## 🎯 Common Scenarios

### Standardize Secrets

```bash
# Before: api_key, DatabasePassword, token
# After:  API_KEY, DATABASE_PASSWORD, TOKEN

envcli ai suggest
envcli ai apply --yes
```

### Organize by Service

```bash
# Before: redis_host, redis_port, db_url, db_pass
# After:  REDIS_HOST, REDIS_PORT, DATABASE_URL, DATABASE_PASSWORD

envcli ai suggest
envcli ai apply --yes
```

### Clean Up Naming

```bash
# Before: Mixed case, inconsistent patterns
# After:  UPPER_SNAKE_CASE, consistent prefixes

envcli ai suggest
envcli ai apply --yes
```

---

## 🔍 Options

### `envcli ai suggest`

- `-p, --profile TEXT` - Profile to analyze (default: current)

### `envcli ai apply`

- `-p, --profile TEXT` - Profile to modify (default: current)
- `--preview` - Preview without applying
- `-y, --yes` - Skip confirmation

### `envcli ai history`

- `-p, --profile TEXT` - Profile to show history for
- `-n, --limit INT` - Number of entries (default: 10)

---

## 📚 Documentation

- **Full Guide:** [AI_SAFE_ACTIONS.md](AI_SAFE_ACTIONS.md)
- **AI Providers:** [AI_PROVIDERS.md](AI_PROVIDERS.md)
- **Quick Start:** [AI_QUICKSTART.md](AI_QUICKSTART.md)

---

## ✅ Quick Test

```bash
# Create test profile
envcli env add api_key "test123" --profile test
envcli env add database_url "postgres://localhost" --profile test

# Get suggestions
envcli ai suggest --profile test

# Preview
envcli ai apply --profile test --preview

# Apply
envcli ai apply --profile test --yes

# Verify
envcli env list --profile test
envcli ai history --profile test
```

---

**Your secrets are safe, your variables are organized!** 🔒✨
