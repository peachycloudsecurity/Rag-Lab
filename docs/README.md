# 📚 DevNotes Documentation

Complete documentation for the DevNotes vulnerable Flask application.

---

## 📖 Documentation Index

### 🚀 Getting Started

- **[QUICKSTART.md](QUICKSTART.md)** - **Start here!** Get the app running in 3 steps (10 minutes)
  - Prerequisites
  - One-command setup
  - Quick vulnerability tests
  - Common commands

### 🔧 Setup & Deployment

- **[SETUP_FLOW.md](SETUP_FLOW.md)** - Detailed automated setup flow
  - What happens during `docker compose up`
  - Timeline breakdown (first-time vs subsequent)
  - Container architecture
  - Data persistence
  - Troubleshooting

### 🔓 Security & Vulnerabilities

- **[OWASP_2025_REVIEW.md](OWASP_2025_REVIEW.md)** - Complete security review
  - All 10 OWASP Top 10:2025 vulnerabilities
  - Code locations
  - Exploitation examples
  - Fix recommendations
  - Testing instructions

- **[AI_PROMPT_INJECTION.md](AI_PROMPT_INJECTION.md)** - LLM security guide
  - Prompt injection vulnerability details
  - 7+ exploitation techniques
  - OWASP mappings (A03, A04, A09, A10)
  - Mitigation strategies
  - Workshop scenarios

### 👤 Admin Features

- **[ADMIN_MANAGEMENT.md](ADMIN_MANAGEMENT.md)** - Admin functionality guide
  - Admin credentials configuration
  - User management (create, delete, bulk operations)
  - Cleanup database feature
  - Restore to defaults feature
  - Workshop workflows
  - Troubleshooting

---

## 📁 Quick Navigation

```
docs/
├── README.md                    # This file - documentation index
├── QUICKSTART.md               # 3-step quick start (START HERE!)
├── SETUP_FLOW.md               # Detailed setup flow
├── OWASP_2025_REVIEW.md        # Complete security review
├── AI_PROMPT_INJECTION.md      # LLM prompt injection guide
└── ADMIN_MANAGEMENT.md         # Admin features guide
```

---

## 🎯 Recommended Reading Order

### For First-Time Users:
1. **[QUICKSTART.md](QUICKSTART.md)** - Get running quickly
2. **[OWASP_2025_REVIEW.md](OWASP_2025_REVIEW.md)** - Understand vulnerabilities
3. **[AI_PROMPT_INJECTION.md](AI_PROMPT_INJECTION.md)** - Learn AI exploitation

### For Workshop Instructors:
1. **[ADMIN_MANAGEMENT.md](ADMIN_MANAGEMENT.md)** - Set up admin credentials
2. **[QUICKSTART.md](QUICKSTART.md)** - Deploy for students
3. **[OWASP_2025_REVIEW.md](OWASP_2025_REVIEW.md)** - Teaching material

### For DevOps/Setup Issues:
1. **[SETUP_FLOW.md](SETUP_FLOW.md)** - Understand the automation
2. **[QUICKSTART.md](QUICKSTART.md)** - Troubleshooting section

---

## 🔗 External Links

- **Main README:** [../README.md](../README.md)
- **Peachycloud Security:** https://peachycloudsecurity.com
- **YouTube Channel:** https://www.youtube.com/@peachycloudsecurity
- **Support:** https://peachycloudsecurity.com/support

---

**Built by [Peachycloud Security](https://peachycloudsecurity.com) - The Shukla Duo**
