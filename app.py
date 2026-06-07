"""
Lamako PDF Server — Flask + ReportLab
Generates professional post-event reports as PDF.
Deployed on Railway.
"""
import io
import os
from datetime import datetime

from flask import Flask, request, jsonify, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    Image, HRFlowable, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Wedge, String, Circle
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF

app = Flask(__name__)

# ─── Colors ────────────────────────────────────────────────────────────────────
BLUE = colors.HexColor('#2563EB')
BLUE_LIGHT = colors.HexColor('#EFF6FF')
BLUE_MED = colors.HexColor('#DBEAFE')
GREEN = colors.HexColor('#059669')
GREEN_LIGHT = colors.HexColor('#D1FAE5')
RED = colors.HexColor('#DC2626')
RED_LIGHT = colors.HexColor('#FEE2E2')
ORANGE = colors.HexColor('#D97706')
ORANGE_LIGHT = colors.HexColor('#FEF3C7')
DARK = colors.HexColor('#1F2937')
GRAY = colors.HexColor('#6B7280')
GRAY_LIGHT = colors.HexColor('#F3F4F6')
WHITE = colors.white
TEAL = colors.HexColor('#0D9488')
TEAL_DARK = colors.HexColor('#115E59')

# ─── Helpers ───────────────────────────────────────────────────────────────────
def fmt(val):
    """Format number with space thousands separator."""
    if val is None or val == '':
        return '—'
    try:
        n = float(val)
        if n == int(n):
            n = int(n)
        return f'{n:,.0f}'.replace(',', ' ')
    except (ValueError, TypeError):
        return str(val)

def fmt_ar(val):
    """Format as Ariary amount."""
    return f'{fmt(val)} Ar'

def pct(val):
    """Format percentage."""
    if val is None:
        return '—'
    try:
        return f'{float(val):.1f} %'
    except (ValueError, TypeError):
        return str(val)


# ─── PDF Builder ───────────────────────────────────────────────────────────────
def build_pdf(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        'Title2', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=18, textColor=DARK,
        spaceAfter=2*mm
    ))
    styles.add(ParagraphStyle(
        'Section', parent=styles['Heading2'],
        fontName='Helvetica-Bold', fontSize=13, textColor=BLUE,
        spaceBefore=6*mm, spaceAfter=3*mm
    ))
    styles.add(ParagraphStyle(
        'SubSection', parent=styles['Heading3'],
        fontName='Helvetica-Bold', fontSize=10, textColor=DARK,
        spaceBefore=3*mm, spaceAfter=2*mm
    ))
    styles.add(ParagraphStyle(
        'Normal2', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.5, textColor=DARK
    ))
    styles.add(ParagraphStyle(
        'Small', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7, textColor=GRAY
    ))
    styles.add(ParagraphStyle(
        'Footer', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7, textColor=GRAY
    ))

    elements = []
    page_width = A4[0] - 30*mm

    event = data.get('event', {})
    kpi = data.get('kpi', {})
    commissions = data.get('commissions', {})
    frais_fixes = data.get('frais_fixes', {})
    reconciliation = data.get('reconciliation', {})
    refunds = data.get('refunds', {})
    params = data.get('params', {})

    now = datetime.utcnow().strftime('%d/%m/%Y à %H:%M')

    # ─── Header ────────────────────────────────────────────────────────────────
    header_data = [[
        Paragraph('<b><font size="16" color="#1F2937">Ticket</font><font size="10" color="#D97706"> by</font><br/><font size="18" color="#1F2937">LAMAKO</font></b>', styles['Normal2']),
        Paragraph(f'<b><font size="16">Rapport Post-Événement</font></b><br/><font size="8" color="#6B7280">Généré le {now}</font>', ParagraphStyle('RightHeader', parent=styles['Normal2'], alignment=TA_RIGHT))
    ]]
    header_table = Table(header_data, colWidths=[page_width*0.5, page_width*0.5])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 3*mm))

    # Confidential banner
    banner_data = [['DOCUMENT CONFIDENTIEL — USAGE INTERNE LAMAKO EVENTS']]
    banner = Table(banner_data, colWidths=[page_width])
    banner.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), DARK),
        ('TEXTCOLOR', (0,0), (-1,-1), WHITE),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(banner)
    elements.append(Spacer(1, 5*mm))

    # ─── KPI Section ───────────────────────────────────────────────────────────
    elements.append(Paragraph('Indicateurs Clés de Performance', styles['Section']))

    def kpi_cell(label, value, sub='', bg=WHITE, text_color=DARK):
        content = f'<font size="7" color="#6B7280">{label}</font><br/><b><font size="13" color="{text_color.hexval() if hasattr(text_color, "hexval") else "#1F2937"}">{value}</font></b>'
        if sub:
            content += f'<br/><font size="6.5" color="#6B7280">{sub}</font>'
        return Paragraph(content, styles['Normal2'])

    kpi_row1 = [
        kpi_cell('TICKETS VENDUS', fmt(kpi.get('tickets_sold', 0)),
                 f"{fmt(kpi.get('tickets_payants',0))} payants · {fmt(kpi.get('tickets_gratuits',0))} gratuits"),
        kpi_cell('RECETTE BRUTE', fmt_ar(kpi.get('recette_brut', 0)), 'Prix catalogue total'),
        kpi_cell('TOTAL REMISES', fmt_ar(kpi.get('total_remises', 0)),
                 f"{kpi.get('nb_coupons', 0)} code(s) coupon"),
        kpi_cell('RECETTE NETTE', fmt_ar(kpi.get('recette_nette', 0)), 'Prix effectivement encaissé'),
    ]
    kpi_row2 = [
        kpi_cell('CHECK-INS', fmt(kpi.get('checkins', 0)),
                 f"{pct(kpi.get('taux_checkin',0))} de présence"),
        kpi_cell('NON PRÉSENTÉS', fmt(kpi.get('non_checkins', 0)),
                 f"{pct(100 - float(kpi.get('taux_checkin',0)) if kpi.get('taux_checkin') else 0)} absents"),
        kpi_cell('PANIER MOYEN', fmt_ar(kpi.get('aov', 0)),
                 f"{fmt(kpi.get('nb_commandes',0))} commandes"),
        kpi_cell('MONTANT À REVERSER', fmt_ar(kpi.get('montant_reverser', 0)),
                 'Après toutes déductions', bg=GREEN_LIGHT, text_color=GREEN),
    ]
    kpi_row3 = [
        kpi_cell('CANAL WEB', fmt(kpi.get('web_tickets', 0)),
                 f"{pct(round(kpi.get('web_tickets',0)/max(kpi.get('tickets_sold',1),1)*100,1))} des billets"),
        kpi_cell('GUICHET LAMAKO', fmt(kpi.get('pos_lamako_tickets', 0)),
                 f"{pct(round(kpi.get('pos_lamako_tickets',0)/max(kpi.get('tickets_sold',1),1)*100,1))}"),
        kpi_cell('GUICHET CLIENT', fmt(kpi.get('pos_client_tickets', 0)),
                 f"{pct(round(kpi.get('pos_client_tickets',0)/max(kpi.get('tickets_sold',1),1)*100,1))}"),
        kpi_cell('JOUR DE POINTE', kpi.get('peak_day', '—'),
                 f"{fmt(kpi.get('peak_count',0))} billets"),
    ]

    col_w = page_width / 4
    for row_data in [kpi_row1, kpi_row2, kpi_row3]:
        t = Table([row_data], colWidths=[col_w]*4, rowHeights=[22*mm])
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('BOX', (0,0), (0,0), 0.5, colors.HexColor('#E5E7EB')),
            ('BOX', (1,0), (1,0), 0.5, colors.HexColor('#E5E7EB')),
            ('BOX', (2,0), (2,0), 0.5, colors.HexColor('#E5E7EB')),
            ('BOX', (3,0), (3,0), 0.5, colors.HexColor('#E5E7EB')),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 1*mm))

    # ─── Vue d'ensemble (Pie Charts) ──────────────────────────────────────────
    elements.append(Paragraph('VUE D\'ENSEMBLE', styles['Section']))

    # Pie chart - Répartition billets
    payants = kpi.get('tickets_payants', 0)
    gratuits = kpi.get('tickets_gratuits', 0)
    total_tickets = kpi.get('tickets_sold', 1)

    # Pie chart - Taux de présence
    checkins = kpi.get('checkins', 0)
    absents = kpi.get('non_checkins', 0)

    pie_info = f'<b>Répartition billets</b>: {fmt(payants)} payants, {fmt(gratuits)} gratuits | <b>Taux de présence</b>: {fmt(checkins)} présents, {fmt(absents)} absents ({pct(kpi.get("taux_checkin",0))})'
    elements.append(Paragraph(pie_info, styles['Normal2']))
    elements.append(Spacer(1, 4*mm))

    # ─── Ventes par catégorie ──────────────────────────────────────────────────
    elements.append(Paragraph('VENTES PAR CATÉGORIE', styles['Section']))

    # Cat/Pay table if available
    cat_pay_rows = data.get('cat_pay_rows', [])
    if cat_pay_rows:
        pay_labels = data.get('pay_labels', {})
        pay_keys = list(pay_labels.keys()) if pay_labels else []
        header_row = ['Catégorie'] + [pay_labels.get(k, k) for k in pay_keys] + ['Total']
        table_data = [header_row]
        for row in cat_pay_rows:
            r = [row.get('label', '')]
            for pk in pay_keys:
                r.append(fmt(row.get('pays', {}).get(pk, {}).get('count', 0)))
            r.append(fmt(row.get('total_count', 0)))
            table_data.append(r)

        n_cols = len(header_row)
        col_widths = [page_width * 0.25] + [page_width * 0.75 / (n_cols - 1)] * (n_cols - 1)
        t = Table(table_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), BLUE),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, GRAY_LIGHT]),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 4*mm))

    # ─── Commissions & Frais ───────────────────────────────────────────────────
    elements.append(Paragraph('DÉTAIL DES COMMISSIONS & FRAIS LAMAKO', styles['Section']))

    comm_detail = commissions.get('detail', [])
    # Filter out rows with 0 count (no web tickets)
    comm_rows = [r for r in comm_detail if r.get('count', 0) > 0 or r.get('comm', 0) > 0]

    if comm_rows:
        header = ['OPÉRATEUR', 'BILLETS\nWEB', 'BASE NETTE\nWEB', 'TAUX\nCOMM.', 'COMMISSION', 'TAUX\nRETRAIT', 'FRAIS\nRETRAIT', 'TOTAL']
        table_data = [header]
        for r in comm_rows:
            table_data.append([
                r.get('label', ''),
                fmt(r.get('count', 0)),
                fmt_ar(r.get('base_net', 0)),
                pct(r.get('rate_comm', 0)),
                fmt_ar(r.get('comm', 0)),
                pct(r.get('rate_ret', 0)),
                fmt_ar(r.get('retrait', 0)),
                fmt_ar(r.get('total', 0)),
            ])

        col_widths = [page_width*0.18, page_width*0.08, page_width*0.16, page_width*0.08,
                      page_width*0.15, page_width*0.08, page_width*0.14, page_width*0.13]
        t = Table(table_data, colWidths=col_widths)
        style_cmds = [
            ('BACKGROUND', (0,0), (-1,0), BLUE),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 7.5),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, GRAY_LIGHT]),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            # Total column bold
            ('FONTNAME', (-1,1), (-1,-1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (-1,1), (-1,-1), BLUE),
        ]
        t.setStyle(TableStyle(style_cmds))
        elements.append(t)
    else:
        elements.append(Paragraph('Aucune commission applicable (pas de ventes Web).', styles['Normal2']))

    elements.append(Spacer(1, 2*mm))

    # Totals row
    total_variable = commissions.get('total_variable', 0)
    ff_total = frais_fixes.get('total', 0)
    ff_nb = frais_fixes.get('nb_tickets', 0)
    ff_unit = frais_fixes.get('frais_fixe', 800)
    total_deductions_lamako = total_variable + ff_total

    totals_data = [
        ['TOTAL COMMISSIONS VARIABLES', '', '', '', '', '', '', fmt_ar(total_variable)],
        [f'FRAIS FIXES ÉMISSION ({fmt(ff_unit)} Ar × {fmt(ff_nb)} billets)', '', '', '', '', '', '', fmt_ar(ff_total)],
        ['TOTAL DÉDUCTIONS LAMAKO', '', '', '', '', '', '', fmt_ar(total_deductions_lamako)],
    ]
    col_widths_t = [page_width*0.87, 0, 0, 0, 0, 0, 0, page_width*0.13]
    t = Table(totals_data, colWidths=col_widths_t)
    t.setStyle(TableStyle([
        ('SPAN', (0,0), (6,0)),
        ('SPAN', (0,1), (6,1)),
        ('SPAN', (0,2), (6,2)),
        ('BACKGROUND', (0,0), (-1,0), BLUE_LIGHT),
        ('BACKGROUND', (0,1), (-1,1), ORANGE_LIGHT),
        ('BACKGROUND', (0,2), (-1,2), RED_LIGHT),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('ALIGN', (-1,0), (-1,-1), 'RIGHT'),
        ('TEXTCOLOR', (-1,0), (-1,0), BLUE),
        ('TEXTCOLOR', (-1,1), (-1,1), ORANGE),
        ('TEXTCOLOR', (-1,2), (-1,2), RED),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
        ('LINEBELOW', (0,0), (-1,0), 0.5, colors.HexColor('#E5E7EB')),
        ('LINEBELOW', (0,1), (-1,1), 0.5, colors.HexColor('#E5E7EB')),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 6*mm))

    # ─── Remboursements ────────────────────────────────────────────────────────
    if refunds and refunds.get('count', 0) > 0:
        elements.append(Paragraph('REMBOURSEMENTS', styles['Section']))

        ref_summary = f"<b>{refunds.get('count', 0)}</b> remboursement(s) pour un total de <b>{fmt_ar(refunds.get('total', 0))}</b>"
        elements.append(Paragraph(ref_summary, styles['Normal2']))
        elements.append(Spacer(1, 2*mm))

        ref_detail = refunds.get('detail', [])
        if ref_detail:
            header = ['# Commande', 'Montant', 'Moyen paiement', 'Date', 'Raison']
            table_data = [header]
            for r in ref_detail:
                date_str = r.get('date', '')
                if date_str and 'T' in str(date_str):
                    date_str = str(date_str).split('T')[0]
                table_data.append([
                    f"#{r.get('order_id', '')}",
                    fmt_ar(r.get('amount', 0)),
                    r.get('method', ''),
                    date_str,
                    Paragraph(str(r.get('reason', '')), styles['Small']),
                ])

            col_widths = [page_width*0.12, page_width*0.15, page_width*0.18, page_width*0.13, page_width*0.42]
            t = Table(table_data, colWidths=col_widths)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), RED),
                ('TEXTCOLOR', (0,0), (-1,0), WHITE),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 7.5),
                ('ALIGN', (0,0), (-1,0), 'CENTER'),
                ('ALIGN', (0,1), (0,-1), 'CENTER'),
                ('ALIGN', (1,1), (1,-1), 'RIGHT'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, GRAY_LIGHT]),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            elements.append(t)

        elements.append(Spacer(1, 6*mm))

    # ─── Réconciliation Comptable ──────────────────────────────────────────────
    elements.append(Paragraph('RÉCONCILIATION COMPTABLE', styles['Section']))

    recette_brut = reconciliation.get('recette_brut', reconciliation.get('recette_nette', 0))
    total_remises = reconciliation.get('total_remises', 0)
    recette_nette = reconciliation.get('recette_nette', 0)
    comm_variable = reconciliation.get('comm_variable', 0)
    frais_fixes_r = reconciliation.get('frais_fixes', 0)
    partenariat = reconciliation.get('partenariat', 0)
    cash_lamako = reconciliation.get('cash_lamako', 0)
    cash_client = reconciliation.get('cash_client', 0)
    non_cash_client = reconciliation.get('non_cash_client', 0)
    total_deductions = reconciliation.get('total_deductions', 0)
    montant_reverser = reconciliation.get('montant_reverser', 0)

    # Lamako Rewards
    rewards_enabled = reconciliation.get('lamako_rewards_enabled', False)
    rewards_discount = reconciliation.get('lamako_rewards_discount', 0)
    rewards_org_share = reconciliation.get('lamako_rewards_organizer_share', 0)
    rewards_tbl_share = reconciliation.get('lamako_rewards_tbl_share', 0)

    # Sous-total after Lamako deductions
    comm_total = commissions.get('total_comm', 0)
    retrait_total = commissions.get('total_retrait', 0)
    sous_total_lamako = recette_nette - comm_total - retrait_total - frais_fixes_r
    if partenariat:
        sous_total_lamako -= partenariat

    def recon_row(label, value, indent=False, bold=False, bg=WHITE, text_color=DARK, negative=True):
        prefix = '     ' if indent else ''
        sign = '- ' if negative and value != 0 else ''
        lbl = f'<b>{prefix}{label}</b>' if bold else f'{prefix}{label}'
        val_str = f'{sign}{fmt_ar(abs(value) if negative else value)}'
        if bold:
            val_str = f'<b>{val_str}</b>'
        return [Paragraph(lbl, styles['Normal2']), Paragraph(val_str, ParagraphStyle('RVal', parent=styles['Normal2'], alignment=TA_RIGHT, textColor=text_color))]

    def section_header(text, bg=DARK):
        return [Paragraph(f'<b><font color="white">{text}</font></b>', ParagraphStyle('SH', parent=styles['Normal2'], textColor=WHITE)), '']

    recon_data = []

    # A — RECETTES
    recon_data.append(section_header('A — RECETTES'))
    recon_data.append(recon_row('Recette brute (prix catalogue)', recette_brut, negative=False))
    nb_coupons = kpi.get('nb_coupons', 0)
    recon_data.append(recon_row(f'(-) Total remises coupons ({nb_coupons} code(s))', total_remises, indent=True))
    recon_data.append(recon_row('= Recette nette encaissée', recette_nette, bold=True, negative=False, text_color=BLUE))

    # B — DÉDUCTIONS LAMAKO
    recon_data.append(section_header('B — DÉDUCTIONS LAMAKO'))
    recon_data.append(recon_row('(-) Commissions opérateurs MM + Carte', comm_total, indent=True))
    recon_data.append(recon_row('(-) Frais retrait opérateur', retrait_total, indent=True))
    recon_data.append(recon_row(f'(-) Frais fixes émission billets ({fmt(ff_unit)} Ar × {fmt(ff_nb)} billets)', frais_fixes_r, indent=True))
    if partenariat:
        recon_data.append(recon_row('(-) Partenariat / Frais marketing', partenariat, indent=True))
    recon_data.append(recon_row('= Sous-total après déductions Lamako', sous_total_lamako, bold=True, negative=False))

    # C — ESPÈCES & ENCAISSEMENTS GUICHET CLIENT
    recon_data.append(section_header('C — ENCAISSEMENTS GUICHET CLIENT'))
    if cash_client:
        recon_data.append(recon_row('(-) Espèces + chèques encaissés par Guichet Client', cash_client, indent=True))
    if non_cash_client:
        recon_data.append(recon_row('(-) Mobile Money & CB encaissés par Guichet Client', non_cash_client, indent=True))
    if not cash_client and not non_cash_client:
        recon_data.append(recon_row('(-) Aucun encaissement Guichet Client', 0, indent=True))

    total_client = cash_client + non_cash_client

    # D — LAMAKO REWARDS (if enabled)
    if rewards_enabled and rewards_discount > 0:
        recon_data.append(section_header('D — LAMAKO REWARDS'))
        recon_data.append(recon_row(f'(-) Remises Lamako Rewards (part organisateur)', rewards_org_share, indent=True))

    # MONTANT NET
    recon_data.append([
        Paragraph(f'<b><font color="white">■ MONTANT NET À REVERSER À L\'ORGANISATEUR</font></b>',
                  ParagraphStyle('MR', parent=styles['Normal2'], textColor=WHITE)),
        Paragraph(f'<b><font color="white">{fmt_ar(montant_reverser)}</font></b>',
                  ParagraphStyle('MRV', parent=styles['Normal2'], alignment=TA_RIGHT, textColor=WHITE))
    ])

    col_widths = [page_width*0.75, page_width*0.25]
    t = Table(recon_data, colWidths=col_widths)

    # Build style
    style_cmds = [
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]

    # Color section headers and final row
    for i, row in enumerate(recon_data):
        if isinstance(row[0], Paragraph) and 'white' in row[0].text.lower() and '■' not in row[0].text:
            style_cmds.append(('BACKGROUND', (0,i), (-1,i), DARK))
            style_cmds.append(('SPAN', (0,i), (-1,i)) if row[1] == '' else ('BACKGROUND', (0,i), (-1,i), DARK))
        elif isinstance(row[0], Paragraph) and '■' in row[0].text:
            style_cmds.append(('BACKGROUND', (0,i), (-1,i), TEAL))

    # Alternate row backgrounds for non-header rows
    row_idx = 0
    for i, row in enumerate(recon_data):
        is_header = isinstance(row[0], Paragraph) and ('white' in row[0].text.lower())
        if not is_header:
            if row_idx % 2 == 1:
                style_cmds.append(('BACKGROUND', (0,i), (-1,i), GRAY_LIGHT))
            row_idx += 1

    style_cmds.append(('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')))
    style_cmds.append(('LINEBELOW', (0,0), (-1,-2), 0.3, colors.HexColor('#E5E7EB')))

    t.setStyle(TableStyle(style_cmds))
    elements.append(t)

    # Verification formula
    elements.append(Spacer(1, 2*mm))
    total_ded_display = comm_total + retrait_total + frais_fixes_r + (partenariat or 0)
    verif = (f'✓ Vérification : Recette nette ({fmt_ar(recette_nette)}) '
             f'– Déductions Lamako ({fmt_ar(total_ded_display)}) '
             f'– Guichet Client ({fmt_ar(total_client)}) '
             f'= <b>{fmt_ar(montant_reverser)}</b>')
    elements.append(Paragraph(verif, ParagraphStyle('Verif', parent=styles['Small'], textColor=GREEN)))

    # ─── Footer ────────────────────────────────────────────────────────────────
    elements.append(Spacer(1, 8*mm))
    footer_data = [[
        Paragraph('Lamako Events · Ticketbylamako.com', styles['Footer']),
        Paragraph(f'Rapport généré le {now}', ParagraphStyle('FR', parent=styles['Footer'], alignment=TA_RIGHT))
    ]]
    ft = Table(footer_data, colWidths=[page_width*0.5, page_width*0.5])
    ft.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 0.5, GRAY),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(ft)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ─── Routes ────────────────────────────────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'service': 'lamako-pdf-server', 'status': 'ok'})


@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json(force=True) or {}
        buffer = build_pdf(data)
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=False,
            download_name='rapport_lamako.pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
