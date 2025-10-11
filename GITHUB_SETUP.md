# 🚀 GitHub Collaboration Setup - Complete Guide

This document explains the new collaborative development setup for VFScore on GitHub.

---

## 📋 Summary of Changes

### ✅ New Files Created

1. **`setup.py`** - Interactive setup script
2. **`CONTRIBUTING.md`** - Developer contribution guidelines
3. **`LICENSE`** - MIT License
4. **`.gitattributes`** - Git line ending configuration
5. **`.github/ISSUE_TEMPLATE/bug_report.md`** - Bug report template
6. **`.github/ISSUE_TEMPLATE/feature_request.md`** - Feature request template
7. **`.github/pull_request_template.md`** - Pull request template

### 📝 Files Updated

1. **`src/vfscore/config.py`** - Added support for `config.local.yaml` overrides
2. **`README.md`** - Updated with new setup instructions
3. **`.gitignore`** - Enhanced for collaborative development

---

## 🎯 How the New System Works

### Two-Layer Configuration System

**VFScore now uses a dual configuration approach:**

#### 1. **`config.yaml`** (Shared, Committed to Git)
- Contains **default settings** for all developers
- Safe to commit to GitHub
- Examples: render samples, rubric weights, default paths

#### 2. **`config.local.yaml`** (Personal, NOT Committed)
- Contains **machine-specific overrides**
- **Never committed** to git (in `.gitignore`)
- Examples: your Blender path, custom settings

**How it works:**
```
config.yaml (defaults) + config.local.yaml (overrides) = Final Config
```

---

## 🔧 Setup for New Developers

### Option 1: Interactive Setup (Recommended)

```bash
# Clone repository
git clone https://github.com/mattiaTagliente/VFScore.git
cd VFScore

# Run interactive setup
python setup.py
```

**The script will:**
1. ✅ Ask for your Gemini API key
2. ✅ Auto-detect Blender installation
3. ✅ Create `.env` file
4. ✅ Create `config.local.yaml`
5. ✅ Install Python dependencies
6. ✅ Verify the setup

### Option 2: Manual Setup

```bash
# 1. Clone repository
git clone https://github.com/mattiaTagliente/VFScore.git
cd VFScore

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# 3. Install dependencies
pip install -e .

# 4. Create .env file
cp .env.example .env
# Edit .env and add: GEMINI_API_KEY=your_key_here

# 5. Create config.local.yaml
cat > config.local.yaml << EOF
paths:
  blender_exe: "YOUR_BLENDER_PATH"
EOF

# 6. Test
vfscore --version
python tests/test_setup.py
```

---

## 📁 File Structure for Collaboration

### Files That ARE Committed to Git ✅

```
VFScore/
├── src/                  # Source code
├── tests/                # Test files
├── config.yaml           # ✅ Shared default config
├── .env.example          # ✅ Template for API keys
├── .gitignore            # ✅ Ignore rules
├── .gitattributes        # ✅ Git attributes
├── setup.py              # ✅ Setup script
├── pyproject.toml        # ✅ Package config
├── requirements.txt      # ✅ Dependencies
├── README.md             # ✅ Documentation
├── CONTRIBUTING.md       # ✅ Developer guide
├── LICENSE               # ✅ MIT License
└── .github/              # ✅ GitHub templates
```

### Files That Are NOT Committed ❌

```
VFScore/
├── .env                  # ❌ Your API keys
├── config.local.yaml     # ❌ Your local settings
├── venv/                 # ❌ Virtual environment
├── outputs/              # ❌ Generated outputs
├── __pycache__/          # ❌ Python cache
└── .pytest_cache/        # ❌ Test cache
```

---

## 🔐 Security Best Practices

### ⚠️ CRITICAL: Never Commit Sensitive Data

**Files to NEVER commit:**
- `.env` - Contains API keys
- `config.local.yaml` - May contain personal info
- Any file with API keys, passwords, or tokens

### If You Accidentally Commit Sensitive Data:

```bash
# Remove file from Git history (CAREFUL!)
git rm --cached .env
git commit -m "Remove .env from git"

# Force push (if no one has pulled yet)
git push --force

# Rotate your API keys immediately!
# - Gemini: https://aistudio.google.com/app/apikey
# - OpenAI: https://platform.openai.com/api-keys
```

**Prevention:** The `.gitignore` file already excludes these files.

---

## 👥 Collaboration Workflow

### For Team Members

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mattiaTagliente/VFScore.git
   cd VFScore
   ```

2. **Run setup:**
   ```bash
   python setup.py
   ```

3. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature
   ```

4. **Make changes, commit:**
   ```bash
   git add <files>
   git commit -m "feat: add new feature"
   ```

5. **Push and create Pull Request:**
   ```bash
   git push origin feature/your-feature
   # Then create PR on GitHub
   ```

---

## 🎨 Configuration Examples

### Example `config.local.yaml`

```yaml
# Your machine-specific settings
paths:
  blender_exe: "C:\\Program Files\\Blender Foundation\\Blender 4.5\\blender.exe"

# Faster rendering for development
render:
  samples: 128  # Default is 256

# More verbose logging
logging:
  level: DEBUG
```

### Example `.env`

```bash
# Your API keys
GEMINI_API_KEY=AIzaSyC...your_actual_key_here...

# Optional: OpenAI (Phase 2)
# OPENAI_API_KEY=sk-...your_actual_key_here...
```

---

## 🧪 Testing Your Setup

### Quick Test

```bash
# Activate virtual environment
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# Test VFScore is installed
vfscore --version

# Run setup verification
python tests/test_setup.py
```

### Full Pipeline Test

```bash
# Run fast mode on test data
vfscore run-all --fast --repeats 1
```

---

## 🐛 Troubleshooting

### Problem: "config.local.yaml not found"
**Solution:** This is normal! Create one if you need custom settings.

```bash
# Create config.local.yaml
python setup.py
# Or manually create it
```

### Problem: "GEMINI_API_KEY not set"
**Solution:** 

```bash
# Check if .env exists
ls -la .env  # or: dir .env on Windows

# If not, create it
python setup.py
# Or manually:
cp .env.example .env
# Edit .env and add your key
```

### Problem: "Blender not found"
**Solution:**

```yaml
# Create/edit config.local.yaml
paths:
  blender_exe: "YOUR_BLENDER_PATH"
```

**Find your Blender path:**
- Windows: `C:\Program Files\Blender Foundation\Blender X.X\blender.exe`
- macOS: `/Applications/Blender.app/Contents/MacOS/Blender`
- Linux: `/usr/bin/blender` or `~/blender/blender`

### Problem: "Import error: vfscore"
**Solution:**

```bash
# Make sure you're in project root
cd /path/to/VFScore

# Activate venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# Install in editable mode
pip install -e .
```

---

## 📚 Documentation References

| File | Purpose |
|------|---------|
| `README.md` | Project overview and quick start |
| `CONTRIBUTING.md` | Detailed developer guide |
| `SETUP.md` | Step-by-step installation |
| `QUICKSTART.md` | Common commands reference |
| This file | Collaboration setup guide |

---

## 🔄 Keeping Your Fork Updated

```bash
# Add upstream remote (one time)
git remote add upstream https://github.com/mattiaTagliente/VFScore.git

# Fetch latest changes
git fetch upstream

# Merge into your main branch
git checkout main
git merge upstream/main

# Push to your fork
git push origin main
```

---

## 📝 Commit Message Guidelines

Use conventional commits:

```
feat: add new feature
fix: fix a bug
docs: update documentation
refactor: refactor code
test: add tests
chore: maintenance tasks
```

Examples:
```bash
git commit -m "feat: add GPT-4V support"
git commit -m "fix: resolve Blender path detection on macOS"
git commit -m "docs: update installation instructions"
```

---

## 🎯 What Changed from Original Setup

### Before (Old Setup)
- Single `config.yaml` file
- Everyone edits the same config
- Easy to accidentally commit personal settings
- Merge conflicts on `config.yaml`

### After (New Setup) ✅
- **`config.yaml`**: Shared defaults (safe to commit)
- **`config.local.yaml`**: Personal overrides (never committed)
- Interactive setup script
- Auto-detection of Blender
- Clearer documentation
- GitHub templates

---

## ✨ Benefits for Your Team

1. ✅ **No merge conflicts** on configuration
2. ✅ **Easy onboarding** with interactive setup
3. ✅ **Secure** - API keys never committed
4. ✅ **Flexible** - everyone can have custom settings
5. ✅ **Documented** - clear guidelines in CONTRIBUTING.md
6. ✅ **Professional** - GitHub templates for issues/PRs

---

## 🚀 Next Steps

### For Project Maintainer (You):

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "feat: add collaborative development setup"
   git push origin main
   ```

2. **Configure GitHub repo settings:**
   - Add branch protection rules
   - Enable GitHub Issues
   - Add collaborators

3. **Share with team:**
   - Send them the GitHub URL
   - Ask them to run `python setup.py`

### For Team Members:

1. Clone the repo
2. Run `python setup.py`
3. Start developing!

---

## 📞 Getting Help

- 📖 Read `CONTRIBUTING.md`
- 🐛 Check existing [GitHub Issues](https://github.com/mattiaTagliente/VFScore/issues)
- 💬 Create a new issue using templates
- 📧 Contact maintainers

---

**Happy collaborating! 🎉**
