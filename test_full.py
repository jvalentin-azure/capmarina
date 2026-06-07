"""Test the PDF server locally with realistic data matching the PHP output."""
import sys
sys.path.insert(0, '.')
from app import build_pdf

data = {
    "event": {"name": "Concert Test", "date": "2026-05-30"},
    "kpi": {
        "tickets_sold": 79, "tickets_payants": 79, "tickets_gratuits": 0,
        "nb_commandes": 35, "recette_brut": 19750000, "total_remises": 0,
        "recette_nette": 19750000, "checkins": 0, "non_checkins": 79,
        "taux_checkin": 0.0, "aov": 564286, "nb_coupons": 0,
        "montant_reverser": 9885550, "web_tickets": 44,
        "pos_lamako_tickets": 0, "pos_client_tickets": 35,
        "peak_day": "2026-05-18", "peak_count": 10
    },
    "pay_labels": {
        "coupon100": "Coupon 100%",
        "especes_lamako": "Espèces Guichet Lamako",
        "cheque_lamako": "Chèque Guichet Lamako",
        "mvola": "MVola",
        "orange": "Orange Money (Papi)",
        "airtel": "Airtel Money",
        "especes_client": "Espèces Guichet Client",
        "cheque_client": "Chèque Guichet Client",
        "carte": "Carte Bancaire",
        "autre": "Autre"
    },
    "by_pay": {
        "coupon100": {"count": 0, "brut": 0, "net": 0},
        "especes_lamako": {"count": 0, "brut": 0, "net": 0},
        "cheque_lamako": {"count": 0, "brut": 0, "net": 0},
        "mvola": {"count": 10, "brut": 2500000, "net": 2500000},
        "orange": {"count": 16, "brut": 4000000, "net": 4000000},
        "airtel": {"count": 0, "brut": 0, "net": 0},
        "especes_client": {"count": 10, "brut": 2500000, "net": 2500000},
        "cheque_client": {"count": 3, "brut": 750000, "net": 750000},
        "carte": {"count": 40, "brut": 10000000, "net": 10000000},
        "autre": {"count": 0, "brut": 0, "net": 0}
    },
    "col_totals": {
        "coupon100": {"count": 0, "brut": 0, "net": 0},
        "especes_lamako": {"count": 0, "brut": 0, "net": 0},
        "mvola": {"count": 10, "brut": 2500000, "net": 2500000},
        "orange": {"count": 16, "brut": 4000000, "net": 4000000},
        "airtel": {"count": 0, "brut": 0, "net": 0},
        "especes_client": {"count": 10, "brut": 2500000, "net": 2500000},
        "cheque_client": {"count": 3, "brut": 750000, "net": 750000},
        "carte": {"count": 40, "brut": 10000000, "net": 10000000},
        "autre": {"count": 0, "brut": 0, "net": 0}
    },
    "cat_ch_rows": [
        {"cat": "Billet SIMPLE - 30 Mai", "web": 22, "pos_lamako": 0, "pos_client": 19, "total": 41, "brut": 10250000, "net": 10250000, "remise": 0, "unit_price": 250000, "taux_rev": 51.9},
        {"cat": "Billet SIMPLE - 29 Mai", "web": 22, "pos_lamako": 0, "pos_client": 16, "total": 38, "brut": 9500000, "net": 9500000, "remise": 0, "unit_price": 250000, "taux_rev": 48.1}
    ],
    "cat_pay_rows": [
        {
            "cat": "Billet SIMPLE - 30 Mai",
            "cells": {
                "coupon100": {"count": 0, "brut": 0, "net": 0, "remise": 0},
                "especes_lamako": {"count": 0, "brut": 0, "net": 0, "remise": 0},
                "mvola": {"count": 4, "brut": 1000000, "net": 1000000, "remise": 0},
                "orange": {"count": 7, "brut": 1750000, "net": 1750000, "remise": 0},
                "airtel": {"count": 0, "brut": 0, "net": 0, "remise": 0},
                "especes_client": {"count": 5, "brut": 1250000, "net": 1250000, "remise": 0},
                "cheque_client": {"count": 0, "brut": 0, "net": 0, "remise": 0},
                "carte": {"count": 25, "brut": 6250000, "net": 6250000, "remise": 0},
                "autre": {"count": 0, "brut": 0, "net": 0, "remise": 0}
            },
            "total_count": 41, "total_brut": 10250000, "total_net": 10250000, "total_remise": 0
        },
        {
            "cat": "Billet SIMPLE - 29 Mai",
            "cells": {
                "coupon100": {"count": 0, "brut": 0, "net": 0, "remise": 0},
                "especes_lamako": {"count": 0, "brut": 0, "net": 0, "remise": 0},
                "mvola": {"count": 6, "brut": 1500000, "net": 1500000, "remise": 0},
                "orange": {"count": 9, "brut": 2250000, "net": 2250000, "remise": 0},
                "airtel": {"count": 0, "brut": 0, "net": 0, "remise": 0},
                "especes_client": {"count": 5, "brut": 1250000, "net": 1250000, "remise": 0},
                "cheque_client": {"count": 3, "brut": 750000, "net": 750000, "remise": 0},
                "carte": {"count": 15, "brut": 3750000, "net": 3750000, "remise": 0},
                "autre": {"count": 0, "brut": 0, "net": 0, "remise": 0}
            },
            "total_count": 38, "total_brut": 9500000, "total_net": 9500000, "total_remise": 0
        }
    ],
    "mm_breakdown": {
        "mvola": {
            "web": {"count": 0, "brut": 0, "net": 0, "remise": 0},
            "pos": {"count": 10, "brut": 2500000, "net": 2500000, "remise": 0}
        },
        "orange": {
            "web": {"count": 13, "brut": 3250000, "net": 3250000, "remise": 0},
            "pos": {"count": 3, "brut": 750000, "net": 750000, "remise": 0}
        },
        "airtel": {
            "web": {"count": 0, "brut": 0, "net": 0, "remise": 0},
            "pos": {"count": 0, "brut": 0, "net": 0, "remise": 0}
        }
    },
    "carte_breakdown": {
        "web": {"count": 31, "brut": 7750000, "net": 7750000, "remise": 0},
        "pos": {"count": 9, "brut": 2250000, "net": 2250000, "remise": 0}
    },
    "pos_client_breakdown": {
        "especes": {"count": 10, "brut": 2500000, "net": 2500000, "remise": 0},
        "cheque": {"count": 3, "brut": 750000, "net": 750000, "remise": 0},
        "mvola": {"count": 10, "brut": 2500000, "net": 2500000, "remise": 0},
        "orange": {"count": 3, "brut": 750000, "net": 750000, "remise": 0},
        "airtel": {"count": 0, "brut": 0, "net": 0, "remise": 0},
        "carte": {"count": 9, "brut": 2250000, "net": 2250000, "remise": 0},
        "coupon100": {"count": 0, "brut": 0, "net": 0, "remise": 0},
        "autre": {"count": 0, "brut": 0, "net": 0, "remise": 0}
    },
    "commissions": {
        "detail": [
            {"label": "Orange Money (Papi)", "type": "mm", "count": 13, "count_web": 13, "count_pos": 3,
             "base_brut_web": 3250000, "base_brut_pos": 750000, "base_brut": 4000000,
             "base_net_web": 3250000, "base_net_pos": 750000, "base_net": 3250000,
             "rate_comm": 2.5, "comm": 81250, "rate_ret": 6, "retrait": 195000, "total": 276250},
            {"label": "Carte Bancaire (CyberSource)", "type": "card", "count": 31, "count_web": 31, "count_pos": 9,
             "base_brut_web": 7750000, "base_brut_pos": 2250000, "base_brut": 10000000,
             "base_net_web": 7750000, "base_net_pos": 2250000, "base_net": 7750000,
             "rate_comm": 4, "comm": 310000, "rate_ret": 6, "retrait": 465000, "total": 775000}
        ],
        "total_comm": 391250,
        "total_retrait": 660000,
        "total_variable": 1051250
    },
    "frais_fixes": {"nb_tickets": 79, "frais_fixe": 800, "total": 63200},
    "reconciliation": {
        "recette_brut": 19750000, "total_remises": 0, "recette_nette": 19750000,
        "comm_variable": 1051250, "frais_fixes": 63200, "partenariat": 0,
        "cash_client": 3250000, "non_cash_client": 5500000,
        "total_deductions": 1114450, "montant_reverser": 9885550
    },
    "refunds": {
        "count": 2, "total": 750000,
        "detail": [
            {"order_id": 1047, "amount": 500000, "method": "MVOLA", "date": "2026-05-22 13:48:22",
             "reason": "Remboursement total — Double paiement : paiement MVola reçu sur compte Lamako mais confirmation API non reçue. Doublon avec commande POS #1052 (Tiffany). Remboursement MVola à effectuer manuellement."},
            {"order_id": 1140, "amount": 250000, "method": "Paiement par Carte Bancaire", "date": "2026-05-30 13:47:44",
             "reason": "Remboursement total — Paiement CB (Revolut) reçu sur compte BRED mais confirmation API non reçue. Double paiement avec commande #1095 (conservée). Remboursement BRED à effectuer manuellement au client."}
        ]
    },
    "sales_by_day": {
        "2026-05-12": 2, "2026-05-13": 3, "2026-05-14": 4, "2026-05-15": 5,
        "2026-05-16": 6, "2026-05-17": 8, "2026-05-18": 10, "2026-05-19": 7,
        "2026-05-20": 6, "2026-05-21": 5, "2026-05-22": 4, "2026-05-23": 3,
        "2026-05-24": 3, "2026-05-25": 4, "2026-05-26": 3, "2026-05-27": 2,
        "2026-05-28": 2, "2026-05-29": 1, "2026-05-30": 1
    }
}

buffer = build_pdf(data)
with open('/home/ubuntu/test_complete.pdf', 'wb') as f:
    f.write(buffer.read())
print("PDF generated: /home/ubuntu/test_complete.pdf")
