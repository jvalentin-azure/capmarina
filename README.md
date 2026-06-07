# Lamako PDF Server — Railway Deployment

## Overview
Flask + ReportLab PDF generation server for the **Ticket by Lamako** post-event report plugin.

Deployed on Railway: `lamako-pdf-server-production.up.railway.app`

## Versions
- **v2.0-backup** (tag): Working version with all sections. File: `app_v2_backup.py`
- **v3.0** (current): Premium design version with Raleway typography, enhanced charts, condensed tables

## Endpoint
```
POST /generate-pdf
Content-Type: application/json
Body: { event, kpi, pay_labels, by_pay, col_totals, cat_ch_rows, cat_pay_rows, mm_breakdown, carte_breakdown, pos_client_breakdown, commissions, frais_fixes, reconciliation, refunds, sales_by_day }
Returns: application/pdf
```

## Sections in PDF
1. Header with logo + event name + date
2. KPI grid (12 indicators)
3. Vue d'ensemble (3 pie charts: billets, présence, modes de paiement)
4. Ventes par jour (bar chart)
5. Ventes par catégorie (horizontal bar chart + table)
6. Ventes par catégorie × mode de paiement (cross table)
7. Détail Mobile Money (MVola, Orange, Airtel — Web/POS breakdown)
8. Carte Bancaire — Détail Web/POS
9. Détail Guichet Client — Modes de paiement
10. Commissions & Frais Lamako (Web-only basis)
11. Remboursements (table with order details)
12. Réconciliation Comptable (A: Recettes, B: Déductions, C: Encaissements Guichet Client)

## Tech Stack
- Python 3.11 / Flask / Gunicorn
- ReportLab (PDF generation)
- Matplotlib (charts)
- Font: Raleway (Regular, SemiBold, Bold)

## Deployment
Auto-deploys from `main` branch via Railway CLI or GitHub integration.
```bash
RAILWAY_TOKEN=<project_token> railway up --service lamako-pdf-server
```
