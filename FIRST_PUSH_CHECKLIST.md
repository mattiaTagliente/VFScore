# ✅ First GitHub Push Checklist

Use this checklist before pushing VFScore to GitHub for the first time.

---

## 🔍 Pre-Push Verification

### 1. Check for Sensitive Data ⚠️

Run these checks to ensure no sensitive data will be committed:

```bash
# Check if .env is properly ignored
git status | grep .env
# Should NOT show .env file

# Check if config.local.yaml is ignored
git status | grep config.local.yaml
# Should NOT show config.local.yaml

# List all files that will be committed
git ls-files
# Verify .env and config.local.yaml are NOT in this list
```

**If you see `.env` or `config.local.yaml` in git status:**
```bash
# Remove from git tracking
git rm --cached .env
git rm --cached config.local.yaml
```

### 2. Verify .gitignore is Working

```bash
# Check .gitignore includes these patterns
cat .gitignore | grep -E "^\.env$|^config\.local\.yaml$"
```

Should show:
```
.env
config.local.yaml
```

### 3. Remove Any Personal Data from Code

Search for hardcoded paths or keys:

```bash
# Search for potential API keys
grep -r "AIza" src/  # Gemini keys start with AIza
grep -r "sk-" src/   # OpenAI keys start with sk-

# Search for hardcoded paths
grep -r "C:\\Users" src/
grep -r "/Users/" src/
grep -r "/home/" src/
```

**If found:** Replace with config references.

### 4. Verify config.yaml Has Generic Settings

Open `config.yaml` and ensure:
- ✅ Blender path is generic (not your personal path)
- ✅ No hardcoded personal directories
- ✅ All paths use relative references

**Current blender_exe should be:**
```yaml
paths:
  blender_exe: "C:\\Program Files\\Blender Foundation\\Blender 4.5\\blender.exe"
  # This is a generic Windows path, OK to commit
```

---

## 📝 Files to Commit

### ✅ These SHOULD be committed:

- [ ] Source code (`src/`)
- [ ] Tests (`tests/`)
- [ ] Documentation (`.md` files)
- [ ] Configuration template (`config.yaml`)
- [ ] Environment template (`.env.example`)
- [ ] Setup script (`setup.py`)
- [ ] Package files (`pyproject.toml`, `requirements.txt`)
- [ ] Git configuration (`.gitignore`, `.gitattributes`)
- [ ] GitHub templates (`.github/`)
- [ ] License (`LICENSE`)

### ❌ These should NOT be committed:

- [ ] `.env` (your API keys)
- [ ] `config.local.yaml` (your local settings)
- [ ] `venv/` (virtual environment)
- [ ] `outputs/` (generated files)
- [ ] `__pycache__/` (Python cache)
- [ ] `.vscode/` or `.idea/` (IDE settings)
- [ ] `datasets/` (optional - large files)

---

## 🚀 First Push Steps

### 1. Initialize Git (if not already done)

```bash
git init
```

### 2. Add All Files

```bash
# Add everything (respecting .gitignore)
git add .

# Verify what will be committed
git status
```

**Review the output carefully!**

### 3. Create Initial Commit

```bash
git commit -m "Initial commit: VFScore Phase 1 complete

- Interactive setup script
- Collaborative development configuration
- LLM-based visual fidelity scoring
- Blender Cycles rendering
- 4-dimension rubric
- Comprehensive documentation"
```

### 4. Add Remote Repository

```bash
git remote add origin https://github.com/mattiaTagliente/VFScore.git
```

### 5. Push to GitHub

```bash
# Push main branch
git push -u origin main
```

---

## 🔐 Security Double-Check

Before pushing, verify:

```bash
# 1. Check for API keys in committed files
git grep "AIza" $(git ls-files)
git grep "sk-" $(git ls-files)

# 2. Check for personal paths
git grep "matti" $(git ls-files)

# 3. Verify .env is ignored
git check-ignore .env
# Should output: .env

# 4. Verify config.local.yaml is ignored
git check-ignore config.local.yaml
# Should output: config.local.yaml
```

**If any of these checks fail, STOP and fix before pushing!**

---

## 📋 Post-Push Setup

### 1. Configure GitHub Repository

Go to: https://github.com/mattiaTagliente/VFScore/settings

**Recommended settings:**
- ✅ Enable Issues
- ✅ Enable Discussions (optional)
- ✅ Add repository description
- ✅ Add topics: `computer-vision`, `llm`, `3d-rendering`, `blender`, `python`

### 2. Set Up Branch Protection (Optional but Recommended)

Go to: Settings → Branches → Add rule

**For `main` branch:**
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass
- ⚠️ Do not allow force pushes

### 3. Add Collaborators

Go to: Settings → Collaborators → Add people

### 4. Create Initial Release (Optional)

Go to: Releases → Create a new release

```
Tag: v0.1.0
Title: VFScore Phase 1 Release
Description: Initial release with core features
```

---

## 👥 Onboarding Team Members

### Share These Instructions:

**For new developers:**

```bash
# 1. Clone repository
git clone https://github.com/mattiaTagliente/VFScore.git
cd VFScore

# 2. Run interactive setup
python setup.py

# 3. Start developing!
```

**Point them to:**
- README.md - Project overview
- CONTRIBUTING.md - Development guidelines
- GITHUB_SETUP.md - Collaboration guide

---

## 🐛 Common Issues and Solutions

### Issue: "fatal: remote origin already exists"
```bash
# Remove existing remote
git remote remove origin

# Add correct remote
git remote add origin https://github.com/mattiaTagliente/VFScore.git
```

### Issue: ".env file appears in git status"
```bash
# Remove from git tracking
git rm --cached .env

# Verify .gitignore includes .env
echo .env >> .gitignore

# Commit the fix
git add .gitignore
git commit -m "fix: ensure .env is gitignored"
```

### Issue: "Large files warning"
```bash
# If datasets or assets are too large, add to .gitignore:
echo "datasets/" >> .gitignore
echo "assets/*.hdr" >> .gitignore

git add .gitignore
git commit -m "chore: ignore large files"
```

---

## 📊 Final Verification

Before announcing to team:

- [ ] Repository is public (or private if needed)
- [ ] README.md renders correctly on GitHub
- [ ] Issues are enabled
- [ ] Collaborators are added
- [ ] No sensitive data visible in any files
- [ ] Setup script works on a fresh clone
- [ ] Documentation is clear and complete

---

## 🎯 Test the Setup

**Have someone else test:**

```bash
# They should be able to do this without issues:
git clone https://github.com/mattiaTagliente/VFScore.git
cd VFScore
python setup.py
# Follow prompts
vfscore --version
```

If this works, you're ready! 🎉

---

## 📝 Announcement Template

**For team chat/email:**

```
🚀 VFScore is now on GitHub!

Repository: https://github.com/mattiaTagliente/VFScore

Quick Start:
1. Clone: git clone https://github.com/mattiaTagliente/VFScore.git
2. Setup: python setup.py
3. Done!

Documentation:
- README.md - Project overview
- CONTRIBUTING.md - How to contribute
- GITHUB_SETUP.md - Collaboration guide

Questions? Open an issue or message me directly.

Happy coding! 🎉
```

---

## ✅ Checklist Summary

Before pushing:
- [ ] Verified no sensitive data
- [ ] .gitignore is correct
- [ ] config.yaml has generic settings
- [ ] Tested on clean directory
- [ ] Commit message is clear

After pushing:
- [ ] Repository settings configured
- [ ] Collaborators added
- [ ] Team notified
- [ ] Setup tested by someone else

---

**You're ready to push! 🚀**

```bash
git push -u origin main
```
