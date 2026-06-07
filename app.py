"""
Lamako PDF Server v3.0 — Premium Edition
Flask + ReportLab + Matplotlib
State-of-the-art post-event report for management.
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
import matplotlib.font_manager as fm
import numpy as np

app = Flask(__name__)

# ─── Register Raleway Font ───────────────────────────────────────────────────
FONT_DIR = os.path.join(os.path.dirname(__file__), 'fonts')
FONT_REGULAR = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'
FONT_SEMI = 'Helvetica-Bold'
RALEWAY_PATH = None

if os.path.isdir(FONT_DIR):
    for fname in os.listdir(FONT_DIR):
        if fname.endswith('.ttf'):
            fpath = os.path.join(FONT_DIR, fname)
            try:
                name = fname.replace('.ttf', '').replace('-', '')
                pdfmetrics.registerFont(TTFont(name, fpath))
                if 'Regular' in fname:
                    FONT_REGULAR = name
                    RALEWAY_PATH = fpath
                elif 'Bold' in fname:
                    FONT_BOLD = name
                elif 'SemiBold' in fname:
                    FONT_SEMI = name
            except:
                pass

# Register Raleway for matplotlib
if RALEWAY_PATH and os.path.isfile(RALEWAY_PATH):
    fm.fontManager.addfont(RALEWAY_PATH)
    plt.rcParams['font.family'] = 'Raleway'
else:
    plt.rcParams['font.family'] = 'sans-serif'

# ─── Logo path ───────────────────────────────────────────────────────────────
LOGO_PATH = os.path.join(os.path.dirname(__file__), 'logo.png')

# ─── Premium Color Palette ───────────────────────────────────────────────────
NAVY = colors.HexColor('#0F172A')
NAVY_LIGHT = colors.HexColor('#1E293B')
SLATE = colors.HexColor('#334155')
SLATE_LIGHT = colors.HexColor('#64748B')
BLUE = colors.HexColor('#3B82F6')
BLUE_DARK = colors.HexColor('#1D4ED8')
BLUE_LIGHT = colors.HexColor('#EFF6FF')
BLUE_ACCENT = colors.HexColor('#DBEAFE')
EMERALD = colors.HexColor('#059669')
EMERALD_LIGHT = colors.HexColor('#D1FAE5')
AMBER = colors.HexColor('#D97706')
AMBER_LIGHT = colors.HexColor('#FEF3C7')
RED = colors.HexColor('#DC2626')
RED_LIGHT = colors.HexColor('#FEE2E2')
GOLD = colors.HexColor('#B8860B')
GOLD_LIGHT = colors.HexColor('#FDF6E3')
TEAL = colors.HexColor('#0D9488')
TEAL_DARK = colors.HexColor('#115E59')
WHITE = colors.white
GRAY_50 = colors.HexColor('#F8FAFC')
GRAY_100 = colors.HexColor('#F1F5F9')
GRAY_200 = colors.HexColor('#E2E8F0')
GRAY_400 = colors.HexColor('#94A3B8')
GRAY_500 = colors.HexColor('#64748B')
GRAY_700 = colors.HexColor('#334155')
GRAY_900 = colors.HexColor('#0F172A')

# Chart colors
CHART_COLORS = ['#3B82F6', '#059669', '#D97706', '#DC2626', '#8B5CF6', '#EC4899', '#0D9488', '#6366F1']

# ─── Helpers ─────────────────────────────────────────────────────────────────
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
    """Premium donut chart with clean aesthetics."""
    fig, ax = plt.subplots(1, 1, figsize=(2.4, 2.4), facecolor='none')
    if sum(sizes) == 0:
        sizes = [1]
        labels = ['N/A']
        colors_list = ['#E2E8F0']

    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, autopct='%1.0f%%',
        colors=colors_list, startangle=90,
        textprops={'fontsize': 7, 'color': '#334155', 'fontweight': 'bold'},
        pctdistance=0.78,
        wedgeprops={'width': 0.55, 'edgecolor': 'white', 'linewidth': 1.5}
    )
    ax.set_title(title, fontsize=8, fontweight='bold', color='#0F172A', pad=8)
    ax.legend(labels, loc='lower center', bbox_to_anchor=(0.5, -0.22),
              fontsize=6, ncol=min(3, len(labels)), frameon=False,
              labelcolor='#334155')
    plt.tight_layout()
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    plt.savefig(tmp.name, dpi=180, bbox_inches='tight', transparent=True)
    plt.close(fig)
    return tmp.name


def make_bar_chart(dates, counts, peak_day='', title='Ventes par jour'):
    """Premium bar chart with gradient-like effect."""
    fig, ax = plt.subplots(1, 1, figsize=(5.8, 2.0), facecolor='none')
    x_labels = [d[5:] if len(d) > 5 else d for d in dates]
    bar_colors = ['#D97706' if d == peak_day else '#3B82F6' for d in dates]
    bars = ax.bar(range(len(dates)), counts, color=bar_colors, width=0.65,
                  edgecolor='white', linewidth=0.5, zorder=3)

    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels(x_labels, fontsize=5.5, rotation=45, ha='right', color='#64748B')
    ax.set_ylabel('Billets', fontsize=6.5, color='#64748B')
    ax.set_title(title, fontsize=9, fontweight='bold', color='#0F172A', pad=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E2E8F0')
    ax.spines['bottom'].set_color('#E2E8F0')
    ax.tick_params(axis='y', labelsize=6, colors='#64748B')
    ax.yaxis.grid(True, alpha=0.3, color='#E2E8F0', linestyle='--', zorder=0)
    ax.set_axisbelow(True)

    for bar, count in zip(bars, counts):
        if count > 0:
            ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.2,
                    str(count), ha='center', va='bottom', fontsize=5.5,
                    color='#334155', fontweight='bold')
    plt.tight_layout()
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    plt.savefig(tmp.name, dpi=180, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return tmp.name


def make_category_chart(cat_ch_rows, title='Ventes par catégorie'):
    """Premium horizontal bar chart with brut vs net."""
    if not cat_ch_rows:
        return None
    labels = [r.get('cat', '')[:30] for r in cat_ch_rows]
    brut = [r.get('brut', 0) / 1_000_000 for r in cat_ch_rows]
    net = [r.get('net', 0) / 1_000_000 for r in cat_ch_rows]

    fig, ax = plt.subplots(1, 1, figsize=(5.8, max(1.5, len(labels) * 0.6)), facecolor='none')
    x = np.arange(len(labels))
    width = 0.35
    ax.barh(x - width/2, brut, width, label='Recette brute', color='#3B82F6',
            edgecolor='white', linewidth=0.5)
    ax.barh(x + width/2, net, width, label='Recette nette', color='#059669',
            edgecolor='white', linewidth=0.5)
    ax.set_yticks(x)
    ax.set_yticklabels(labels, fontsize=7, color='#334155')
    ax.set_xlabel('Millions Ar', fontsize=7, color='#64748B')
    ax.set_title(title, fontsize=9, fontweight='bold', color='#0F172A', pad=8)
    ax.legend(fontsize=7, frameon=False, labelcolor='#334155')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E2E8F0')
    ax.spines['bottom'].set_color('#E2E8F0')
    ax.tick_params(axis='x', labelsize=6, colors='#64748B')
    ax.xaxis.grid(True, alpha=0.3, color='#E2E8F0', linestyle='--')
    ax.set_axisbelow(True)
    plt.tight_layout()
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    plt.savefig(tmp.name, dpi=180, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return tmp.name


# ─── Table Style Presets ─────────────────────────────────────────────────────
def premium_table_style(header_bg=NAVY, font_size=7):
    """Return a premium table style with dark header and clean rows."""
    return TableStyle([
        ('BACKGROUND', (0,0), (-1,0), header_bg),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), FONT_BOLD),
        ('FONTSIZE', (0,0), (-1,0), font_size),
        ('FONTSIZE', (0,1), (-1,-1), font_size),
        ('FONTNAME', (0,1), (-1,-1), FONT_REGULAR),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.4, GRAY_200),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, GRAY_50]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ])


def total_row_style(row_idx, bg=NAVY_LIGHT):
    """Style for total rows."""
    return [
        ('BACKGROUND', (0, row_idx), (-1, row_idx), bg),
        ('TEXTCOLOR', (0, row_idx), (-1, row_idx), WHITE),
        ('FONTNAME', (0, row_idx), (-1, row_idx), FONT_BOLD),
    ]


# ─── PDF Builder ─────────────────────────────────────────────────────────────
def build_pdf(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=12*mm,
        rightMargin=12*mm,
        topMargin=12*mm,
        bottomMargin=12*mm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('Section', parent=styles['Heading2'],
        fontName=FONT_BOLD, fontSize=11, textColor=NAVY, spaceBefore=5*mm, spaceAfter=2*mm))
    styles.add(ParagraphStyle('SubSection', parent=styles['Heading3'],
        fontName=FONT_SEMI, fontSize=9, textColor=SLATE, spaceBefore=3*mm, spaceAfter=1.5*mm))
    styles.add(ParagraphStyle('Body', parent=styles['Normal'],
        fontName=FONT_REGULAR, fontSize=7.5, textColor=GRAY_700, leading=10))
    styles.add(ParagraphStyle('Small', parent=styles['Normal'],
        fontName=FONT_REGULAR, fontSize=6.5, textColor=GRAY_500, leading=8))
    styles.add(ParagraphStyle('Footer', parent=styles['Normal'],
        fontName=FONT_REGULAR, fontSize=6.5, textColor=GRAY_400))
    styles.add(ParagraphStyle('KPILabel', parent=styles['Normal'],
        fontName=FONT_SEMI, fontSize=6, textColor=GRAY_500, leading=8))
    styles.add(ParagraphStyle('KPIValue', parent=styles['Normal'],
        fontName=FONT_BOLD, fontSize=12, textColor=NAVY, leading=14))

    elements = []
    page_width = A4[0] - 24*mm

    event = data.get('event', {})
    kpi = data.get('kpi', {})
    commissions = data.get('commissions', {})
    frais_fixes = data.get('frais_fixes', {})
    reconciliation = data.get('reconciliation', {})
    refunds = data.get('refunds', {})

    now = datetime.utcnow().strftime('%d/%m/%Y à %H:%M')

    # ─── HEADER ──────────────────────────────────────────────────────────────
    if os.path.isfile(LOGO_PATH):
        logo_cell = Image(LOGO_PATH, width=32*mm, height=16*mm)
    else:
        logo_cell = Paragraph(f'<b><font size="14" color="{NAVY.hexval()}">Ticket by LAMAKO</font></b>', styles['Body'])

    header_right = Paragraph(
        f'<b><font size="14" color="{NAVY.hexval()}">Rapport Post-Événement</font></b><br/>'
        f'<font size="7" color="{GRAY_500.hexval()}">{event.get("name", "")} — {event.get("date", "")}</font><br/>'
        f'<font size="6.5" color="{GRAY_400.hexval()}">Généré le {now}</font>',
        ParagraphStyle('RH', parent=styles['Body'], alignment=TA_RIGHT)
    )

    header_data = [[logo_cell, header_right]]
    header_table = Table(header_data, colWidths=[page_width*0.4, page_width*0.6])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 2*mm))

    # Accent line
    elements.append(HRFlowable(width='100%', thickness=2, color=NAVY, spaceBefore=0, spaceAfter=1*mm))

    # Confidential banner
    banner_data = [['DOCUMENT CONFIDENTIEL — USAGE INTERNE LAMAKO EVENTS']]
    banner = Table(banner_data, colWidths=[page_width])
    banner.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), NAVY),
        ('TEXTCOLOR', (0,0), (-1,-1), WHITE),
        ('FONTNAME', (0,0), (-1,-1), FONT_BOLD),
        ('FONTSIZE', (0,0), (-1,-1), 6.5),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(banner)
    elements.append(Spacer(1, 5*mm))

    # ─── KPI SECTION ─────────────────────────────────────────────────────────
    elements.append(Paragraph('Indicateurs Clés de Performance', styles['Section']))

    def kpi_cell(label, value, sub='', accent_color=NAVY):
        tc = accent_color.hexval() if hasattr(accent_color, 'hexval') else '#0F172A'
        content = (f'<font size="5.5" color="{GRAY_500.hexval()}">{label}</font><br/>'
                   f'<b><font size="11" color="{tc}">{value}</font></b>')
        if sub:
            content += f'<br/><font size="5.5" color="{GRAY_400.hexval()}">{sub}</font>'
        return Paragraph(content, styles['Body'])

    total_tickets = max(kpi.get('tickets_sold', 1), 1)
    kpi_row1 = [
        kpi_cell('TICKETS VENDUS', fmt(kpi.get('tickets_sold', 0)),
                 f"{fmt(kpi.get('tickets_payants',0))} payants · {fmt(kpi.get('tickets_gratuits',0))} gratuits"),
        kpi_cell('RECETTE BRUTE', fmt_ar(kpi.get('recette_brut', 0)), 'Prix catalogue total'),
        kpi_cell('TOTAL REMISES', fmt_ar(kpi.get('total_remises', 0)),
                 f"{kpi.get('nb_coupons', 0)} code(s) coupon"),
        kpi_cell('RECETTE NETTE', fmt_ar(kpi.get('recette_nette', 0)), 'Prix effectivement encaissé', BLUE_DARK),
    ]
    kpi_row2 = [
        kpi_cell('CHECK-INS', fmt(kpi.get('checkins', 0)),
                 f"{pct(kpi.get('taux_checkin',0))} de présence"),
        kpi_cell('NON PRÉSENTÉS', fmt(kpi.get('non_checkins', 0)),
                 f"{pct(100 - float(kpi.get('taux_checkin',0) or 0))} absents"),
        kpi_cell('PANIER MOYEN', fmt_ar(kpi.get('aov', 0)),
                 f"{fmt(kpi.get('nb_commandes',0))} commandes"),
        kpi_cell('MONTANT À REVERSER', fmt_ar(kpi.get('montant_reverser', 0)),
                 'Après toutes déductions', EMERALD),
    ]
    kpi_row3 = [
        kpi_cell('CANAL WEB', fmt(kpi.get('web_tickets', 0)),
                 f"{pct(round(kpi.get('web_tickets',0)/total_tickets*100,1))} des billets"),
        kpi_cell('GUICHET LAMAKO', fmt(kpi.get('pos_lamako_tickets', 0)),
                 f"{pct(round(kpi.get('pos_lamako_tickets',0)/total_tickets*100,1))}"),
        kpi_cell('GUICHET CLIENT', fmt(kpi.get('pos_client_tickets', 0)),
                 f"{pct(round(kpi.get('pos_client_tickets',0)/total_tickets*100,1))}"),
        kpi_cell('JOUR DE POINTE', kpi.get('peak_day', '—'),
                 f"{fmt(kpi.get('peak_count',0))} billets", AMBER),
    ]

    col_w = page_width / 4
    for row_data in [kpi_row1, kpi_row2, kpi_row3]:
        t = Table([row_data], colWidths=[col_w]*4, rowHeights=[20*mm])
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('RIGHTPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('BOX', (0,0), (0,0), 0.4, GRAY_200),
            ('BOX', (1,0), (1,0), 0.4, GRAY_200),
            ('BOX', (2,0), (2,0), 0.4, GRAY_200),
            ('BOX', (3,0), (3,0), 0.4, GRAY_200),
            ('BACKGROUND', (0,0), (-1,-1), GRAY_50),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.5*mm))

    # ─── VUE D'ENSEMBLE (Donut Charts) ──────────────────────────────────────
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph('Vue d\'Ensemble', styles['Section']))

    payants = kpi.get('tickets_payants', 0)
    gratuits_count = kpi.get('tickets_gratuits', 0)
    checkins = kpi.get('checkins', 0)
    absents = kpi.get('non_checkins', 0)

    try:
        pie1 = make_pie_chart(
            ['Payants', 'Gratuits'], [payants, gratuits_count],
            ['#3B82F6', '#D97706'], 'Répartition billets'
        )
        pie2 = make_pie_chart(
            ['Présents', 'Absents'], [checkins, absents],
            ['#059669', '#DC2626'], 'Taux de présence'
        )

        by_pay = data.get('by_pay', {})
        pay_labels_map = data.get('pay_labels', {})
        pay_sizes = []
        pay_names = []
        for pk, pl in pay_labels_map.items():
            count = 0
            if isinstance(by_pay.get(pk), dict):
                count = by_pay[pk].get('brut', 0)
            elif isinstance(by_pay.get(pk), (int, float)):
                count = by_pay[pk]
            if count > 0:
                pay_sizes.append(count)
                pay_names.append(pl[:15])

        pie3 = make_pie_chart(
            pay_names if pay_names else ['N/A'],
            pay_sizes if pay_sizes else [1],
            CHART_COLORS[:len(pay_names)] if pay_names else ['#E2E8F0'],
            'Modes de paiement'
        )

        pie_row = [[Image(pie1, width=53*mm, height=53*mm),
                    Image(pie2, width=53*mm, height=53*mm),
                    Image(pie3, width=53*mm, height=53*mm)]]
        pie_table = Table(pie_row, colWidths=[page_width/3]*3)
        pie_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(pie_table)
    except Exception:
        pass

    elements.append(Spacer(1, 3*mm))

    # ─── VENTES PAR JOUR ─────────────────────────────────────────────────────
    sales_by_day = data.get('sales_by_day', {})
    if sales_by_day:
        elements.append(Paragraph('Ventes par Jour', styles['Section']))
        elements.append(Paragraph(
            'Nombre de billets vendus chaque jour. La barre dorée indique le jour de pointe.',
            styles['Small']))
        elements.append(Spacer(1, 2*mm))

        try:
            sorted_days = sorted(sales_by_day.keys())
            counts = [sales_by_day[d] for d in sorted_days]
            peak = kpi.get('peak_day', '')
            bar_path = make_bar_chart(sorted_days, counts, peak)
            elements.append(Image(bar_path, width=page_width, height=50*mm))
        except Exception:
            pass
        elements.append(Spacer(1, 3*mm))

    # ─── VENTES PAR CATÉGORIE ────────────────────────────────────────────────
    cat_ch_rows = data.get('cat_ch_rows', [])
    if cat_ch_rows:
        elements.append(Paragraph('Ventes par Catégorie', styles['Section']))

        try:
            chart_path = make_category_chart(cat_ch_rows)
            if chart_path:
                elements.append(Image(chart_path, width=page_width, height=max(35*mm, len(cat_ch_rows)*15*mm)))
                elements.append(Spacer(1, 2*mm))
        except Exception:
            pass

        header = ['CATÉGORIE', 'BILLETS', 'PRIX UNIT.', 'RECETTE BRUTE', 'REMISES', 'RECETTE NETTE', 'TAUX REV.']
        table_data = [header]
        for row in cat_ch_rows:
            taux = row.get('taux_rev', 0)
            table_data.append([
                Paragraph(str(row.get('cat', '')), styles['Small']),
                fmt(row.get('total', 0)),
                fmt_ar(row.get('unit_price', 0)),
                fmt_ar(row.get('brut', 0)),
                f"- {fmt_ar(row.get('remise', 0))}" if row.get('remise', 0) else '—',
                fmt_ar(row.get('net', 0)),
                f"{taux:.1f} %" if taux else '—',
            ])
        tot_billets = sum(r.get('total', 0) for r in cat_ch_rows)
        tot_brut = sum(r.get('brut', 0) for r in cat_ch_rows)
        tot_net = sum(r.get('net', 0) for r in cat_ch_rows)
        table_data.append(['TOTAL', fmt(tot_billets), '', fmt_ar(tot_brut), '', fmt_ar(tot_net), ''])

        cw = [page_width*0.25, page_width*0.09, page_width*0.13, page_width*0.16, page_width*0.11, page_width*0.16, page_width*0.10]
        t = Table(table_data, colWidths=cw)
        base_style = premium_table_style()
        t.setStyle(base_style)
        t.setStyle(TableStyle(total_row_style(len(table_data)-1)))
        elements.append(t)
        elements.append(Spacer(1, 3*mm))

    # ─── VENTES PAR CATÉGORIE & MODE DE PAIEMENT ─────────────────────────────
    cat_pay_rows = data.get('cat_pay_rows', [])
    pay_labels = data.get('pay_labels', {})
    if cat_pay_rows and pay_labels:
        elements.append(Paragraph('Ventes par Catégorie & Mode de Paiement', styles['Section']))

        pay_keys = list(pay_labels.keys())
        short_labels = {
            'coupon100': 'COUPON', 'especes_lamako': 'ESP.\nLAM.',
            'cheque_lamako': 'CHQ.\nLAM.', 'mvola': 'MVOLA',
            'orange': 'ORANGE', 'airtel': 'AIRTEL',
            'especes_client': 'ESP.\nCLI.', 'cheque_client': 'CHQ.\nCLI.',
            'carte': 'CARTE', 'autre': 'AUTRE',
        }
        header_row = ['CATÉGORIE'] + [short_labels.get(k, k[:6]) for k in pay_keys] + ['TOT.', 'BRUT']
        table_data = [header_row]

        for row in cat_pay_rows:
            cat_name = row.get('cat', '')
            cells = row.get('cells', {})
            r = [Paragraph(cat_name[:25], styles['Small'])]
            for pk in pay_keys:
                cell_data = cells.get(pk, {})
                count = cell_data.get('count', 0) if isinstance(cell_data, dict) else 0
                brut = cell_data.get('brut', 0) if isinstance(cell_data, dict) else 0
                if count > 0:
                    r.append(f"{fmt(brut)}")
                else:
                    r.append('—')
            r.append(fmt(row.get('total_count', 0)))
            r.append(fmt(row.get('total_brut', 0)))
            table_data.append(r)

        # Total row
        col_totals = data.get('col_totals', {})
        total_row_data = ['TOTAL']
        for pk in pay_keys:
            ct = col_totals.get(pk, {})
            brut = ct.get('brut', 0) if isinstance(ct, dict) else 0
            total_row_data.append(fmt(brut) if brut > 0 else '—')
        total_row_data.append(fmt(sum(r.get('total_count', 0) for r in cat_pay_rows)))
        total_row_data.append(fmt(sum(r.get('total_brut', 0) for r in cat_pay_rows)))
        table_data.append(total_row_data)

        n_cols = len(header_row)
        cw = [page_width * 0.16] + [page_width * 0.84 / (n_cols - 1)] * (n_cols - 1)
        t = Table(table_data, colWidths=cw)
        t.setStyle(premium_table_style(font_size=6))
        t.setStyle(TableStyle(total_row_style(len(table_data)-1)))
        elements.append(t)
        elements.append(Spacer(1, 3*mm))

    # ─── DÉTAIL MOBILE MONEY ─────────────────────────────────────────────────
    mm_breakdown = data.get('mm_breakdown', {})
    mm_labels = {'mvola': 'MVola', 'orange': 'Orange Money (Papi)', 'airtel': 'Airtel Money'}
    if mm_breakdown:
        elements.append(Paragraph('Détail Mobile Money (MVola · Orange · Airtel)', styles['Section']))

        header = ['OPÉRATEUR', 'BILLETS\nWEB', 'RECETTE\nWEB', 'BILLETS\nPOS', 'RECETTE\nPOS', 'TOTAL', 'RECETTE\nBRUTE', 'RECETTE\nNETTE']
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
                label, fmt(w_count), fmt_ar(w_brut) if w_brut else '—',
                fmt(p_count), fmt_ar(p_brut) if p_brut else '—',
                fmt(t_count), fmt_ar(t_brut), fmt_ar(t_net),
            ])

        table_data.append([
            'TOTAL MM', fmt(total_web_b), '—', fmt(total_pos_b), '—',
            fmt(total_all), fmt_ar(total_brut), fmt_ar(total_net)
        ])

        cw = [page_width*0.17, page_width*0.08, page_width*0.14, page_width*0.08, page_width*0.14, page_width*0.08, page_width*0.15, page_width*0.16]
        t = Table(table_data, colWidths=cw)
        t.setStyle(premium_table_style())
        t.setStyle(TableStyle(total_row_style(len(table_data)-1)))
        elements.append(t)
        elements.append(Spacer(1, 1*mm))
        elements.append(Paragraph('Ventilation Web / Guichet (POS) par opérateur Mobile Money.', styles['Small']))
        elements.append(Spacer(1, 3*mm))

    # ─── CARTE BANCAIRE ──────────────────────────────────────────────────────
    carte_breakdown = data.get('carte_breakdown', {})
    if carte_breakdown:
        elements.append(Paragraph('Carte Bancaire — Détail Web / POS', styles['Section']))

        web_cb = carte_breakdown.get('web', {})
        pos_cb = carte_breakdown.get('pos', {})
        w_count = web_cb.get('count', 0)
        p_count = pos_cb.get('count', 0)
        t_count = w_count + p_count

        header = ['CANAL', 'BILLETS', '% BILLETS', 'RECETTE BRUTE', 'RECETTE NETTE']
        table_data = [header]
        pct_w = round(w_count / max(t_count, 1) * 100) if t_count else 0
        pct_p = round(p_count / max(t_count, 1) * 100) if t_count else 0
        table_data.append(['Web (en ligne)', fmt(w_count), f'{pct_w}%', fmt_ar(web_cb.get('brut', 0)), fmt_ar(web_cb.get('net', 0))])
        table_data.append(['POS (guichet)', fmt(p_count), f'{pct_p}%', fmt_ar(pos_cb.get('brut', 0)), fmt_ar(pos_cb.get('net', 0))])
        table_data.append(['TOTAL CARTE', fmt(t_count), '100%', fmt_ar(web_cb.get('brut',0)+pos_cb.get('brut',0)), fmt_ar(web_cb.get('net',0)+pos_cb.get('net',0))])

        cw = [page_width*0.22, page_width*0.15, page_width*0.15, page_width*0.24, page_width*0.24]
        t = Table(table_data, colWidths=cw)
        t.setStyle(premium_table_style())
        t.setStyle(TableStyle(total_row_style(len(table_data)-1)))
        elements.append(t)
        elements.append(Spacer(1, 1*mm))
        elements.append(Paragraph('Paiements CB ventilés entre canal Web (en ligne) et POS (guichet).', styles['Small']))
        elements.append(Spacer(1, 3*mm))

    # ─── DÉTAIL GUICHET CLIENT ───────────────────────────────────────────────
    pos_client_breakdown = data.get('pos_client_breakdown', {})
    if pos_client_breakdown:
        elements.append(Paragraph('Détail Guichet Client — Modes de Paiement', styles['Section']))

        pc_labels = {
            'especes': 'Espèces', 'cheque': 'Chèque', 'mvola': 'MVola',
            'orange': 'Orange Money', 'airtel': 'Airtel Money',
            'carte': 'Carte Bancaire', 'coupon100': 'Coupon 100%', 'autre': 'Autre'
        }
        header = ['MODE DE PAIEMENT', 'BILLETS', '%', 'RECETTE BRUTE', 'REMISE', 'RECETTE NETTE']
        table_data = [header]
        total_b = sum(pos_client_breakdown.get(pk, {}).get('count', 0) for pk in pc_labels)

        for pk, label in pc_labels.items():
            bd = pos_client_breakdown.get(pk, {})
            count = bd.get('count', 0)
            if count > 0:
                pct_val = round(count / max(total_b, 1) * 100)
                table_data.append([
                    label, fmt(count), f'{pct_val}%',
                    fmt_ar(bd.get('brut', 0)),
                    f"- {fmt_ar(bd.get('remise', 0))}" if bd.get('remise', 0) else '—',
                    fmt_ar(bd.get('net', 0))
                ])

        tot_brut = sum(pos_client_breakdown.get(pk, {}).get('brut', 0) for pk in pc_labels)
        tot_net = sum(pos_client_breakdown.get(pk, {}).get('net', 0) for pk in pc_labels)
        table_data.append(['TOTAL GUICHET CLIENT', fmt(total_b), '100%', fmt_ar(tot_brut), '—', fmt_ar(tot_net)])

        cw = [page_width*0.22, page_width*0.10, page_width*0.08, page_width*0.20, page_width*0.16, page_width*0.24]
        t = Table(table_data, colWidths=cw)
        t.setStyle(premium_table_style())
        t.setStyle(TableStyle(total_row_style(len(table_data)-1)))
        elements.append(t)
        elements.append(Spacer(1, 3*mm))

    # ─── COMMISSIONS & FRAIS ─────────────────────────────────────────────────
    elements.append(Paragraph('Détail des Commissions & Frais Lamako', styles['Section']))

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

        cw = [page_width*0.17, page_width*0.08, page_width*0.16, page_width*0.08,
              page_width*0.14, page_width*0.08, page_width*0.14, page_width*0.15]
        t = Table(table_data, colWidths=cw)
        t.setStyle(premium_table_style())
        # Highlight total column
        for i in range(1, len(table_data)):
            t.setStyle(TableStyle([
                ('FONTNAME', (-1, i), (-1, i), FONT_BOLD),
                ('TEXTCOLOR', (-1, i), (-1, i), NAVY),
            ]))
        elements.append(t)
    else:
        elements.append(Paragraph('Aucune commission applicable (pas de ventes Web).', styles['Body']))

    elements.append(Spacer(1, 2*mm))

    # Totals summary
    total_variable = commissions.get('total_variable', 0)
    ff_total = frais_fixes.get('total', 0)
    ff_nb = frais_fixes.get('nb_tickets', 0)
    ff_unit = frais_fixes.get('frais_fixe', 800)
    total_deductions_lamako = total_variable + ff_total

    totals_data = [
        ['TOTAL COMMISSIONS VARIABLES', fmt_ar(total_variable)],
        [f'FRAIS FIXES ÉMISSION ({fmt(ff_unit)} Ar × {fmt(ff_nb)} billets)', fmt_ar(ff_total)],
        ['TOTAL DÉDUCTIONS LAMAKO', fmt_ar(total_deductions_lamako)],
    ]
    cw_t = [page_width*0.75, page_width*0.25]
    t = Table(totals_data, colWidths=cw_t)
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), FONT_BOLD),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('ALIGN', (-1,0), (-1,-1), 'RIGHT'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (-1,0), BLUE_LIGHT),
        ('BACKGROUND', (0,1), (-1,1), AMBER_LIGHT),
        ('BACKGROUND', (0,2), (-1,2), RED_LIGHT),
        ('TEXTCOLOR', (-1,0), (-1,0), BLUE_DARK),
        ('TEXTCOLOR', (-1,1), (-1,1), AMBER),
        ('TEXTCOLOR', (-1,2), (-1,2), RED),
        ('BOX', (0,0), (-1,-1), 0.4, GRAY_200),
        ('LINEBELOW', (0,0), (-1,1), 0.3, GRAY_200),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 5*mm))

    # ─── REMBOURSEMENTS ──────────────────────────────────────────────────────
    if refunds and refunds.get('count', 0) > 0:
        elements.append(Paragraph('Remboursements', styles['Section']))
        ref_summary = f"<b>{refunds.get('count', 0)}</b> remboursement(s) pour un total de <b>{fmt_ar(refunds.get('total', 0))}</b>"
        elements.append(Paragraph(ref_summary, styles['Body']))
        elements.append(Spacer(1, 2*mm))

        ref_detail = refunds.get('detail', [])
        if ref_detail:
            header = ['# CMD', 'MONTANT', 'MOYEN', 'DATE', 'RAISON']
            table_data = [header]
            for r in ref_detail:
                date_str = str(r.get('date', ''))
                if 'T' in date_str:
                    date_str = date_str.split('T')[0]
                table_data.append([
                    f"#{r.get('order_id', '')}",
                    fmt_ar(r.get('amount', 0)),
                    r.get('method', ''),
                    date_str[:16],
                    Paragraph(str(r.get('reason', ''))[:120], styles['Small']),
                ])

            cw = [page_width*0.09, page_width*0.14, page_width*0.16, page_width*0.14, page_width*0.47]
            t = Table(table_data, colWidths=cw)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), RED),
                ('TEXTCOLOR', (0,0), (-1,0), WHITE),
                ('FONTNAME', (0,0), (-1,0), FONT_BOLD),
                ('FONTSIZE', (0,0), (-1,-1), 6.5),
                ('ALIGN', (0,0), (-1,0), 'CENTER'),
                ('ALIGN', (0,1), (0,-1), 'CENTER'),
                ('ALIGN', (1,1), (1,-1), 'RIGHT'),
                ('GRID', (0,0), (-1,-1), 0.4, GRAY_200),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, GRAY_50]),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            elements.append(t)
        elements.append(Spacer(1, 5*mm))

    # ─── RÉCONCILIATION COMPTABLE ────────────────────────────────────────────
    elements.append(Paragraph('Réconciliation Comptable', styles['Section']))

    recette_brut = reconciliation.get('recette_brut', 0)
    total_remises = reconciliation.get('total_remises', 0)
    recette_nette = reconciliation.get('recette_nette', 0)
    comm_variable = reconciliation.get('comm_variable', 0)
    frais_fixes_r = reconciliation.get('frais_fixes', 0)
    partenariat = reconciliation.get('partenariat', 0)
    cash_client = reconciliation.get('cash_client', 0)
    non_cash_client = reconciliation.get('non_cash_client', 0)
    montant_reverser = reconciliation.get('montant_reverser', 0)

    comm_total = commissions.get('total_comm', 0)
    retrait_total = commissions.get('total_retrait', 0)
    sous_total_lamako = recette_nette - comm_total - retrait_total - frais_fixes_r - (partenariat or 0)
    total_client = cash_client + non_cash_client

    def recon_row(label, value, indent=False, bold=False, text_color=GRAY_700, negative=True):
        prefix = '    ' if indent else ''
        sign = '- ' if negative and value != 0 else ''
        lbl = f'<b>{prefix}{label}</b>' if bold else f'{prefix}{label}'
        val_str = f'{sign}{fmt_ar(abs(value) if negative else value)}'
        if bold:
            val_str = f'<b>{val_str}</b>'
        tc = text_color.hexval() if hasattr(text_color, 'hexval') else '#334155'
        return [
            Paragraph(lbl, ParagraphStyle('RL', parent=styles['Body'], fontSize=7.5)),
            Paragraph(val_str, ParagraphStyle('RV', parent=styles['Body'], alignment=TA_RIGHT, textColor=colors.HexColor(tc), fontSize=7.5))
        ]

    def section_hdr(text, bg=NAVY):
        return [
            Paragraph(f'<b><font color="white" size="7">{text}</font></b>', styles['Body']),
            ''
        ]

    recon_data = []
    recon_bg = []  # Track background colors

    # A — RECETTES
    recon_data.append(section_hdr('A — RECETTES'))
    recon_bg.append(NAVY)
    recon_data.append(recon_row('Recette brute (prix catalogue)', recette_brut, negative=False))
    recon_bg.append(None)
    nb_coupons = kpi.get('nb_coupons', 0)
    recon_data.append(recon_row(f'(-) Total remises coupons ({nb_coupons} code(s))', total_remises, indent=True))
    recon_bg.append(GRAY_50)
    recon_data.append(recon_row('= Recette nette encaissée', recette_nette, bold=True, negative=False, text_color=BLUE_DARK))
    recon_bg.append(BLUE_LIGHT)

    # B — DÉDUCTIONS LAMAKO
    recon_data.append(section_hdr('B — DÉDUCTIONS LAMAKO'))
    recon_bg.append(NAVY)
    recon_data.append(recon_row('(-) Commissions opérateurs MM + Carte', comm_total, indent=True))
    recon_bg.append(None)
    recon_data.append(recon_row('(-) Frais retrait opérateur', retrait_total, indent=True))
    recon_bg.append(GRAY_50)
    recon_data.append(recon_row(f'(-) Frais fixes émission ({fmt(ff_unit)} Ar × {fmt(ff_nb)} billets)', frais_fixes_r, indent=True))
    recon_bg.append(None)
    if partenariat:
        recon_data.append(recon_row('(-) Partenariat / Frais marketing', partenariat, indent=True))
        recon_bg.append(GRAY_50)
    recon_data.append(recon_row('= Sous-total après déductions Lamako', sous_total_lamako, bold=True, negative=False))
    recon_bg.append(BLUE_LIGHT)

    # C — ENCAISSEMENTS GUICHET CLIENT
    recon_data.append(section_hdr('C — ENCAISSEMENTS GUICHET CLIENT'))
    recon_bg.append(NAVY)
    if cash_client:
        recon_data.append(recon_row('(-) Espèces + chèques encaissés par Guichet Client', cash_client, indent=True))
        recon_bg.append(None)
    if non_cash_client:
        recon_data.append(recon_row('(-) Mobile Money & CB encaissés par Guichet Client', non_cash_client, indent=True))
        recon_bg.append(GRAY_50)
    if not cash_client and not non_cash_client:
        recon_data.append(recon_row('Aucun encaissement Guichet Client', 0, indent=True))
        recon_bg.append(None)

    # MONTANT NET
    recon_data.append([
        Paragraph(f'<b><font color="white" size="8">MONTANT NET À REVERSER À L\'ORGANISATEUR</font></b>', styles['Body']),
        Paragraph(f'<b><font color="white" size="9">{fmt_ar(montant_reverser)}</font></b>',
                  ParagraphStyle('MRV', parent=styles['Body'], alignment=TA_RIGHT))
    ])
    recon_bg.append(EMERALD)

    col_widths_r = [page_width*0.72, page_width*0.28]
    t = Table(recon_data, colWidths=col_widths_r)

    style_cmds = [
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 0.4, GRAY_200),
    ]

    for i, bg in enumerate(recon_bg):
        if bg:
            style_cmds.append(('BACKGROUND', (0,i), (-1,i), bg))
            if bg in (NAVY, EMERALD):
                style_cmds.append(('TEXTCOLOR', (0,i), (-1,i), WHITE))
        if i < len(recon_bg) - 1:
            style_cmds.append(('LINEBELOW', (0,i), (-1,i), 0.3, GRAY_200))

    t.setStyle(TableStyle(style_cmds))
    elements.append(t)

    # Verification formula
    elements.append(Spacer(1, 2*mm))
    total_ded_display = comm_total + retrait_total + frais_fixes_r + (partenariat or 0)
    verif = (f'<font color="{EMERALD.hexval()}"><b>✓</b></font> '
             f'Vérification : Recette nette ({fmt_ar(recette_nette)}) '
             f'– Déductions Lamako ({fmt_ar(total_ded_display)}) '
             f'– Guichet Client ({fmt_ar(total_client)}) '
             f'= <b>{fmt_ar(montant_reverser)}</b>')
    elements.append(Paragraph(verif, ParagraphStyle('Verif', parent=styles['Small'], textColor=GRAY_500)))

    # ─── FOOTER ──────────────────────────────────────────────────────────────
    elements.append(Spacer(1, 8*mm))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=GRAY_200, spaceBefore=0, spaceAfter=2*mm))
    footer_data = [[
        Paragraph('Lamako Events · Ticketbylamako.com', styles['Footer']),
        Paragraph(f'Rapport généré le {now}', ParagraphStyle('FR', parent=styles['Footer'], alignment=TA_RIGHT))
    ]]
    ft = Table(footer_data, colWidths=[page_width*0.5, page_width*0.5])
    ft.setStyle(TableStyle([('TOPPADDING', (0,0), (-1,-1), 2)]))
    elements.append(ft)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ─── Routes ──────────────────────────────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'service': 'lamako-pdf-server', 'version': '3.0-premium', 'status': 'ok'})


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
