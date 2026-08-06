# Baseline Data Pipeline & Observability Report (Phase 1)

## 1. Executive Summary

This report documents the baseline performance and observability status of the RAG data pipeline operating on scholarly paper metadata fetched from Crossref.

## 2. Ingestion & Dataset Summary

| Parameter | Value |
| :--- | :--- |
| **Source API** | Crossref REST API |
| **Search Query** | `agentic retrieval augmented generation large language model` |
| **Search Filter** | `from-pub-date:2026-02-07,has-abstract:true` |
| **Total Records Ingested** | 24 |
| **Cleaned Dataset Rows** | 24 |

## 3. Baseline Evaluation Metrics

Evaluation performed across 60 synthetic test samples.

| Metric | Score | Target Standard |
| :--- | :---: | :---: |
| **Retrieval Hit Rate** | 1.0000 | >= 0.8000 |
| **Mean Token F1** | 1.0000 | >= 0.5000 |
| **Judge Accuracy** | 1.0000 | >= 0.8000 |
| **Mean Judge Score** | 5.00 / 5.0 | >= 3.50 |

## 4. Data Observability & Quality Audit

Overall Quality Status: **PASSED**

| Check | Passed? | Value |
| :--- | :---: | :--- |
| Row Count Check | YES | Total rows: 24 |
| Null Paper IDs | YES | Null count: 0 |
| Duplicate Paper IDs | YES | Duplicate count: 0 |
| Null Titles | YES | Null title count: 0 |
| Short Summaries (<50 chars) | YES | Short summary count: 0 |
| Freshness Check | YES | Stale rows: 0 |

## 5. Freshness Monitoring

| Freshness Signal | Value |
| :--- | :--- |
| **Latest Published Date** | 2026-08-05 |
| **Oldest Published Date** | 2026-02-12 |
| **Freshness Threshold** | 180 days |
| **Stale Row Count** | 0 |
| **Is Fresh?** | YES |
