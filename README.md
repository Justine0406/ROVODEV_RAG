# Thesis Panelist AI - MVP

## Quick Start
1. Visit the deployed app (URL will be added after deployment)
2. Get free Groq API key: https://console.groq.com
3. Upload your thesis PDF
4. Get instant expert feedback!

## Local Development
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Features
- ✅ Comprehensive thesis critique like a real committee member
- ✅ Visual annotations showing exactly what to fix
- ✅ Free demo - no signup required
- ✅ Privacy-first - documents processed in memory only

## Note
This is a demo MVP. Documents are processed in memory only.
Nothing is saved or stored on our servers.

## Review Modes
- **Full Panelist Review** - Comprehensive critique covering all aspects
- **Methodology Check** - Focus on research design and validity
- **Writing Quality** - Grammar, clarity, and structure review

## Limitations (MVP Phase)
- Max 10MB PDF file size
- Recommended under 50 pages for optimal performance
- Requires your own Groq API key (free tier available)
- No persistent storage - refresh resets session
