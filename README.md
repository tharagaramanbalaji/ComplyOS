# 🏛️ ComplyOS: Natural Language Rule Engine for XML Invoice Validation

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-00a67e.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2-61dafb.svg)](https://react.dev/)

**Natural Language Rule Engine for XML Invoice Validation**  
ComplyOS is an enterprise-grade validation engine that converts plain English compliance rules into deterministic, high-performance XSLT machine code.

---

## 📖 Overview

Tax-compliant e-invoicing systems rely on strict XML validation. Today, validation rules are written as code-heavy XSLT, creating an engineering bottleneck whenever compliance requirements change. 

**ComplyOS** allows users to write validation rules in plain English. The system pairs local, zero-shot NLP embeddings with an Intermediate Representation (IR) compiler to generate deterministic XSLT scripts. It runs these rules against XML invoices and returns clear pass/fail results with Explainable AI data traceability.

## 🚀 Quickstart

### 1. Start FastAPI Backend
```bash
venv\Scripts\activate
pip install -r requirements.txt
uvicorn api.main:app --reload
```
*API running at `http://localhost:8000`.*

### 2. Start React Dashboard
Open a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
*Interactive UI running at `http://localhost:5173`.*

---
**ComplyOS** • *Hackathon Submission*
