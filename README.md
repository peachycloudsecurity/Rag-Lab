# Rag-Lab — RAG Poisoning & Prompt Injection Defense Lab

**Peachycloud Security** | [peachycloudsecurity.com](https://peachycloudsecurity.com) | By The Shukla Duo

---

## Repo Structure

```
Rag-Lab/
├── attack/        ← Full vulnerable app — run this for the attack demo
│   ├── attack.md  ← Attack steps
│   └── ...        ← Complete Flask app (app.py, templates, docker-compose, Makefile)
└── defense/       ← LLM Guard defense — run this after the attack demo
    ├── defense.md ← Defense steps
    ├── app.py     ← Vulnerable version
    ├── app_fix.py ← Fixed version (LLM Guard integrated)
    └── ...        ← Complete Flask app with all modules
```

---

## Attack Lab

```bash
cd /home/ubuntu
git clone https://github.com/peachycloudsecurity/Rag-Lab.git
cd Rag-Lab/attack
make start
```

See `attack/attack.md` for full step-by-step.

---

## Defense Lab

```bash
cd /home/ubuntu/Rag-Lab/defense
docker stop $(docker ps -aq) && docker rm $(docker ps -aq)
cp app_fix.py app.py
echo "llm-guard" >> requirements.txt
make start
```

See `defense/defense.md` for full step-by-step.

---

## Default Credentials

| Field | Value |
|-------|-------|
| URL | `http://<EC2-IP>:5000` |
| Username | `admin` |
| Password | `admin123` |

---

## What This Lab Demonstrates

| Attack | OWASP Coverage |
|--------|---------------|
| RAG Poisoning | LLM08, LLM09 |
| Indirect Prompt Injection via vector store | LLM01 |
| Prompt Injection (defense with LLM Guard) | LLM01 |
