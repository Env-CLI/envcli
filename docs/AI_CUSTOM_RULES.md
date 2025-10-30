# AI Custom Rules & Policies

**Define your own rules for AI-powered environment variable management!**

EnvCLI allows you to create custom rules that the AI will automatically apply when suggesting improvements. This gives you fine-grained control over naming conventions, organization patterns, and transformations while maintaining the security guarantee that **values are never exposed**.

---

## 🎯 Overview

Custom rules allow you to:

- **Enforce naming conventions** across your team
- **Standardize variable organization** automatically
- **Group related variables** with prefixes
- **Apply custom transformations** to variable names
- **Exclude specific variables** from modifications
- **Integrate with policy engine** for compliance

---

## 📋 Rule Types

### 1. Naming Rules

Enforce specific naming formats for variables matching a pattern.

**Supported Formats:**

- `uppercase` - ALL_CAPS
- `lowercase` - all_lowercase
- `snake_case` - lower_snake_case
- `SCREAMING_SNAKE_CASE` - UPPER_SNAKE_CASE
- `camelCase` - camelCase
- `PascalCase` - PascalCase

**Example:**

```bash
# All variables ending with _key, _secret, _token should be uppercase
envcli ai add-rule naming '.*_(key|secret|token)$' uppercase \
  --description "Security credentials must be uppercase"

# Database variables should use SCREAMING_SNAKE_CASE
envcli ai add-rule naming '^(db|database)_.*' SCREAMING_SNAKE_CASE \
  --description "Database variables convention"
```

### 2. Prefix Rules

Add prefixes to group related variables.

**Example:**

```bash
# Add REDIS_ prefix to all redis-related variables
envcli ai add-rule prefix '^redis_' 'REDIS_' \
  --description "Group Redis configuration"

# Add AWS_ prefix to AWS-related variables
envcli ai add-rule prefix '^(aws|s3|ec2|lambda)_' 'AWS_' \
  --description "Group AWS services"

# Add EMAIL_ prefix to SMTP variables
envcli ai add-rule prefix '^smtp_' 'EMAIL_SMTP_' \
  --description "Group email configuration"
```

### 3. Transformation Rules

Apply custom transformations to variable names.

**Supported Transformations:**

- `replace:old:new` - Replace substring
- `regex:pattern:replacement:flags` - Regex replacement
- `remove_prefix:prefix` - Remove prefix
- `remove_suffix:suffix` - Remove suffix

**Example:**

```bash
# Replace 'api' with 'API' in all variable names
envcli ai add-rule transform '.*api.*' 'replace:api:API' \
  --description "Standardize API naming"

# Remove 'app_' prefix from all variables
envcli ai add-rule transform '^app_' 'remove_prefix:app_' \
  --description "Remove legacy app_ prefix"

# Replace underscores with dashes in specific variables
envcli ai add-rule transform '^feature_flag_' 'replace:_:-' \
  --description "Use dashes in feature flags"
```

### 4. Exclusion Rules

Prevent specific variables from being modified.

**Example:**

```bash
# Never modify system variables
envcli ai add-rule exclude '^(PATH|HOME|USER|SHELL)$' \
  --description "System environment variables"

# Protect production secrets
envcli ai add-rule exclude '.*_PROD_.*' \
  --description "Production secrets are locked"

# Exclude legacy variables
envcli ai add-rule exclude '^LEGACY_' \
  --description "Legacy variables - do not touch"
```

---

## 🚀 Quick Start

### Step 1: Add Rules

```bash
# Add naming rule for secrets
envcli ai add-rule naming '.*_(key|secret|password|token)' uppercase \
  -d "Secrets must be uppercase"

# Add prefix rule for database variables
envcli ai add-rule prefix '^(db|database)_' 'DATABASE_' \
  -d "Group database configuration"

# Exclude system variables
envcli ai add-rule exclude '^(PATH|HOME)$' \
  -d "System variables"
```

### Step 2: View Rules

```bash
envcli ai list-rules
```

Output:

```bash
📋 Custom AI Rules for 'dev'
Total: 3 rule(s)

Naming Rules:
  0. Pattern: .*_(key|secret|password|token) → uppercase
     Secrets must be uppercase

Prefix Rules:
  0. Pattern: ^(db|database)_ → DATABASE_*
     Group database configuration

Exclusions:
  0. Pattern: ^(PATH|HOME)$
     System variables
```

### Step 3: Apply Rules

```bash
# Generate suggestions (includes custom rules)
envcli ai suggest

# Preview changes
envcli ai apply --preview

# Apply changes
envcli ai apply --yes
```

### Step 4: Remove Rules (if needed)

```bash
# Remove a naming rule
envcli ai remove-rule naming_rules 0

# Remove an exclusion
envcli ai remove-rule exclusions 0
```

---

## 📖 Real-World Examples

### Example 1: Standardize Team Conventions

**Scenario:** Your team uses inconsistent naming for API keys.

**Before:**

```bash
api_key=[REDACTED:api-key]
ApiKey=sk-456
API_KEY=[REDACTED:api-key]
apiKey=sk-000
```

**Add Rule:**

```bash
envcli ai add-rule naming '.*api.*key.*' uppercase \
  -d "API keys must be uppercase"
```

**After applying:**

```bash
API_KEY=[REDACTED:api-key]
API_KEY=[REDACTED:api-key]
API_KEY=[REDACTED:api-key]
```

### Example 2: Organize Microservices Configuration

**Scenario:** Multiple services with mixed variable names.

**Before:**

```bash
redis_host=localhost
redis_port=6379
postgres_url=postgres://...
postgres_password=secret
smtp_server=smtp.gmail.com
smtp_port=587
```

**Add Rules:**

```bash
envcli ai add-rule prefix '^redis_' 'REDIS_'
envcli ai add-rule prefix '^postgres_' 'DATABASE_'
envcli ai add-rule prefix '^smtp_' 'EMAIL_SMTP_'
```

**After applying:**

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
DATABASE_URL=postgres://...
DATABASE_PASSWORD=secret
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
```

### Example 3: Migrate Legacy Naming

**Scenario:** Migrating from old naming convention to new one.

**Before:**

```bash
app_db_host=localhost
app_db_port=5432
app_cache_host=redis
app_cache_port=6379
```

**Add Rules:**

```bash
# Remove 'app_' prefix
envcli ai add-rule transform '^app_' 'remove_prefix:app_'

# Add service-specific prefixes
envcli ai add-rule prefix '^db_' 'DATABASE_'
envcli ai add-rule prefix '^cache_' 'CACHE_'

# Uppercase everything
envcli ai add-rule naming '.*' 'SCREAMING_SNAKE_CASE'
```

**After applying:**

```bash
DATABASE_HOST=localhost
DATABASE_PORT=5432
CACHE_HOST=redis
CACHE_PORT=6379
```

### Example 4: Protect Critical Variables

**Scenario:** Ensure production secrets are never accidentally modified.

```bash
# Exclude all production variables
envcli ai add-rule exclude '.*_PROD_.*' \
  -d "Production secrets - locked"

# Exclude system variables
envcli ai add-rule exclude '^(PATH|HOME|USER|SHELL|TERM)$' \
  -d "System environment variables"

# Exclude CI/CD variables
envcli ai add-rule exclude '^(CI|GITHUB|GITLAB|JENKINS)_' \
  -d "CI/CD platform variables"
```

Now these variables will **never** be modified by AI suggestions!

---

## 🔧 Advanced Usage

### Regex Patterns

Custom rules use Python regex patterns. Here are some useful patterns:

```bash
# Match any variable containing 'key'
'.*key.*'

# Match variables ending with '_key' or '_secret'
'.*_(key|secret)$'

# Match variables starting with 'db_' or 'database_'
'^(db|database)_'

# Match exact variable name
'^API_KEY$'

# Match variables with numbers
'.*[0-9]+.*'

# Match uppercase variables
'^[A-Z_]+$'
```

### Combining Rules

Rules are applied in order:

1. Exclusions (checked first)
2. Naming rules
3. Prefix rules
4. Transformation rules

**Example workflow:**

```bash
# Step 1: Exclude system variables
envcli ai add-rule exclude '^(PATH|HOME)$'

# Step 2: Standardize naming
envcli ai add-rule naming '.*' 'SCREAMING_SNAKE_CASE'

# Step 3: Add service prefixes
envcli ai add-rule prefix '^redis_' 'REDIS_'
envcli ai add-rule prefix '^db_' 'DATABASE_'

# Step 4: Apply all rules
envcli ai suggest
envcli ai apply --yes
```

### Profile-Specific Rules

Rules are stored per-profile, allowing different conventions for different environments:

```bash
# Development profile - relaxed rules
envcli ai add-rule naming '.*_(key|secret)' uppercase -p dev

# Production profile - strict rules
envcli ai add-rule naming '.*' 'SCREAMING_SNAKE_CASE' -p prod
envcli ai add-rule exclude '.*' -p prod  # Lock everything!
```

---

## 🔒 Security Guarantees

**Custom rules NEVER expose sensitive values!**

- ✅ Rules only match variable **names**, never values
- ✅ Transformations preserve values exactly
- ✅ Exclusions prevent accidental modifications
- ✅ Preview mode shows changes before applying
- ✅ Full audit trail maintained
- ✅ Values displayed as `[PRESERVED - NOT SHOWN]`

---

## 📊 Integration with Policy Engine

Custom rules work seamlessly with EnvCLI's policy engine:

```bash
# Add policy for required naming convention
envcli policy add naming uppercase "All secrets must be uppercase"

# Add custom rule to enforce it
envcli ai add-rule naming '.*_(key|secret|token|password)' uppercase \
  -d "Enforce security naming policy"

# Validate compliance
envcli policy validate

# Auto-fix violations
envcli ai suggest
envcli ai apply --yes

# Verify compliance
envcli policy validate
```

---

## 🎯 Best Practices

### 1. Start with Exclusions

Always define exclusions first to protect critical variables:

```bash
envcli ai add-rule exclude '^(PATH|HOME|PROD_)' "Protected variables"
```

### 2. Use Descriptive Names

Add descriptions to make rules self-documenting:

```bash
envcli ai add-rule naming '.*_key$' uppercase \
  --description "Security keys must be uppercase per team policy"
```

### 3. Test with Preview

Always preview changes before applying:

```bash
envcli ai apply --preview  # Safe - no modifications
```

### 4. Version Control Rules

Export and commit your rules configuration:

```bash
# Rules are stored in ~/.envcli/ai_rules.json
cp ~/.envcli/ai_rules.json ./team-rules.json
git add team-rules.json
git commit -m "Add team AI rules"
```

### 5. Document Team Conventions

Create a team guide:

```markdown
# Team Environment Variable Conventions

## Naming Rules
- All secrets: UPPERCASE
- Database vars: DATABASE_* prefix
- Cache vars: CACHE_* prefix
- API vars: API_* prefix

## Setup
\`\`\`bash
envcli ai add-rule naming '.*_(key|secret|token)' uppercase
envcli ai add-rule prefix '^db_' 'DATABASE_'
envcli ai add-rule prefix '^cache_' 'CACHE_'
envcli ai add-rule prefix '^api_' 'API_'
\`\`\`
```

---

## 🛠️ Troubleshooting

### Rules Not Applied

**Problem:** Rules don't seem to be working.

**Solution:**

```bash
# Check if rules are enabled
envcli ai list-rules

# Verify rule patterns
envcli ai list-rules | grep "Pattern"

# Test with preview
envcli ai apply --preview
```

### Conflicting Rules

**Problem:** Multiple rules match the same variable.

**Solution:** Rules are applied in order. The last matching rule wins. Use exclusions to prevent conflicts:

```bash
# Exclude specific variables from general rules
envcli ai add-rule exclude '^SPECIAL_VAR$'
```

### Regex Not Matching

**Problem:** Regex pattern doesn't match expected variables.

**Solution:** Test your regex:

```python
import re
pattern = '.*_key$'
test_vars = ['api_key', 'API_KEY', 'database_url']
for var in test_vars:
    if re.match(pattern, var):
        print(f"✓ {var} matches")
```

---

## 📚 Command Reference

### Add Rule

```bash
envcli ai add-rule <type> <pattern> <target> [--description DESC] [--profile PROFILE]
```

### List Rules

```bash
envcli ai list-rules [--profile PROFILE]
```

### Remove Rule

```bash
envcli ai remove-rule <rule_type> <index> [--profile PROFILE]
```

### Apply Rules

```bash
envcli ai suggest [--profile PROFILE]
envcli ai apply [--preview] [--yes] [--profile PROFILE]
```

---

## 🎉 Summary

Custom rules give you **complete control** over AI-powered environment variable management:

- ✅ Define team conventions once, apply automatically
- ✅ Enforce naming standards across all profiles
- ✅ Organize variables by service/function
- ✅ Protect critical variables from modification
- ✅ Integrate with policy engine for compliance
- ✅ **Never expose sensitive values**

**Get started now:**

```bash
envcli ai add-rule naming '.*_(key|secret)' uppercase
envcli ai suggest
envcli ai apply --preview
```

Your environment variables, your rules, your way! 🚀
