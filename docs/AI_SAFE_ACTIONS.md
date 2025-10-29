# AI Safe Actions - Apply Recommendations Without Compromising Secrets

## 🔒 Overview

EnvCLI's AI Safe Actions feature allows you to **automatically apply AI-recommended improvements** to your environment variables while **guaranteeing that sensitive values are never exposed or compromised**.

### Key Security Principles

✅ **Values are ALWAYS preserved** - Only variable names are changed  
✅ **No secrets are exposed** - Values are never shown in output  
✅ **Full audit trail** - Every change is logged  
✅ **Preview before apply** - See exactly what will change  
✅ **Atomic operations** - Each change is independent  

---

## 🚀 Quick Start

### 1. Get AI Suggestions

```bash
# Analyze your profile and get actionable suggestions
envcli ai suggest --profile demo

# Output:
# 💡 Found 12 actionable suggestion(s):
# 
# 1. Rename 'api_key' to 'API_KEY' (uppercase for secrets)
#    Type: rename
#    Reason: Secret variables should be uppercase
# 
# 2. Add 'REDIS_' prefix to 'redis_host'
#    Type: add_prefix
#    Reason: Group redis-related variables
```

### 2. Preview Changes

```bash
# See what will change WITHOUT applying
envcli ai apply --profile demo --preview

# Output shows:
#   - api_key
#   + API_KEY
#   Value: [PRESERVED - NOT SHOWN]
```

### 3. Apply Changes

```bash
# Apply all suggestions (with confirmation)
envcli ai apply --profile demo

# Or skip confirmation
envcli ai apply --profile demo --yes
```

### 4. View History

```bash
# See all applied changes
envcli ai history --profile demo
```

---

## 📋 Supported Actions

### 1. **Rename Variables**

Standardizes variable naming conventions.

**Example:**
```
api_key → API_KEY
DatabasePassword → DATABASE_PASSWORD
```

**Use Cases:**
- Convert secrets to uppercase
- Fix mixed case variables
- Standardize naming conventions

### 2. **Add Prefixes**

Groups related variables with common prefixes.

**Example:**
```
redis_host → REDIS_HOST
redis_port → REDIS_PORT
smtp_server → EMAIL_SMTP_SERVER
```

**Use Cases:**
- Organize variables by service (DATABASE_, REDIS_, AWS_)
- Group authentication variables (AUTH_)
- Separate environments (PROD_, DEV_)

---

## 🔍 How It Works

### Step 1: Analysis

The AI analyzes your environment variable **metadata only**:
- Variable names
- Naming patterns
- Common prefixes
- Grouping opportunities

**❌ Never analyzed:**
- Actual secret values
- Sensitive data
- API keys or passwords

### Step 2: Generate Actions

The system creates a list of safe, actionable transformations:

```python
{
  "action_type": "rename",
  "old_name": "api_key",
  "new_name": "API_KEY",
  "reason": "Secret variables should be uppercase"
}
```

### Step 3: Preview

You can preview all changes before applying:

```bash
envcli ai apply --preview
```

Shows:
- What will be renamed
- New variable names
- Reason for each change
- **Values are HIDDEN**

### Step 4: Apply

When you apply changes:

1. ✅ Load current environment
2. ✅ Verify old variable exists
3. ✅ Check new name doesn't conflict
4. ✅ **Copy value to new name**
5. ✅ Delete old name
6. ✅ Save updated environment
7. ✅ Log action for audit

**The actual secret value is preserved throughout!**

---

## 🛡️ Security Guarantees

### What's Protected

| Feature | Protection |
|---------|-----------|
| **Values** | Never exposed in CLI output |
| **Secrets** | Never sent to AI providers |
| **Logs** | Only metadata logged, no values |
| **Preview** | Shows `[PRESERVED - NOT SHOWN]` |
| **History** | Records actions, not values |

### Example: Renaming an API Key

**Before:**
```json
{
  "api_key": "sk-proj-abc123xyz789..."
}
```

**Action:**
```
Rename 'api_key' to 'API_KEY'
```

**After:**
```json
{
  "API_KEY": "sk-proj-abc123xyz789..."
}
```

**✅ The secret value `sk-proj-abc123xyz789...` is preserved exactly!**

---

## 📊 Real-World Example

### Initial State (Messy)

```bash
$ envcli env list --profile demo
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Key               ┃ Value                     ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ api_key           │ *****************         │
│ database_url      │ postgres://localhost/mydb │
│ DatabasePassword  │ *********                 │
│ redis_host        │ localhost                 │
│ redis_port        │ 6379                      │
│ smtp_server       │ smtp.gmail.com            │
│ smtp_port         │ 587                       │
└───────────────────┴───────────────────────────┘
```

### Get Suggestions

```bash
$ envcli ai suggest --profile demo

💡 Found 7 actionable suggestion(s):

1. Rename 'api_key' to 'API_KEY' (uppercase for secrets)
2. Rename 'DatabasePassword' to 'DATABASE_PASSWORD'
3. Add 'REDIS_' prefix to 'redis_host'
4. Add 'REDIS_' prefix to 'redis_port'
5. Add 'EMAIL_' prefix to 'smtp_server'
6. Add 'EMAIL_' prefix to 'smtp_port'
7. Add 'DATABASE_' prefix to 'database_url'
```

### Apply Changes

```bash
$ envcli ai apply --profile demo --yes

✓ Successfully applied 7 change(s)
```

### Final State (Organized)

```bash
$ envcli env list --profile demo
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Key                   ┃ Value                     ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ API_KEY               │ *****************         │
│ DATABASE_PASSWORD     │ *********                 │
│ DATABASE_URL          │ postgres://localhost/mydb │
│ REDIS_HOST            │ localhost                 │
│ REDIS_PORT            │ 6379                      │
│ EMAIL_SMTP_SERVER     │ smtp.gmail.com            │
│ EMAIL_SMTP_PORT       │ 587                       │
└───────────────────────┴───────────────────────────┘
```

**✅ All values preserved, organization improved!**

---

## 🎯 CLI Commands

### `envcli ai suggest`

Generate actionable suggestions for improvements.

```bash
envcli ai suggest [OPTIONS]

Options:
  -p, --profile TEXT  Profile to analyze (default: current)
```

**Example:**
```bash
envcli ai suggest --profile production
```

### `envcli ai apply`

Apply AI-suggested improvements.

```bash
envcli ai apply [OPTIONS]

Options:
  -p, --profile TEXT  Profile to modify (default: current)
  --preview          Preview changes without applying
  -y, --yes          Skip confirmation prompt
```

**Examples:**
```bash
# Preview changes
envcli ai apply --preview

# Apply with confirmation
envcli ai apply

# Apply without confirmation
envcli ai apply --yes

# Apply to specific profile
envcli ai apply --profile staging --yes
```

### `envcli ai history`

View history of applied AI actions.

```bash
envcli ai history [OPTIONS]

Options:
  -p, --profile TEXT  Profile to show history for
  -n, --limit INT     Number of entries to show (default: 10)
```

**Example:**
```bash
envcli ai history --profile demo --limit 20
```

---

## 🔧 Advanced Usage

### Selective Application

Currently, all suggestions are applied together. To apply selectively:

1. Preview all suggestions: `envcli ai apply --preview`
2. Manually apply specific changes: `envcli env add NEW_NAME value`
3. Remove old variable: `envcli env remove old_name`

### Rollback Changes

If you need to undo changes:

1. Check history: `envcli ai history`
2. Manually rename back: `envcli env add old_name value`
3. Or restore from backup if you exported before applying

**💡 Tip:** Always export before major changes:
```bash
envcli env export backup.env --profile demo
envcli ai apply --profile demo --yes
# If needed: envcli env import backup.env --profile demo
```

---

## 🧪 Testing

Test the feature safely:

```bash
# Create a test profile
envcli env add TEST_VAR "test_value" --profile test
envcli env add api_key "sk-test-123" --profile test
envcli env add database_url "postgres://localhost/db" --profile test

# Get suggestions
envcli ai suggest --profile test

# Preview changes
envcli ai apply --profile test --preview

# Apply changes
envcli ai apply --profile test --yes

# Verify values preserved
envcli env list --profile test --no-mask

# Check history
envcli ai history --profile test
```

---

## 📝 Audit Trail

Every action is logged to `~/.envcli/ai_actions_log.json`:

```json
{
  "profile": "demo",
  "action": {
    "action_type": "rename",
    "description": "Rename 'api_key' to 'API_KEY'",
    "details": {
      "old_name": "api_key",
      "new_name": "API_KEY",
      "reason": "Secret variables should be uppercase"
    },
    "applied": true,
    "timestamp": "2025-10-28T13:15:53.928296"
  },
  "timestamp": "2025-10-28T13:15:53.928296"
}
```

**Note:** Values are NEVER logged!

---

## ❓ FAQ

### Q: Are my secrets safe?

**A:** Yes! The AI only sees variable **names**, never values. When applying changes, values are copied internally without ever being displayed or logged.

### Q: What if something goes wrong?

**A:** Each action is independent. If one fails, others continue. Failed actions are reported clearly. Always use `--preview` first!

### Q: Can I undo changes?

**A:** Export your profile before applying changes. You can then re-import if needed. We recommend:

```bash
envcli env export backup.env
envcli ai apply --yes
```

### Q: Will this break my application?

**A:** Variable names change, so you'll need to update your application code to use the new names. Use `--preview` to see all changes first.

### Q: Can I customize the suggestions?

**A:** Currently, suggestions are based on best practices. Future versions will support custom rules and policies.

---

## 🎉 Benefits

✅ **Consistency** - Standardized naming across all environments  
✅ **Organization** - Related variables grouped with prefixes  
✅ **Security** - Secrets properly identified and formatted  
✅ **Compliance** - Audit trail for all changes  
✅ **Efficiency** - Automated improvements save time  
✅ **Safety** - Preview before apply, values always preserved  

---

## 🚀 Next Steps

1. Try it on a test profile first
2. Use `--preview` to understand changes
3. Export backups before applying
4. Review history after applying
5. Update your application code to use new variable names

**Ready to organize your environment variables safely?**

```bash
envcli ai suggest
envcli ai apply --preview
envcli ai apply --yes
```
