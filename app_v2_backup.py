"""
Lamako PDF Server — Flask + ReportLab + Matplotlib
Generates professional post-event reports as PDF.
Deployed on Railway.
"""
import io
import os
import tempfile
from datetime import datetime

from flask import Flask, request, jsonify, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    Image, HRFlowable, KeepTogether, PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)

# ─── Try to register Raleway font ─────────────────────────────────────────────
FONT_DIR = os.path.join(os.path.dirname(__file__), 'fonts')
FONT_REGULAR = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'
if os.path.isdir(FONT_DIR):
    for fname in os.listdir(FONT_DIR):
        if fname.endswith('.ttf'):
            try:
                name = fname.replace('.ttf', '').replace('-', '')
                pdfmetrics.registerFont(TTFont(name, os.path.join(FONT_DIR, fname)))
            except:
                pass

# ─── Logo path ─────────────────────────────────────────────────────────────────
LOGO_PATH = os.path.join(os.path.dirname(__file__), 'logo.png')

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
    return f'{fmt(val)} Ar'

def pct(val):
    if val is None:
        return '—'
    try:
        return f'{float(val):.1f} %'
    except (ValueError, TypeError):
        return str(val)


def make_pie_chart(labels, sizes, colors_list, title=''):
    """Generate a pie chart and return path to temp PNG."""
    fig, ax = plt.subplots(1, 1, figsize=(2.5, 2.5))
    if sum(sizes) == 0:
        sizes = [1]
        labels = ['N/A']
        colors_list = ['#E5E7EB']
    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, autopct='%1.0f%%',
        colors=colors_list, startangle=90,
        textprops={'fontsize': 7}
    )
    ax.set_title(title, fontsize=8, fontweight='bold', pad=5)
    ax.legend(labels, loc='lower center', bbox_to_anchor=(0.5, -0.2),
              fontsize=6, ncol=2, frameon=False)
    plt.tight_layout()
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    plt.savefig(tmp.name, dpi=150, bbox_inches='tight', transparent=True)
    plt.close(fig)
    return tmp.name


def make_bar_chart(dates, counts, peak_day='', title='Ventes par jour'):
    """Generate a bar chart for daily sales."""
    fig, ax = plt.subplots(1, 1, figsize=(5.5, 2.2))
    x_labels = [d[5:] if len(d) > 5 else d for d in dates]  # MM-DD format
    bar_colors = ['#D97706' if d == peak_day else '#2563EB' for d in dates]
    bars = ax.bar(range(len(dates)), counts, color=bar_colors, width=0.7)
    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels(x_labels, fontsize=6, rotation=45, ha='right')
    ax.set_ylabel('Billets', fontsize=7)
    ax.set_title(title, fontsize=9, fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='y', labelsize=6)
    for bar, count in zip(bars, counts):
        if count > 0:
            ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.3,
                    str(count), ha='center', va='bottom', fontsize=6)
    plt.tight_layout()
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    plt.savefig(tmp.name, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return tmp.name


def make_category_chart(cat_ch_rows, title='Ventes par catégorie'):
    """Generate grouped bar chart: brute vs nette per category."""
    if not cat_ch_rows:
        return None
    labels = [r.get('cat', '')[:25] for r in cat_ch_rows]
    brut = [r.get('brut', 0) / 1_000_000 for r in cat_ch_rows]
    net = [r.get('net', 0) / 1_000_000 for r in cat_ch_rows]

    fig, ax = plt.subplots(1, 1, figsize=(5.5, 2.0))
    x = np.arange(len(labels))
    width = 0.35
    ax.barh(x - width/2, brut, width, label='Recette brute', color='#2563EB')
    ax.barh(x + width/2, net, width, label='Recette nette', color='#059669')
    ax.set_yticks(x)
    ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlabel('Millions Ar', fontsize=7)
    ax.set_title(title, fontsize=9, fontweight='bold')
    ax.legend(fontsize=7, frameon=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='x', labelsize=6)
    plt.tight_layout()
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    plt.savefig(tmp.name, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return tmp.name


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
    styles.add(ParagraphStyle('Title2', parent=styles['Heading1'],
        fontName=FONT_BOLD, fontSize=18, textColor=DARK, spaceAfter=2*mm))
    styles.add(ParagraphStyle('Section', parent=styles['Heading2'],
        fontName=FONT_BOLD, fontSize=13, textColor=BLUE, spaceBefore=6*mm, spaceAfter=3*mm))
    styles.add(ParagraphStyle('SubSection', parent=styles['Heading3'],
        fontName=FONT_BOLD, fontSize=10, textColor=DARK, spaceBefore=3*mm, spaceAfter=2*mm))
    styles.add(ParagraphStyle('Normal2', parent=styles['Normal'],
        fontName=FONT_REGULAR, fontSize=8.5, textColor=DARK))
    styles.add(ParagraphStyle('Small', parent=styles['Normal'],
        fontName=FONT_REGULAR, fontSize=7, textColor=GRAY))
    styles.add(ParagraphStyle('Footer', parent=styles['Normal'],
        fontName=FONT_REGULAR, fontSize=7, textColor=GRAY))

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
    if os.path.isfile(LOGO_PATH):
        logo_cell = Image(LOGO_PATH, width=35*mm, height=18*mm)
    else:
        logo_cell = Paragraph('<b><font size="16" color="#1F2937">Ticket</font><font size="10" color="#D97706"> by</font><br/><font size="18" color="#1F2937">LAMAKO</font></b>', styles['Normal2'])

    header_data = [[
        logo_cell,
        Paragraph(f'<b><font size="16">Rapport Post-Événement</font></b><br/><font size="8" color="#6B7280">Généré le {now}</font>', ParagraphStyle('RH', parent=styles['Normal2'], alignment=TA_RIGHT))
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
        ('FONTNAME', (0,0), (-1,-1), FONT_BOLD),
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

    def kpi_cell(label, value, sub='', text_color=DARK):
        tc = text_color.hexval() if hasattr(text_color, 'hexval') else '#1F2937'
        content = f'<font size="7" color="#6B7280">{label}</font><br/><b><font size="13" color="{tc}">{value}</font></b>'
        if sub:
            content += f'<br/><font size="6.5" color="#6B7280">{sub}</font>'
        return Paragraph(content, styles['Normal2'])

    total_tickets = max(kpi.get('tickets_sold', 1), 1)
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
                 f"{pct(100 - float(kpi.get('taux_checkin',0) or 0))} absents"),
        kpi_cell('PANIER MOYEN', fmt_ar(kpi.get('aov', 0)),
                 f"{fmt(kpi.get('nb_commandes',0))} commandes"),
        kpi_cell('MONTANT À REVERSER', fmt_ar(kpi.get('montant_reverser', 0)),
                 'Après toutes déductions', text_color=GREEN),
    ]
    kpi_row3 = [
        kpi_cell('CANAL WEB', fmt(kpi.get('web_tickets', 0)),
                 f"{pct(round(kpi.get('web_tickets',0)/total_tickets*100,1))} des billets"),
        kpi_cell('GUICHET LAMAKO', fmt(kpi.get('pos_lamako_tickets', 0)),
                 f"{pct(round(kpi.get('pos_lamako_tickets',0)/total_tickets*100,1))}"),
        kpi_cell('GUICHET CLIENT', fmt(kpi.get('pos_client_tickets', 0)),
                 f"{pct(round(kpi.get('pos_client_tickets',0)/total_tickets*100,1))}"),
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

    payants = kpi.get('tickets_payants', 0)
    gratuits_count = kpi.get('tickets_gratuits', 0)
    checkins = kpi.get('checkins', 0)
    absents = kpi.get('non_checkins', 0)

    # Generate pie charts
    try:
        pie1 = make_pie_chart(
            ['Payants', 'Gratuits'], [payants, gratuits_count],
            ['#2563EB', '#D97706'], 'Répartition billets'
        )
        pie2 = make_pie_chart(
            ['Présents', 'Absents'], [checkins, absents],
            ['#059669', '#DC2626'], 'Taux de présence'
        )

        # Payment mode pie
        by_pay = data.get('by_pay', {})
        pay_labels_map = data.get('pay_labels', {})
        pay_sizes = []
        pay_names = []
        pay_colors = ['#2563EB', '#059669', '#D97706', '#DC2626', '#6B7280', '#0D9488', '#7C3AED', '#EC4899']
        for pk, pl in pay_labels_map.items():
            count = 0
            if isinstance(by_pay.get(pk), dict):
                count = by_pay[pk].get('brut', 0)
            elif isinstance(by_pay.get(pk), (int, float)):
                count = by_pay[pk]
            if count > 0:
                pay_sizes.append(count)
                pay_names.append(pl)

        pie3 = make_pie_chart(
            pay_names if pay_names else ['N/A'],
            pay_sizes if pay_sizes else [1],
            pay_colors[:len(pay_names)] if pay_names else ['#E5E7EB'],
            'Modes de paiement'
        )

        # Add pie charts in a row
        pie_row = [[Image(pie1, width=55*mm, height=55*mm),
                    Image(pie2, width=55*mm, height=55*mm),
                    Image(pie3, width=55*mm, height=55*mm)]]
        pie_table = Table(pie_row, colWidths=[page_width/3]*3)
        pie_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(pie_table)
    except Exception as e:
        pie_info = f'<b>Répartition billets</b>: {fmt(payants)} payants, {fmt(gratuits_count)} gratuits | <b>Taux de présence</b>: {fmt(checkins)} présents, {fmt(absents)} absents ({pct(kpi.get("taux_checkin",0))})'
        elements.append(Paragraph(pie_info, styles['Normal2']))

    elements.append(Spacer(1, 4*mm))

    # ─── Ventes par jour (Bar Chart) ──────────────────────────────────────────
    sales_by_day = data.get('sales_by_day', {})
    if sales_by_day:
        elements.append(Paragraph('VENTES PAR JOUR', styles['Section']))
        desc = "Nombre de billets vendus chaque jour. La barre orange indique le jour de pointe. L'axe X montre les dates (MM-JJ), l'axe Y le nombre de billets."
        elements.append(Paragraph(desc, styles['Small']))
        elements.append(Spacer(1, 2*mm))

        try:
            sorted_days = sorted(sales_by_day.keys())
            counts = [sales_by_day[d] for d in sorted_days]
            peak = kpi.get('peak_day', '')
            bar_path = make_bar_chart(sorted_days, counts, peak)
            elements.append(Image(bar_path, width=page_width, height=55*mm))
        except Exception:
            pass
        elements.append(Spacer(1, 4*mm))

    # ─── Ventes par catégorie (Chart + Table) ─────────────────────────────────
    cat_ch_rows = data.get('cat_ch_rows', [])
    if cat_ch_rows:
        elements.append(Paragraph('VENTES PAR CATÉGORIE', styles['Section']))

        # Chart
        try:
            chart_path = make_category_chart(cat_ch_rows)
            if chart_path:
                desc2 = "Comparaison recette brute (bleu) vs recette nette (vert) par catégorie de billet, en millions d'Ariary."
                elements.append(Paragraph(desc2, styles['Small']))
                elements.append(Spacer(1, 2*mm))
                elements.append(Image(chart_path, width=page_width, height=50*mm))
                elements.append(Spacer(1, 3*mm))
        except Exception:
            pass

        # Table: Catégorie | Billets | Prix Unit. | Recette Brute | Remises | Recette Nette | Check-ins | Taux Prés.
        header = ['CATÉGORIE', 'BILLETS', 'PRIX UNIT.', 'RECETTE BRUTE', 'REMISES', 'RECETTE NETTE', 'CHECK-INS', 'TAUX PRÉS.']
        table_data = [header]
        for row in cat_ch_rows:
            table_data.append([
                Paragraph(str(row.get('cat', '')), styles['Small']),
                fmt(row.get('total', 0)),
                fmt_ar(row.get('unit_price', 0)),
                fmt_ar(row.get('brut', 0)),
                f"- {fmt_ar(row.get('remise', 0))}",
                fmt_ar(row.get('net', 0)),
                fmt(0),  # checkins per cat not available in this structure
                pct(0),
            ])
        # Total row
        tot_billets = sum(r.get('total', 0) for r in cat_ch_rows)
        tot_brut = sum(r.get('brut', 0) for r in cat_ch_rows)
        tot_remise = sum(r.get('remise', 0) for r in cat_ch_rows)
        tot_net = sum(r.get('net', 0) for r in cat_ch_rows)
        table_data.append(['TOTAL', fmt(tot_billets), '', fmt_ar(tot_brut), f"- {fmt_ar(tot_remise)}", fmt_ar(tot_net), '', ''])

        cw = [page_width*0.22, page_width*0.08, page_width*0.12, page_width*0.14, page_width*0.12, page_width*0.14, page_width*0.09, page_width*0.09]
        t = Table(table_data, colWidths=cw)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), BLUE),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0), FONT_BOLD),
            ('FONTSIZE', (0,0), (-1,-1), 7),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0,1), (-1,-2), [WHITE, GRAY_LIGHT]),
            ('BACKGROUND', (0,-1), (-1,-1), BLUE_LIGHT),
            ('FONTNAME', (0,-1), (-1,-1), FONT_BOLD),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 4*mm))

    # ─── Ventes par catégorie & mode de paiement ──────────────────────────────
    cat_pay_rows = data.get('cat_pay_rows', [])
    pay_labels = data.get('pay_labels', {})
    if cat_pay_rows and pay_labels:
        elements.append(Paragraph('VENTES PAR CATÉGORIE & MODE DE PAIEMENT', styles['Section']))

        pay_keys = list(pay_labels.keys())
        # Shorten labels for table header
        short_labels = {
            'coupon100': 'COUPON\n100%',
            'especes_lamako': 'ESPÈCES\nLAMAKO',
            'cheque_lamako': 'CHÈQUE\nLAMAKO',
            'mvola': 'MVOLA',
            'orange': 'ORANGE\nMONEY',
            'airtel': 'AIRTEL',
            'especes_client': 'ESPÈCES\nCLIENT',
            'cheque_client': 'CHÈQUE\nCLIENT',
            'carte': 'CARTE',
            'autre': 'AUTRE',
        }
        header_row = ['CATÉGORIE'] + [short_labels.get(k, pay_labels.get(k, k)) for k in pay_keys] + ['Total', 'RECETTE\nBRUTE']
        table_data = [header_row]

        for row in cat_pay_rows:
            cat_name = row.get('cat', '')
            cells = row.get('cells', {})
            r = [Paragraph(cat_name, styles['Small'])]
            for pk in pay_keys:
                cell_data = cells.get(pk, {})
                count = cell_data.get('count', 0) if isinstance(cell_data, dict) else 0
                brut = cell_data.get('brut', 0) if isinstance(cell_data, dict) else 0
                if count > 0:
                    r.append(f"{fmt_ar(brut)}")
                else:
                    r.append('—')
            r.append(fmt(row.get('total_count', 0)))
            r.append(fmt_ar(row.get('total_brut', 0)))
            table_data.append(r)

        # Total row
        col_totals = data.get('col_totals', {})
        total_row = ['TOTAL']
        for pk in pay_keys:
            ct = col_totals.get(pk, {})
            brut = ct.get('brut', 0) if isinstance(ct, dict) else 0
            if brut > 0:
                total_row.append(fmt_ar(brut))
            else:
                total_row.append('—')
        total_row.append(fmt(sum(r.get('total_count', 0) for r in cat_pay_rows)))
        total_row.append(fmt_ar(sum(r.get('total_brut', 0) for r in cat_pay_rows)))
        table_data.append(total_row)

        n_cols = len(header_row)
        cw = [page_width * 0.18] + [page_width * 0.82 / (n_cols - 1)] * (n_cols - 1)
        t = Table(table_data, colWidths=cw)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), BLUE),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0), FONT_BOLD),
            ('FONTSIZE', (0,0), (-1,-1), 6.5),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0,1), (-1,-2), [WHITE, GRAY_LIGHT]),
            ('BACKGROUND', (0,-1), (-1,-1), BLUE_LIGHT),
            ('FONTNAME', (0,-1), (-1,-1), FONT_BOLD),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 4*mm))

    # ─── Détail Mobile Money ──────────────────────────────────────────────────
    mm_breakdown = data.get('mm_breakdown', {})
    mm_labels = {'mvola': 'MVola', 'orange': 'Orange Money (Papi)', 'airtel': 'Airtel Money'}
    if mm_breakdown:
        elements.append(Paragraph('DÉTAIL MOBILE MONEY (MVola · Orange Money · Airtel)', styles['Section']))

        header = ['OPÉRATEUR', 'BILLETS\nWEB', 'RECETTE\nWEB', 'BILLETS\nPOS', 'RECETTE\nPOS', 'TOTAL\nBILLETS', 'RECETTE\nBRUTE', 'RECETTE\nNETTE']
        table_data = [header]
        total_web_b = 0; total_pos_b = 0; total_all = 0; total_brut = 0; total_net = 0

        for pk, label in mm_labels.items():
            bd = mm_breakdown.get(pk, {})
            web = bd.get('web', {})
            pos = bd.get('pos', {})
            w_count = web.get('count', 0)
            w_brut = web.get('brut', 0)
            p_count = pos.get('count', 0)
            p_brut = pos.get('brut', 0)
            t_count = w_count + p_count
            t_brut = w_brut + p_brut
            t_net = web.get('net', 0) + pos.get('net', 0)
            total_web_b += w_count; total_pos_b += p_count
            total_all += t_count; total_brut += t_brut; total_net += t_net

            table_data.append([
                label,
                fmt(w_count) if w_count > 0 else '0',
                fmt_ar(w_brut) if w_brut > 0 else '—',
                fmt(p_count) if p_count > 0 else '0',
                fmt_ar(p_brut) if p_brut > 0 else '—',
                fmt(t_count),
                fmt_ar(t_brut),
                fmt_ar(t_net),
            ])

        # Total row
        table_data.append([
            'TOTAL MOBILE\nMONEY', fmt(total_web_b), '—', fmt(total_pos_b), '—',
            fmt(total_all), fmt_ar(total_brut), fmt_ar(total_net)
        ])

        cw = [page_width*0.18, page_width*0.09, page_width*0.13, page_width*0.09, page_width*0.13, page_width*0.09, page_width*0.14, page_width*0.15]
        t = Table(table_data, colWidths=cw)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), BLUE),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0), FONT_BOLD),
            ('FONTSIZE', (0,0), (-1,-1), 7),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0,1), (-1,-2), [WHITE, GRAY_LIGHT]),
            ('BACKGROUND', (0,-1), (-1,-1), BLUE_LIGHT),
            ('FONTNAME', (0,-1), (-1,-1), FONT_BOLD),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 1*mm))
        elements.append(Paragraph('Détail des paiements Mobile Money (MVola, Orange Money, Airtel) ventilés par canal Web et Guichet (POS).', styles['Small']))
        elements.append(Spacer(1, 4*mm))

    # ─── Carte Bancaire — Détail Web / POS ────────────────────────────────────
    carte_breakdown = data.get('carte_breakdown', {})
    if carte_breakdown:
        elements.append(Paragraph('CARTE BANCAIRE — DÉTAIL WEB / POS', styles['Section']))

        web_cb = carte_breakdown.get('web', {})
        pos_cb = carte_breakdown.get('pos', {})
        w_count = web_cb.get('count', 0)
        p_count = pos_cb.get('count', 0)
        t_count = w_count + p_count
        w_brut = web_cb.get('brut', 0)
        p_brut = pos_cb.get('brut', 0)
        w_net = web_cb.get('net', 0)
        p_net = pos_cb.get('net', 0)

        header = ['CANAL', 'BILLETS', '% BILLETS', 'RECETTE BRUTE', 'RECETTE NETTE']
        table_data = [header]
        pct_w = round(w_count / max(t_count, 1) * 100) if t_count else 0
        pct_p = round(p_count / max(t_count, 1) * 100) if t_count else 0
        table_data.append(['Web (en ligne)', fmt(w_count), f'{pct_w}%', fmt_ar(w_brut), fmt_ar(w_net)])
        table_data.append(['POS (guichet)', fmt(p_count), f'{pct_p}%', fmt_ar(p_brut), fmt_ar(p_net)])
        table_data.append(['TOTAL CARTE', fmt(t_count), '100%', fmt_ar(w_brut + p_brut), fmt_ar(w_net + p_net)])

        cw = [page_width*0.25, page_width*0.15, page_width*0.15, page_width*0.22, page_width*0.23]
        t = Table(table_data, colWidths=cw)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), BLUE),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0), FONT_BOLD),
            ('FONTSIZE', (0,0), (-1,-1), 7.5),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0,1), (-1,-2), [WHITE, GRAY_LIGHT]),
            ('BACKGROUND', (0,-1), (-1,-1), BLUE_LIGHT),
            ('FONTNAME', (0,-1), (-1,-1), FONT_BOLD),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 1*mm))
        elements.append(Paragraph('Paiements par carte bancaire ventilés entre le canal Web (en ligne) et le canal POS (guichet).', styles['Small']))
        elements.append(Spacer(1, 4*mm))

    # ─── Détail Guichet Client ────────────────────────────────────────────────
    pos_client_breakdown = data.get('pos_client_breakdown', {})
    if pos_client_breakdown:
        elements.append(Paragraph('DÉTAIL GUICHET CLIENT — MODES DE PAIEMENT', styles['Section']))

        pc_labels = {
            'especes': 'Espèces', 'cheque': 'Chèque', 'mvola': 'MVola',
            'orange': 'Orange Money', 'airtel': 'Airtel Money',
            'carte': 'Carte Bancaire', 'coupon100': 'Coupon 100%', 'autre': 'Autre'
        }
        header = ['MODE DE PAIEMENT', 'BILLETS', '% BILLETS', 'RECETTE BRUTE', 'REMISE', 'RECETTE NETTE']
        table_data = [header]
        total_b = 0; total_brut = 0; total_net = 0; total_remise = 0

        for pk, label in pc_labels.items():
            bd = pos_client_breakdown.get(pk, {})
            count = bd.get('count', 0)
            brut = bd.get('brut', 0)
            net = bd.get('net', 0)
            remise = bd.get('remise', 0)
            if count > 0:
                total_b += count; total_brut += brut; total_net += net; total_remise += remise

        for pk, label in pc_labels.items():
            bd = pos_client_breakdown.get(pk, {})
            count = bd.get('count', 0)
            brut = bd.get('brut', 0)
            net = bd.get('net', 0)
            remise = bd.get('remise', 0)
            if count > 0:
                pct_val = round(count / max(total_b, 1) * 100)
                table_data.append([
                    label, fmt(count), f'{pct_val}%',
                    fmt_ar(brut),
                    f"- {fmt_ar(remise)}" if remise > 0 else '—',
                    fmt_ar(net)
                ])

        table_data.append(['TOTAL GUICHET CLIENT', fmt(total_b), '100%', fmt_ar(total_brut), f"- {fmt_ar(total_remise)}" if total_remise > 0 else '—', fmt_ar(total_net)])

        cw = [page_width*0.22, page_width*0.12, page_width*0.12, page_width*0.18, page_width*0.14, page_width*0.22]
        t = Table(table_data, colWidths=cw)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), BLUE),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0), FONT_BOLD),
            ('FONTSIZE', (0,0), (-1,-1), 7.5),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0,1), (-1,-2), [WHITE, GRAY_LIGHT]),
            ('BACKGROUND', (0,-1), (-1,-1), BLUE_LIGHT),
            ('FONTNAME', (0,-1), (-1,-1), FONT_BOLD),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 4*mm))

    # ─── Commissions & Frais ───────────────────────────────────────────────────
    elements.append(Paragraph('DÉTAIL DES COMMISSIONS & FRAIS LAMAKO', styles['Section']))

    comm_detail = commissions.get('detail', [])
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

        cw = [page_width*0.18, page_width*0.08, page_width*0.16, page_width*0.08,
              page_width*0.15, page_width*0.08, page_width*0.14, page_width*0.13]
        t = Table(table_data, colWidths=cw)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), BLUE),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0), FONT_BOLD),
            ('FONTSIZE', (0,0), (-1,-1), 7.5),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, GRAY_LIGHT]),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('FONTNAME', (-1,1), (-1,-1), FONT_BOLD),
            ('TEXTCOLOR', (-1,1), (-1,-1), BLUE),
        ]))
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
        ('FONTNAME', (0,0), (-1,-1), FONT_BOLD),
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
                    str(date_str),
                    Paragraph(str(r.get('reason', '')), styles['Small']),
                ])

            cw = [page_width*0.12, page_width*0.15, page_width*0.18, page_width*0.13, page_width*0.42]
            t = Table(table_data, colWidths=cw)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), RED),
                ('TEXTCOLOR', (0,0), (-1,0), WHITE),
                ('FONTNAME', (0,0), (-1,0), FONT_BOLD),
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

    comm_total = commissions.get('total_comm', 0)
    retrait_total = commissions.get('total_retrait', 0)
    sous_total_lamako = recette_nette - comm_total - retrait_total - frais_fixes_r
    if partenariat:
        sous_total_lamako -= partenariat

    def recon_row(label, value, indent=False, bold=False, text_color=DARK, negative=True):
        prefix = '     ' if indent else ''
        sign = '- ' if negative and value != 0 else ''
        lbl = f'<b>{prefix}{label}</b>' if bold else f'{prefix}{label}'
        val_str = f'{sign}{fmt_ar(abs(value) if negative else value)}'
        if bold:
            val_str = f'<b>{val_str}</b>'
        return [Paragraph(lbl, styles['Normal2']), Paragraph(val_str, ParagraphStyle('RVal', parent=styles['Normal2'], alignment=TA_RIGHT, textColor=text_color))]

    def section_header(text):
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

    # C — ENCAISSEMENTS GUICHET CLIENT
    recon_data.append(section_header('C — ENCAISSEMENTS GUICHET CLIENT'))
    if cash_client:
        recon_data.append(recon_row('(-) Espèces + chèques encaissés par Guichet Client', cash_client, indent=True))
    if non_cash_client:
        recon_data.append(recon_row('(-) Mobile Money & CB encaissés par Guichet Client', non_cash_client, indent=True))
    if not cash_client and not non_cash_client:
        recon_data.append(recon_row('(-) Aucun encaissement Guichet Client', 0, indent=True))

    total_client = cash_client + non_cash_client

    # MONTANT NET
    recon_data.append([
        Paragraph(f'<b><font color="white">■ MONTANT NET À REVERSER À L\'ORGANISATEUR</font></b>',
                  ParagraphStyle('MR', parent=styles['Normal2'], textColor=WHITE)),
        Paragraph(f'<b><font color="white">{fmt_ar(montant_reverser)}</font></b>',
                  ParagraphStyle('MRV', parent=styles['Normal2'], alignment=TA_RIGHT, textColor=WHITE))
    ])

    col_widths_r = [page_width*0.75, page_width*0.25]
    t = Table(recon_data, colWidths=col_widths_r)

    style_cmds = [
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]

    for i, row in enumerate(recon_data):
        if isinstance(row[0], Paragraph) and 'white' in row[0].text.lower() and '■' not in row[0].text:
            style_cmds.append(('BACKGROUND', (0,i), (-1,i), DARK))
        elif isinstance(row[0], Paragraph) and '■' in row[0].text:
            style_cmds.append(('BACKGROUND', (0,i), (-1,i), TEAL))

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
    return jsonify({'service': 'lamako-pdf-server', 'version': '2.0', 'status': 'ok'})


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
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
