import os
import io
import re
from datetime import datetime
from PIL import Image

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from django.conf import settings

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
)
from reportlab.platypus import Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas

from assets.models import Asset, AssetUnit, Category, Employee, AssetAssignment, UnitLog

@login_required
def asset_export_pdf(request):
    """Generate a professional PDF report of all assets."""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm, cm
    from reportlab.lib.colors import HexColor, white, black
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.platypus import PageBreak
    from io import BytesIO
    import locale
    
    active_tab = request.GET.get('tab', 'karyawan')
    
    # Query assets
    assets = Asset.objects.select_related('category').annotate(
        unit_tersedia=Count('units', filter=Q(units__status='tersedia')),
        unit_digunakan=Count('units', filter=Q(units__status='digunakan')),
        total_units=Count('units'),
    )
    
    if active_tab == 'network':
        assets = assets.filter(category__name__icontains='Network')
        category_label = 'Aset Network & Infrastruktur'
    else:
        assets = assets.filter(category__name__icontains='Karyawan')
        category_label = 'Aset Karyawan'
    
    assets = assets.order_by('asset_code')
    
    # Colors
    navy = HexColor('#002060')
    light_navy = HexColor('#003399')
    header_bg = HexColor('#E8EDF5')
    alt_row = HexColor('#F8F9FC')
    border_color = HexColor('#D0D5DD')
    green = HexColor('#16A34A')
    amber = HexColor('#D97706')
    
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.5*cm,
        rightMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=2*cm,
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=white,
        leading=20,
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=HexColor('#B0C4DE'),
        leading=14,
    )
    
    company_style = ParagraphStyle(
        'CompanyName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=white,
        alignment=TA_RIGHT,
        leading=14,
    )
    
    company_sub_style = ParagraphStyle(
        'CompanySub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=HexColor('#B0C4DE'),
        alignment=TA_RIGHT,
        leading=11,
    )
    
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
    )
    
    cell_bold_style = ParagraphStyle(
        'CellBoldStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
    )
    
    cell_center = ParagraphStyle(
        'CellCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        alignment=TA_CENTER,
        leading=12,
    )
    
    cell_center_bold = ParagraphStyle(
        'CellCenterBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        alignment=TA_CENTER,
        leading=12,
    )
    
    header_cell = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=white,
        alignment=TA_CENTER,
        leading=11,
    )
    
    elements = []
    
    # --- HEADER BANNER ---
    from datetime import datetime as dt
    now = dt.now()
    
    # Month names in Indonesian
    bulan_indo = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    tanggal_str = f"{now.day} {bulan_indo[now.month]} {now.year}"
    
    page_width = landscape(A4)[0] - 3*cm
    
    # LOGOS
    import os
    from reportlab.platypus import Image as RLImage
    from PIL import Image
    
    # Try to load logos, fallback gracefully if not found
    try:
        from django.conf import settings
        it_logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'it_all_role_logo.png')
        kerinci_logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'kerinci_logo.png')
        
        desired_height = 1.3 * cm
        
        it_img = Image.open(it_logo_path)
        it_width = desired_height * (it_img.width / float(it_img.height))
        it_rl_img = RLImage(it_logo_path, width=it_width, height=desired_height)
        
        ker_img = Image.open(kerinci_logo_path)
        ker_width = desired_height * (ker_img.width / float(ker_img.height))
        ker_rl_img = RLImage(kerinci_logo_path, width=ker_width, height=desired_height)
        
        logo_data = [[ker_rl_img, it_rl_img]]
        logo_table = Table(logo_data, colWidths=[page_width/2, page_width/2])
        logo_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(logo_table)
    except Exception as e:
        print("Logo error:", e)
        pass # If images missing, just skip logos
    
    header_data = [[
        [Paragraph('Laporan Daftar Aset', title_style),
         Paragraph(f'{category_label} - {tanggal_str}', subtitle_style)],
        [Paragraph('SISTEM MANAJEMEN ASET IT', company_style),
         Paragraph('Dicetak otomatis dari sistem', company_sub_style)],
    ]]
    
    header_table = Table(header_data, colWidths=[page_width * 0.65, page_width * 0.35])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), navy),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 20),
        ('RIGHTPADDING', (-1, -1), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('ROUNDEDCORNERS', [6, 6, 0, 0]),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8*mm))
    
    # --- INFO SECTION ---
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=HexColor('#555555'),
        leading=13,
    )
    info_bold = ParagraphStyle(
        'InfoBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=HexColor('#333333'),
        leading=13,
    )
    
    total_aset = assets.count()
    total_unit = sum(a.total_units for a in assets)
    total_tersedia = sum(a.unit_tersedia for a in assets)
    total_digunakan = sum(a.unit_digunakan for a in assets)
    
    info_data = [
        [Paragraph('Kategori', info_style), Paragraph(f': {category_label}', info_bold),
         Paragraph('Total Aset', info_style), Paragraph(f': {total_aset} jenis', info_bold)],
        [Paragraph('Tanggal Cetak', info_style), Paragraph(f': {tanggal_str}, {now.strftime("%H:%M")} WIB', info_bold),
         Paragraph('Total Unit', info_style), Paragraph(f': {total_unit} unit ({total_tersedia} tersedia, {total_digunakan} digunakan)', info_bold)],
    ]
    
    info_table = Table(info_data, colWidths=[page_width*0.12, page_width*0.38, page_width*0.12, page_width*0.38])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(info_table)
    
    elements.append(Spacer(1, 6*mm))
    
    # Separator line
    elements.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceAfter=4*mm))
    
    # --- ASSET TABLE ---
    # Table header
    table_header = [
        Paragraph('NO', header_cell),
        Paragraph('KODE', header_cell),
        Paragraph('NAMA ASET', header_cell),
        Paragraph('MEREK', header_cell),
        Paragraph('JUMLAH', header_cell),
        Paragraph('SATUAN', header_cell),
        Paragraph('TERSEDIA', header_cell),
        Paragraph('DIGUNAKAN', header_cell),
    ]
    
    table_data = [table_header]
    
    for idx, asset in enumerate(assets, 1):
        row = [
            Paragraph(str(idx), cell_center),
            Paragraph(asset.asset_code, cell_bold_style),
            Paragraph(asset.name, cell_bold_style),
            Paragraph(asset.brand or '-', cell_style),
            Paragraph(str(asset.total_units), cell_center_bold),
            Paragraph(asset.uom or 'Unit', cell_center),
            Paragraph(str(asset.unit_tersedia), cell_center),
            Paragraph(str(asset.unit_digunakan), cell_center),
        ]
        table_data.append(row)
    
    col_widths = [
        page_width * 0.05,   # NO
        page_width * 0.10,   # KODE
        page_width * 0.30,   # NAMA ASET
        page_width * 0.15,   # MEREK
        page_width * 0.10,   # JUMLAH
        page_width * 0.10,   # SATUAN
        page_width * 0.10,   # TERSEDIA
        page_width * 0.10,   # DIGUNAKAN
    ]
    
    asset_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # Style the table
    table_style_commands = [
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), navy),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Data rows
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        
        # Alignment
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # NO
        ('ALIGN', (4, 1), (-1, -1), 'CENTER'),  # JUMLAH onwards
        
        # Grid
        ('LINEBELOW', (0, 0), (-1, 0), 1, navy),
        ('LINEBELOW', (0, 1), (-1, -2), 0.5, HexColor('#E5E7EB')),
        ('LINEBELOW', (0, -1), (-1, -1), 1, border_color),
    ]
    
    # Alternating row colors
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            table_style_commands.append(('BACKGROUND', (0, i), (-1, i), alt_row))
    
    asset_table.setStyle(TableStyle(table_style_commands))
    elements.append(asset_table)
    
    elements.append(Spacer(1, 5*mm))
    
    # --- FOOTER NOTE ---
    footer_style = ParagraphStyle(
        'FooterNote',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=HexColor('#999999'),
        alignment=TA_LEFT,
        leading=11,
    )
    elements.append(Paragraph(
        f'Menampilkan {total_aset} aset — Dokumen ini digenerate secara otomatis oleh Sistem Manajemen Aset IT pada {tanggal_str}.',
        footer_style
    ))
    
    # Build PDF
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Laporan_Daftar_Aset_{active_tab}_{now.strftime("%Y%m%d")}.pdf"'
    return response


@login_required
def distribusi_export_pdf(request):
    """Generate a professional PDF report for asset distribution."""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm, cm
    from reportlab.lib.colors import HexColor, white
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus.flowables import HRFlowable
    from io import BytesIO
    import locale
    from django.db.models import Q
    import datetime
    import re
    
    tab = request.GET.get('tab', 'handover')
    if not tab:
        tab = 'handover'
    search_query = request.GET.get('q', '')
    sort_order = request.GET.get('sort', 'desc')
    
    # Same query logic as distribusi_list
    assignments = AssetAssignment.objects.filter(type=tab).select_related(
        'unit', 'unit__asset', 'employee', 'from_employee'
    )
    
    if sort_order == 'asc':
        assignments = assignments.order_by('assigned_date', 'id')
    else:
        assignments = assignments.order_by('-assigned_date', '-id')
    
    if search_query:
        date_q = Q(assigned_date__icontains=search_query)
        query_lower = search_query.lower()
        months = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'mei': 5, 'may': 5, 'jun': 6,
            'jul': 7, 'agu': 8, 'aug': 8, 'sep': 9, 'okt': 10, 'oct': 10, 'nov': 11, 'des': 12, 'dec': 12
        }
        
        try:
            dt = datetime.datetime.strptime(query_lower.title(), "%d %b %Y")
            date_q = Q(assigned_date=dt.date())
        except ValueError:
            month_val = None
            for k, v in months.items():
                if k in query_lower:
                    month_val = v
                    break
            
            year_match = re.search(r'(20\d{2})', query_lower)
            year_val = int(year_match.group(1)) if year_match else None
            
            day_match = re.search(r'(0?[1-9]|[12]\d|3[01])', query_lower)
            day_val = int(day_match.group(1)) if day_match else None

            if month_val and year_val:
                date_q = Q(assigned_date__month=month_val, assigned_date__year=year_val)
            elif month_val:
                date_q = Q(assigned_date__month=month_val)

        assignments = assignments.filter(
            Q(employee__nik__icontains=search_query) |
            Q(employee__name__icontains=search_query) |
            Q(unit__unit_code__icontains=search_query) |
            Q(unit__asset__name__icontains=search_query) |
            date_q
        )
        
    tab_titles = {
        'handover': 'Serah Terima',
        'mutation': 'Mutasi',
        'return': 'Pengembalian'
    }
    
    category_label = f"Distribusi Aset: {tab_titles.get(tab, 'Serah Terima')}"
    
    # Colors
    navy = HexColor('#002060')
    alt_row = HexColor('#F8F9FC')
    border_color = HexColor('#D0D5DD')
    
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.5*cm,
        rightMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=2*cm,
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=16, textColor=white, leading=20)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=HexColor('#B0C4DE'), leading=14)
    company_style = ParagraphStyle('CompanyName', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=white, alignment=TA_RIGHT, leading=14)
    company_sub_style = ParagraphStyle('CompanySub', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=HexColor('#B0C4DE'), alignment=TA_RIGHT, leading=11)
    
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12)
    cell_bold_style = ParagraphStyle('CellBoldStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12)
    cell_small = ParagraphStyle('CellSmall', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=HexColor('#666666'), leading=10)
    header_cell = ParagraphStyle('HeaderCell', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=white, alignment=TA_CENTER, leading=11)
    
    elements = []
    
    now = datetime.datetime.now()
    bulan_indo = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    tanggal_str = f"{now.day} {bulan_indo[now.month]} {now.year}"
    
    page_width = landscape(A4)[0] - 3*cm
    
    # LOGOS
    import os
    from reportlab.platypus import Image as RLImage
    from PIL import Image
    try:
        from django.conf import settings
        it_logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'it_all_role_logo.png')
        kerinci_logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'kerinci_logo.png')
        
        desired_height = 1.3 * cm
        
        it_img = Image.open(it_logo_path)
        it_rl_img = RLImage(it_logo_path, width=desired_height * (it_img.width / float(it_img.height)), height=desired_height)
        
        ker_img = Image.open(kerinci_logo_path)
        ker_rl_img = RLImage(kerinci_logo_path, width=desired_height * (ker_img.width / float(ker_img.height)), height=desired_height)
        
        logo_table = Table([[ker_rl_img, it_rl_img]], colWidths=[page_width/2, page_width/2])
        logo_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(logo_table)
    except Exception as e:
        pass
    
    header_data = [[
        [Paragraph('Laporan Distribusi Aset', title_style),
         Paragraph(f'{category_label} - {tanggal_str}', subtitle_style)],
        [Paragraph('SISTEM MANAJEMEN ASET IT', company_style),
         Paragraph('Dicetak otomatis dari sistem', company_sub_style)],
    ]]
    
    header_table = Table(header_data, colWidths=[page_width * 0.65, page_width * 0.35])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), navy),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 20),
        ('RIGHTPADDING', (-1, -1), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('ROUNDEDCORNERS', [6, 6, 0, 0]),
    ]))
    elements.append(header_table)
    
    elements.append(Spacer(1, 8*mm))
    
    # INFO
    info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=HexColor('#555555'))
    info_bold = ParagraphStyle('InfoBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=HexColor('#333333'))
    
    total_data = assignments.count()
    
    info_data = [
        [Paragraph('Kategori', info_style), Paragraph(f': {category_label}', info_bold),
         Paragraph('Total Data', info_style), Paragraph(f': {total_data} transaksi', info_bold)]
    ]
    
    row_2 = [Paragraph('Tanggal Cetak', info_style), Paragraph(f': {tanggal_str}, {now.strftime("%H:%M")} WIB', info_bold)]
    
    if search_query:
        row_2.extend([Paragraph('Filter Pencarian', info_style), Paragraph(f': {search_query}', info_bold)])
    else:
        row_2.extend(['', ''])
        
    info_data.append(row_2)
    
    info_table = Table(info_data, colWidths=[page_width*0.12, page_width*0.38, page_width*0.12, page_width*0.38])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6*mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceAfter=4*mm))
    
    # TABLE
    if tab == 'mutation':
        table_header = [
            Paragraph('NO', header_cell),
            Paragraph('TANGGAL', header_cell),
            Paragraph('UNIT ASET', header_cell),
            Paragraph('DARI (PENGIRIM)', header_cell),
            Paragraph('KE (PENERIMA)', header_cell),
            Paragraph('CATATAN', header_cell),
        ]
        col_widths = [page_width*0.05, page_width*0.12, page_width*0.28, page_width*0.20, page_width*0.20, page_width*0.15]
    elif tab == 'return':
        table_header = [
            Paragraph('NO', header_cell),
            Paragraph('TANGGAL', header_cell),
            Paragraph('UNIT ASET', header_cell),
            Paragraph('DIKEMBALIKAN OLEH', header_cell),
            Paragraph('CATATAN', header_cell),
        ]
        col_widths = [page_width*0.05, page_width*0.12, page_width*0.35, page_width*0.28, page_width*0.20]
    else:
        table_header = [
            Paragraph('NO', header_cell),
            Paragraph('TANGGAL', header_cell),
            Paragraph('UNIT ASET', header_cell),
            Paragraph('DISERAHKAN KEPADA', header_cell),
            Paragraph('CATATAN', header_cell),
        ]
        col_widths = [page_width*0.05, page_width*0.12, page_width*0.35, page_width*0.28, page_width*0.20]
        
    table_data = [table_header]
    
    for idx, asn in enumerate(assignments, 1):
        tgl_str = f"{asn.assigned_date.day} {bulan_indo[asn.assigned_date.month]} {asn.assigned_date.year}"
        
        tgl_info = [Paragraph(tgl_str, cell_style)]
        if asn.created_at:
            tgl_info.append(Paragraph(f"{asn.created_at.strftime('%H:%M')} WIB", cell_small))
        
        unit_info = [
            Paragraph(asn.unit.asset.name, cell_bold_style),
            Paragraph(asn.unit.unit_code, cell_small)
        ]
        
        penerima = [
            Paragraph(asn.employee.name, cell_bold_style),
            Paragraph(f"NIK: {asn.employee.nik}", cell_small)
        ]
        
        if tab == 'mutation':
            pengirim = [
                Paragraph(asn.from_employee.name if asn.from_employee else "-", cell_bold_style),
                Paragraph(f"NIK: {asn.from_employee.nik}" if asn.from_employee else "", cell_small)
            ]
            row = [
                Paragraph(str(idx), ParagraphStyle('C', parent=cell_style, alignment=TA_CENTER)),
                tgl_info,
                unit_info,
                pengirim,
                penerima,
                Paragraph(asn.notes or '-', cell_style),
            ]
        else:
            row = [
                Paragraph(str(idx), ParagraphStyle('C', parent=cell_style, alignment=TA_CENTER)),
                tgl_info,
                unit_info,
                penerima,
                Paragraph(asn.notes or '-', cell_style),
            ]
        table_data.append(row)
        
    asn_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), navy),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('LINEBELOW', (0, 0), (-1, 0), 1, navy),
        ('LINEBELOW', (0, 1), (-1, -2), 0.5, HexColor('#E5E7EB')),
        ('LINEBELOW', (0, -1), (-1, -1), 1, border_color),
    ]
    
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            table_style.append(('BACKGROUND', (0, i), (-1, i), alt_row))
            
    asn_table.setStyle(TableStyle(table_style))
    elements.append(asn_table)
    
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph(f'Menampilkan {total_data} data — Dokumen ini digenerate secara otomatis oleh Sistem Manajemen Aset IT pada {tanggal_str}.', ParagraphStyle('F', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=HexColor('#999999'))))
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Laporan_Distribusi_{tab}_{now.strftime("%Y%m%d")}.pdf"'
    return response



@login_required
def status_aset_export_pdf(request):
    """Generate a professional PDF report for status aset."""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm, cm
    from reportlab.lib.colors import HexColor, white
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus.flowables import HRFlowable
    from io import BytesIO
    import locale
    from django.db.models import Q
    import datetime
    
    tab = request.GET.get('tab', 'tersedia')
    if not tab: tab = 'tersedia'
    cat_filter = request.GET.get('cat', 'karyawan')
    if not cat_filter: cat_filter = 'karyawan'
    search_query = request.GET.get('q', '')
    
    units = AssetUnit.objects.select_related('asset', 'assigned_to', 'asset__category').order_by('-id')
    
    if cat_filter == 'network':
        units = units.filter(asset__category__name__icontains='Network')
        cat_label = 'Network & Infrastruktur'
    else:
        units = units.filter(asset__category__name__icontains='Karyawan')
        cat_label = 'Karyawan'
        
    if tab == 'tersedia':
        units = units.filter(status='tersedia')
        tab_label = 'Tersedia'
    elif tab == 'digunakan':
        units = units.filter(status='digunakan')
        tab_label = 'Digunakan'
    elif tab == 'rusak':
        units = units.filter(status='rusak')
        tab_label = 'Maintenance'
    else:
        units = units.filter(status='tersedia')
        tab_label = 'Tersedia'
        
    if search_query:
        units = units.filter(
            Q(unit_code__icontains=search_query) |
            Q(asset__name__icontains=search_query) |
            Q(assigned_to__name__icontains=search_query) |
            Q(assigned_to__nik__icontains=search_query) |
            Q(area__icontains=search_query) |
            Q(location__icontains=search_query)
        )
        
    category_label = f"Status Aset {cat_label}: {tab_label}"
    
    navy = HexColor('#002060')
    alt_row = HexColor('#F8F9FC')
    border_color = HexColor('#D0D5DD')
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=16, textColor=white, leading=20)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=HexColor('#B0C4DE'), leading=14)
    company_style = ParagraphStyle('CompanyName', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=white, alignment=TA_RIGHT, leading=14)
    company_sub_style = ParagraphStyle('CompanySub', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=HexColor('#B0C4DE'), alignment=TA_RIGHT, leading=11)
    
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12)
    cell_bold_style = ParagraphStyle('CellBoldStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12)
    cell_small = ParagraphStyle('CellSmall', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=HexColor('#666666'), leading=10)
    header_cell = ParagraphStyle('HeaderCell', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=white, alignment=TA_CENTER, leading=11)
    cell_center = ParagraphStyle('CellCenter', parent=styles['Normal'], fontName='Helvetica', fontSize=9, alignment=TA_CENTER)
    
    elements = []
    now = datetime.datetime.now()
    bulan_indo = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    tanggal_str = f"{now.day} {bulan_indo[now.month]} {now.year}"
    
    page_width = landscape(A4)[0] - 3*cm
    
    import os
    from reportlab.platypus import Image as RLImage
    from PIL import Image
    try:
        from django.conf import settings
        it_logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'it_all_role_logo.png')
        kerinci_logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'kerinci_logo.png')
        desired_height = 1.3 * cm
        it_img = Image.open(it_logo_path)
        it_rl_img = RLImage(it_logo_path, width=desired_height * (it_img.width / float(it_img.height)), height=desired_height)
        ker_img = Image.open(kerinci_logo_path)
        ker_rl_img = RLImage(kerinci_logo_path, width=desired_height * (ker_img.width / float(ker_img.height)), height=desired_height)
        logo_table = Table([[ker_rl_img, it_rl_img]], colWidths=[page_width/2, page_width/2])
        logo_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'), ('ALIGN', (1, 0), (1, 0), 'RIGHT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('BOTTOMPADDING', (0, 0), (-1, -1), 10), ('TOPPADDING', (0, 0), (-1, -1), 0)]))
        elements.append(logo_table)
    except Exception as e: pass
    
    header_data = [[
        [Paragraph('Laporan Status Aset', title_style), Paragraph(f'{category_label} - {tanggal_str}', subtitle_style)],
        [Paragraph('SISTEM MANAJEMEN ASET IT', company_style), Paragraph('Dicetak otomatis dari sistem', company_sub_style)]
    ]]
    
    header_table = Table(header_data, colWidths=[page_width * 0.65, page_width * 0.35])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), navy),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 20),
        ('RIGHTPADDING', (-1, -1), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('ROUNDEDCORNERS', [6, 6, 0, 0]),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8*mm))
    
    info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=HexColor('#555555'))
    info_bold = ParagraphStyle('InfoBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=HexColor('#333333'))
    
    total_data = units.count()
    info_data = [
        [Paragraph('Kategori', info_style), Paragraph(f': {category_label}', info_bold), Paragraph('Total Data', info_style), Paragraph(f': {total_data} unit', info_bold)]
    ]
    row_2 = [Paragraph('Tanggal Cetak', info_style), Paragraph(f': {tanggal_str}, {now.strftime("%H:%M")} WIB', info_bold)]
    if search_query: row_2.extend([Paragraph('Filter Pencarian', info_style), Paragraph(f': {search_query}', info_bold)])
    else: row_2.extend(['', ''])
    info_data.append(row_2)
    
    info_table = Table(info_data, colWidths=[page_width*0.12, page_width*0.38, page_width*0.12, page_width*0.38])
    info_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2), ('LEFTPADDING', (0, 0), (-1, -1), 0)]))
    elements.append(info_table)
    elements.append(Spacer(1, 6*mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceAfter=4*mm))
    
    if tab != 'tersedia':
        if cat_filter == 'network':
            table_header = [Paragraph('NO', header_cell), Paragraph('KODE UNIT', header_cell), Paragraph('NAMA ASET', header_cell), Paragraph('STATUS', header_cell), Paragraph('LOKASI (AREA)', header_cell)]
        else:
            table_header = [Paragraph('NO', header_cell), Paragraph('KODE UNIT', header_cell), Paragraph('NAMA ASET', header_cell), Paragraph('STATUS', header_cell), Paragraph('DIPEGANG OLEH', header_cell)]
        col_widths = [page_width*0.05, page_width*0.15, page_width*0.35, page_width*0.15, page_width*0.30]
    else:
        table_header = [Paragraph('NO', header_cell), Paragraph('KODE UNIT', header_cell), Paragraph('NAMA ASET', header_cell), Paragraph('STATUS', header_cell)]
        col_widths = [page_width*0.05, page_width*0.20, page_width*0.50, page_width*0.25]
        
    table_data = [table_header]
    
    for idx, unit in enumerate(units, 1):
        asset_info = [Paragraph(unit.asset.name, cell_bold_style), Paragraph(unit.asset.category.name, cell_small)]
        status_text = unit.get_status_display()
        
        row = [Paragraph(str(idx), cell_center), Paragraph(unit.unit_code, cell_bold_style), asset_info, Paragraph(status_text, cell_center)]
        
        if tab != 'tersedia':
            if cat_filter == 'network':
                area = unit.area or '-'
                loc = unit.location or '-'
                holder_info = [Paragraph(f"Area: {area}", cell_bold_style), Paragraph(f"Lokasi: {loc}", cell_small)]
            else:
                if unit.assigned_to:
                    holder_info = [Paragraph(unit.assigned_to.name, cell_bold_style), Paragraph(f"NIK: {unit.assigned_to.nik}", cell_small)]
                else:
                    holder_info = Paragraph('-', cell_center)
            row.append(holder_info)
            
        table_data.append(row)
        
    unit_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), navy),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('LINEBELOW', (0, 0), (-1, 0), 1, navy),
        ('LINEBELOW', (0, 1), (-1, -2), 0.5, HexColor('#E5E7EB')),
        ('LINEBELOW', (0, -1), (-1, -1), 1, border_color),
    ]
    
    for i in range(1, len(table_data)):
        if i % 2 == 0: table_style.append(('BACKGROUND', (0, i), (-1, i), alt_row))
            
    unit_table.setStyle(TableStyle(table_style))
    elements.append(unit_table)
    
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph(f'Menampilkan {total_data} unit — Dokumen ini digenerate secara otomatis oleh Sistem Manajemen Aset IT pada {tanggal_str}.', ParagraphStyle('F', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=HexColor('#999999'))))
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Laporan_Status_Aset_{tab}_{now.strftime("%Y%m%d")}.pdf"'
    return response



@login_required
def employee_export_pdf(request):
    """Generate a professional PDF report for employee data."""
    from reportlab.lib.pagesizes import A4, portrait
    from reportlab.lib.units import mm, cm
    from reportlab.lib.colors import HexColor, white
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus.flowables import HRFlowable
    from io import BytesIO
    from django.db.models import Count, Q
    import datetime
    
    search_query = request.GET.get('q', '')
    
    employees = Employee.objects.annotate(
        active_assets=Count('held_units')
    ).order_by('name')
    
    if search_query:
        employees = employees.filter(
            Q(name__icontains=search_query) |
            Q(nik__icontains=search_query)
        )
        
    navy = HexColor('#002060')
    alt_row = HexColor('#F8F9FC')
    border_color = HexColor('#D0D5DD')
    
    buffer = BytesIO()
    # Using portrait for Employee list because it has fewer columns
    doc = SimpleDocTemplate(buffer, pagesize=portrait(A4), leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=16, textColor=white, leading=20)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=HexColor('#B0C4DE'), leading=14)
    company_style = ParagraphStyle('CompanyName', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=white, alignment=TA_RIGHT, leading=14)
    company_sub_style = ParagraphStyle('CompanySub', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=HexColor('#B0C4DE'), alignment=TA_RIGHT, leading=11)
    
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12)
    cell_bold_style = ParagraphStyle('CellBoldStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12)
    header_cell = ParagraphStyle('HeaderCell', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=white, alignment=TA_CENTER, leading=11)
    cell_center = ParagraphStyle('CellCenter', parent=styles['Normal'], fontName='Helvetica', fontSize=9, alignment=TA_CENTER)
    
    elements = []
    now = datetime.datetime.now()
    bulan_indo = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    tanggal_str = f"{now.day} {bulan_indo[now.month]} {now.year}"
    
    page_width = portrait(A4)[0] - 3*cm
    
    import os
    from reportlab.platypus import Image as RLImage
    from PIL import Image
    try:
        from django.conf import settings
        it_logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'it_all_role_logo.png')
        kerinci_logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'kerinci_logo.png')
        desired_height = 1.3 * cm
        it_img = Image.open(it_logo_path)
        it_rl_img = RLImage(it_logo_path, width=desired_height * (it_img.width / float(it_img.height)), height=desired_height)
        ker_img = Image.open(kerinci_logo_path)
        ker_rl_img = RLImage(kerinci_logo_path, width=desired_height * (ker_img.width / float(ker_img.height)), height=desired_height)
        logo_table = Table([[ker_rl_img, it_rl_img]], colWidths=[page_width/2, page_width/2])
        logo_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'), ('ALIGN', (1, 0), (1, 0), 'RIGHT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('BOTTOMPADDING', (0, 0), (-1, -1), 10), ('TOPPADDING', (0, 0), (-1, -1), 0)]))
        elements.append(logo_table)
    except Exception as e: pass
    
    header_data = [[
        [Paragraph('Laporan Data Karyawan', title_style), Paragraph(f'Daftar Karyawan - {tanggal_str}', subtitle_style)],
        [Paragraph('SISTEM MANAJEMEN ASET IT', company_style), Paragraph('Dicetak otomatis dari sistem', company_sub_style)]
    ]]
    
    header_table = Table(header_data, colWidths=[page_width * 0.60, page_width * 0.40])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), navy),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 20),
        ('RIGHTPADDING', (-1, -1), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('ROUNDEDCORNERS', [6, 6, 0, 0]),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8*mm))
    
    info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=HexColor('#555555'))
    info_bold = ParagraphStyle('InfoBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=HexColor('#333333'))
    
    total_data = employees.count()
    info_data = [
        [Paragraph('Kategori', info_style), Paragraph(': Data Karyawan', info_bold), Paragraph('Total Data', info_style), Paragraph(f': {total_data} orang', info_bold)]
    ]
    row_2 = [Paragraph('Tanggal Cetak', info_style), Paragraph(f': {tanggal_str}, {now.strftime("%H:%M")} WIB', info_bold)]
    if search_query: row_2.extend([Paragraph('Filter Pencarian', info_style), Paragraph(f': {search_query}', info_bold)])
    else: row_2.extend(['', ''])
    info_data.append(row_2)
    
    info_table = Table(info_data, colWidths=[page_width*0.16, page_width*0.34, page_width*0.16, page_width*0.34])
    info_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2), ('LEFTPADDING', (0, 0), (-1, -1), 0)]))
    elements.append(info_table)
    elements.append(Spacer(1, 6*mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceAfter=4*mm))
    
    table_header = [Paragraph('NO', header_cell), Paragraph('NOMOR INDUK (NIK)', header_cell), Paragraph('NAMA LENGKAP', header_cell), Paragraph('ASET YANG DIGUNAKAN', header_cell)]
    col_widths = [page_width*0.08, page_width*0.25, page_width*0.42, page_width*0.25]
        
    table_data = [table_header]
    
    for idx, emp in enumerate(employees, 1):
        if emp.active_assets > 0:
            asset_text = f"{emp.active_assets} Perangkat"
        else:
            asset_text = "Tidak ada aset"
            
        row = [
            Paragraph(str(idx), cell_center), 
            Paragraph(emp.nik, cell_bold_style), 
            Paragraph(emp.name, cell_bold_style), 
            Paragraph(asset_text, cell_center)
        ]
        table_data.append(row)
        
    emp_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), navy),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'), # NO col
        ('ALIGN', (3, 1), (3, -1), 'CENTER'), # ASET col
        ('LINEBELOW', (0, 0), (-1, 0), 1, navy),
        ('LINEBELOW', (0, 1), (-1, -2), 0.5, HexColor('#E5E7EB')),
        ('LINEBELOW', (0, -1), (-1, -1), 1, border_color),
    ]
    
    for i in range(1, len(table_data)):
        if i % 2 == 0: table_style.append(('BACKGROUND', (0, i), (-1, i), alt_row))
            
    emp_table.setStyle(TableStyle(table_style))
    elements.append(emp_table)
    
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph(f'Menampilkan {total_data} karyawan — Dokumen ini digenerate secara otomatis oleh Sistem Manajemen Aset IT pada {tanggal_str}.', ParagraphStyle('F', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=HexColor('#999999'))))
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Laporan_Data_Karyawan_{now.strftime("%Y%m%d")}.pdf"'
    return response



@login_required
def employee_detail_export_pdf(request, emp_id):
    """Generate a professional PDF report for specific employee assets."""
    from reportlab.lib.pagesizes import A4, portrait
    from reportlab.lib.units import mm, cm
    from reportlab.lib.colors import HexColor, white
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus.flowables import HRFlowable
    from io import BytesIO
    import datetime
    
    employee = get_object_or_404(Employee, id=emp_id)
    units = employee.held_units.select_related('asset', 'asset__category').all()
    
    navy = HexColor('#002060')
    alt_row = HexColor('#F8F9FC')
    border_color = HexColor('#D0D5DD')
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=portrait(A4), leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=16, textColor=white, leading=20)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=HexColor('#B0C4DE'), leading=14)
    company_style = ParagraphStyle('CompanyName', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=white, alignment=TA_RIGHT, leading=14)
    company_sub_style = ParagraphStyle('CompanySub', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=HexColor('#B0C4DE'), alignment=TA_RIGHT, leading=11)
    
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12)
    cell_bold_style = ParagraphStyle('CellBoldStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12)
    cell_small = ParagraphStyle('CellSmall', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=HexColor('#666666'), leading=10)
    header_cell = ParagraphStyle('HeaderCell', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=white, alignment=TA_CENTER, leading=11)
    cell_center = ParagraphStyle('CellCenter', parent=styles['Normal'], fontName='Helvetica', fontSize=9, alignment=TA_CENTER)
    
    elements = []
    now = datetime.datetime.now()
    bulan_indo = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    tanggal_str = f"{now.day} {bulan_indo[now.month]} {now.year}"
    
    page_width = portrait(A4)[0] - 3*cm
    
    import os
    from reportlab.platypus import Image as RLImage
    from PIL import Image
    try:
        from django.conf import settings
        it_logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'it_all_role_logo.png')
        kerinci_logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'kerinci_logo.png')
        desired_height = 1.3 * cm
        it_img = Image.open(it_logo_path)
        it_rl_img = RLImage(it_logo_path, width=desired_height * (it_img.width / float(it_img.height)), height=desired_height)
        ker_img = Image.open(kerinci_logo_path)
        ker_rl_img = RLImage(kerinci_logo_path, width=desired_height * (ker_img.width / float(ker_img.height)), height=desired_height)
        logo_table = Table([[ker_rl_img, it_rl_img]], colWidths=[page_width/2, page_width/2])
        logo_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'), ('ALIGN', (1, 0), (1, 0), 'RIGHT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('BOTTOMPADDING', (0, 0), (-1, -1), 10), ('TOPPADDING', (0, 0), (-1, -1), 0)]))
        elements.append(logo_table)
    except Exception as e: pass
    
    header_data = [[
        [Paragraph('Rincian Aset Karyawan', title_style), Paragraph(f'{employee.name} (NIK: {employee.nik})', subtitle_style)],
        [Paragraph('SISTEM MANAJEMEN ASET IT', company_style), Paragraph('Dicetak otomatis dari sistem', company_sub_style)]
    ]]
    
    header_table = Table(header_data, colWidths=[page_width * 0.60, page_width * 0.40])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), navy),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 20),
        ('RIGHTPADDING', (-1, -1), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('ROUNDEDCORNERS', [6, 6, 0, 0]),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8*mm))
    
    info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=HexColor('#555555'))
    info_bold = ParagraphStyle('InfoBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=HexColor('#333333'))
    
    total_data = units.count()
    info_data = [
        [Paragraph('Nama Lengkap', info_style), Paragraph(f': {employee.name}', info_bold), Paragraph('Total Aset', info_style), Paragraph(f': {total_data} perangkat', info_bold)],
        [Paragraph('Nomor Induk (NIK)', info_style), Paragraph(f': {employee.nik}', info_bold), Paragraph('Tanggal Cetak', info_style), Paragraph(f': {tanggal_str}', info_bold)],
        [Paragraph('Jabatan', info_style), Paragraph(f': {employee.position or "-"}', info_bold), '', '']
    ]
    
    info_table = Table(info_data, colWidths=[page_width*0.20, page_width*0.30, page_width*0.20, page_width*0.30])
    info_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2), ('LEFTPADDING', (0, 0), (-1, -1), 0)]))
    elements.append(info_table)
    elements.append(Spacer(1, 6*mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceAfter=4*mm))
    
    table_header = [Paragraph('NO', header_cell), Paragraph('KODE UNIT', header_cell), Paragraph('NAMA ASET', header_cell), Paragraph('STATUS', header_cell)]
    col_widths = [page_width*0.08, page_width*0.25, page_width*0.42, page_width*0.25]
        
    table_data = [table_header]
    
    if total_data == 0:
        table_data.append([Paragraph('Karyawan ini tidak memegang aset apapun saat ini.', cell_center), '', '', ''])
        emp_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), navy),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('SPAN', (0, 1), (-1, 1)),
            ('TOPPADDING', (0, 1), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 15),
            ('LINEBELOW', (0, 0), (-1, 0), 1, navy),
            ('LINEBELOW', (0, -1), (-1, -1), 1, border_color),
        ]
        emp_table.setStyle(TableStyle(table_style))
    else:
        for idx, unit in enumerate(units, 1):
            asset_info = [Paragraph(unit.asset.name, cell_bold_style), Paragraph(unit.asset.category.name, cell_small)]
            status_text = unit.get_status_display()
            
            row = [
                Paragraph(str(idx), cell_center), 
                Paragraph(unit.unit_code, cell_bold_style), 
                asset_info, 
                Paragraph(status_text, cell_center)
            ]
            table_data.append(row)
            
        emp_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), navy),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'), # NO col
            ('ALIGN', (3, 1), (3, -1), 'CENTER'), # STATUS col
            ('LINEBELOW', (0, 0), (-1, 0), 1, navy),
            ('LINEBELOW', (0, 1), (-1, -2), 0.5, HexColor('#E5E7EB')),
            ('LINEBELOW', (0, -1), (-1, -1), 1, border_color),
        ]
        
        for i in range(1, len(table_data)):
            if i % 2 == 0: table_style.append(('BACKGROUND', (0, i), (-1, i), alt_row))
                
        emp_table.setStyle(TableStyle(table_style))
        
    elements.append(emp_table)
    
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph(f'Menampilkan {total_data} perangkat — Dokumen ini digenerate secara otomatis oleh Sistem Manajemen Aset IT pada {tanggal_str}.', ParagraphStyle('F', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=HexColor('#999999'))))
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Laporan_Aset_{employee.name.replace(" ", "_")}_{now.strftime("%Y%m%d")}.pdf"'
    return response



@login_required
def unit_history_export_pdf(request, unit_id):
    """Generate a professional PDF report for unit history logs."""
    from reportlab.lib.pagesizes import A4, portrait
    from reportlab.lib.units import mm, cm
    from reportlab.lib.colors import HexColor, white
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus.flowables import HRFlowable
    from io import BytesIO
    import datetime
    
    unit = get_object_or_404(AssetUnit, id=unit_id)
    logs_qs = unit.logs.all().select_related('employee')
    import re
    pattern = re.compile(r"^(.+?) \((.+?)\) - (.*)$")
    logs = []
    for log in logs_qs:
        log.deleted_employee_name = None
        if not log.employee and log.notes:
            match = pattern.match(log.notes.strip())
            if match:
                name, nik, rest_of_notes = match.groups()
                log.deleted_employee_name = name
                log.notes = rest_of_notes.strip()
        logs.append(log)
    
    navy = HexColor('#002060')
    alt_row = HexColor('#F8F9FC')
    border_color = HexColor('#D0D5DD')
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=portrait(A4), leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=16, textColor=white, leading=20)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=HexColor('#B0C4DE'), leading=14)
    company_style = ParagraphStyle('CompanyName', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=white, alignment=TA_RIGHT, leading=14)
    company_sub_style = ParagraphStyle('CompanySub', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=HexColor('#B0C4DE'), alignment=TA_RIGHT, leading=11)
    
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12)
    cell_bold_style = ParagraphStyle('CellBoldStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12)
    cell_small = ParagraphStyle('CellSmall', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=HexColor('#666666'), leading=10)
    header_cell = ParagraphStyle('HeaderCell', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=white, alignment=TA_CENTER, leading=11)
    cell_center = ParagraphStyle('CellCenter', parent=styles['Normal'], fontName='Helvetica', fontSize=9, alignment=TA_CENTER)
    
    elements = []
    now = datetime.datetime.now()
    bulan_indo = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    tanggal_str = f"{now.day} {bulan_indo[now.month]} {now.year}"
    
    page_width = portrait(A4)[0] - 3*cm
    
    import os
    from reportlab.platypus import Image as RLImage
    from PIL import Image
    try:
        from django.conf import settings
        it_logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'it_all_role_logo.png')
        kerinci_logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'kerinci_logo.png')
        desired_height = 1.3 * cm
        it_img = Image.open(it_logo_path)
        it_rl_img = RLImage(it_logo_path, width=desired_height * (it_img.width / float(it_img.height)), height=desired_height)
        ker_img = Image.open(kerinci_logo_path)
        ker_rl_img = RLImage(kerinci_logo_path, width=desired_height * (ker_img.width / float(ker_img.height)), height=desired_height)
        logo_table = Table([[ker_rl_img, it_rl_img]], colWidths=[page_width/2, page_width/2])
        logo_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'), ('ALIGN', (1, 0), (1, 0), 'RIGHT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('BOTTOMPADDING', (0, 0), (-1, -1), 10), ('TOPPADDING', (0, 0), (-1, -1), 0)]))
        elements.append(logo_table)
    except Exception as e: pass
    
    header_data = [[
        [Paragraph('Laporan Riwayat Unit', title_style), Paragraph(f'{unit.unit_code} - {unit.asset.name}', subtitle_style)],
        [Paragraph('SISTEM MANAJEMEN ASET IT', company_style), Paragraph('Dicetak otomatis dari sistem', company_sub_style)]
    ]]
    
    header_table = Table(header_data, colWidths=[page_width * 0.60, page_width * 0.40])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), navy),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 20),
        ('RIGHTPADDING', (-1, -1), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('ROUNDEDCORNERS', [6, 6, 0, 0]),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8*mm))
    
    info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=HexColor('#555555'))
    info_bold = ParagraphStyle('InfoBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=HexColor('#333333'))
    
    total_data = len(logs)
    info_data = [
        [Paragraph('Nama Aset', info_style), Paragraph(f': {unit.asset.name}', info_bold), Paragraph('Total Kejadian', info_style), Paragraph(f': {total_data} riwayat', info_bold)],
        [Paragraph('Kode Unit', info_style), Paragraph(f': {unit.unit_code}', info_bold), Paragraph('Tanggal Cetak', info_style), Paragraph(f': {tanggal_str}', info_bold)]
    ]
    
    info_table = Table(info_data, colWidths=[page_width*0.15, page_width*0.35, page_width*0.18, page_width*0.32])
    info_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2), ('LEFTPADDING', (0, 0), (-1, -1), 0)]))
    elements.append(info_table)
    elements.append(Spacer(1, 6*mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceAfter=4*mm))
    
    table_header = [Paragraph('NO', header_cell), Paragraph('WAKTU', header_cell), Paragraph('KEJADIAN', header_cell), Paragraph('KETERANGAN', header_cell)]
    col_widths = [page_width*0.06, page_width*0.22, page_width*0.25, page_width*0.47]
        
    table_data = [table_header]
    
    if total_data == 0:
        table_data.append([Paragraph('Belum ada riwayat pada unit ini.', cell_center), '', '', ''])
        log_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), navy),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('SPAN', (0, 1), (-1, 1)),
            ('TOPPADDING', (0, 1), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 15),
            ('LINEBELOW', (0, 0), (-1, 0), 1, navy),
            ('LINEBELOW', (0, -1), (-1, -1), 1, border_color),
        ]
        log_table.setStyle(TableStyle(table_style))
    else:
        for idx, log in enumerate(logs, 1):
            date_str = f"{log.timestamp.day:02d} {bulan_indo[log.timestamp.month][:3]} {log.timestamp.year}"
            time_str = f"{log.timestamp.strftime('%H:%M')}"
            
            time_col = [Paragraph(date_str, cell_bold_style), Paragraph(time_str, cell_small)]
            
            notes = log.notes or '-'
            if log.employee:
                notes = f"{log.employee.name} - {notes}"
            elif log.deleted_employee_name:
                notes = f"{log.deleted_employee_name} [Dihapus] - {notes}"
                
            row = [
                Paragraph(str(idx), cell_center), 
                time_col, 
                Paragraph(log.get_action_display(), cell_bold_style), 
                Paragraph(notes, cell_style)
            ]
            table_data.append(row)
            
        log_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), navy),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'), # NO col
            ('LINEBELOW', (0, 0), (-1, 0), 1, navy),
            ('LINEBELOW', (0, 1), (-1, -2), 0.5, HexColor('#E5E7EB')),
            ('LINEBELOW', (0, -1), (-1, -1), 1, border_color),
        ]
        
        for i in range(1, len(table_data)):
            if i % 2 == 0: table_style.append(('BACKGROUND', (0, i), (-1, i), alt_row))
                
        log_table.setStyle(TableStyle(table_style))
        
    elements.append(log_table)
    
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph(f'Menampilkan {total_data} riwayat kejadian — Dokumen ini digenerate secara otomatis oleh Sistem Manajemen Aset IT pada {tanggal_str}.', ParagraphStyle('F', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=HexColor('#999999'))))
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Laporan_Riwayat_{unit.unit_code}_{now.strftime("%Y%m%d")}.pdf"'
    return response



@login_required
def asset_units_export_pdf(request, asset_id):
    """Generate a professional PDF report for specific asset units."""
    from reportlab.lib.pagesizes import A4, portrait
    from reportlab.lib.units import mm, cm
    from reportlab.lib.colors import HexColor, white
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus.flowables import HRFlowable
    from io import BytesIO
    import datetime
    
    asset = get_object_or_404(Asset, id=asset_id)
    units = asset.units.all().select_related('assigned_to').order_by('unit_code')
    
    navy = HexColor('#002060')
    alt_row = HexColor('#F8F9FC')
    border_color = HexColor('#D0D5DD')
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=portrait(A4), leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=16, textColor=white, leading=20)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=HexColor('#B0C4DE'), leading=14)
    company_style = ParagraphStyle('CompanyName', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=white, alignment=TA_RIGHT, leading=14)
    company_sub_style = ParagraphStyle('CompanySub', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=HexColor('#B0C4DE'), alignment=TA_RIGHT, leading=11)
    
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12)
    cell_bold_style = ParagraphStyle('CellBoldStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12)
    cell_small = ParagraphStyle('CellSmall', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=HexColor('#666666'), leading=10)
    header_cell = ParagraphStyle('HeaderCell', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=white, alignment=TA_CENTER, leading=11)
    cell_center = ParagraphStyle('CellCenter', parent=styles['Normal'], fontName='Helvetica', fontSize=9, alignment=TA_CENTER)
    
    elements = []
    now = datetime.datetime.now()
    bulan_indo = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    tanggal_str = f"{now.day} {bulan_indo[now.month]} {now.year}"
    
    page_width = portrait(A4)[0] - 3*cm
    
    import os
    from reportlab.platypus import Image as RLImage
    from PIL import Image
    try:
        from django.conf import settings
        it_logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'it_all_role_logo.png')
        kerinci_logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'kerinci_logo.png')
        desired_height = 1.3 * cm
        it_img = Image.open(it_logo_path)
        it_rl_img = RLImage(it_logo_path, width=desired_height * (it_img.width / float(it_img.height)), height=desired_height)
        ker_img = Image.open(kerinci_logo_path)
        ker_rl_img = RLImage(kerinci_logo_path, width=desired_height * (ker_img.width / float(ker_img.height)), height=desired_height)
        logo_table = Table([[ker_rl_img, it_rl_img]], colWidths=[page_width/2, page_width/2])
        logo_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'), ('ALIGN', (1, 0), (1, 0), 'RIGHT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('BOTTOMPADDING', (0, 0), (-1, -1), 10), ('TOPPADDING', (0, 0), (-1, -1), 0)]))
        elements.append(logo_table)
    except Exception as e: pass
    
    header_data = [[
        [Paragraph('Laporan Unit Aset', title_style), Paragraph(f'{asset.name}', subtitle_style)],
        [Paragraph('SISTEM MANAJEMEN ASET IT', company_style), Paragraph('Dicetak otomatis dari sistem', company_sub_style)]
    ]]
    
    header_table = Table(header_data, colWidths=[page_width * 0.60, page_width * 0.40])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), navy),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 20),
        ('RIGHTPADDING', (-1, -1), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('ROUNDEDCORNERS', [6, 6, 0, 0]),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8*mm))
    
    info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=HexColor('#555555'))
    info_bold = ParagraphStyle('InfoBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=HexColor('#333333'))
    
    total_data = units.count()
    tersedia = units.filter(status='tersedia').count()
    digunakan = units.filter(status='digunakan').count()
    
    info_data = [
        [Paragraph('Kategori', info_style), Paragraph(f': {asset.category.name}', info_bold), Paragraph('Tersedia', info_style), Paragraph(f': {tersedia} unit', info_bold)],
        [Paragraph('Kode Aset', info_style), Paragraph(f': {asset.asset_code}', info_bold), Paragraph('Digunakan', info_style), Paragraph(f': {digunakan} unit', info_bold)],
        [Paragraph('Tanggal Cetak', info_style), Paragraph(f': {tanggal_str}', info_bold), Paragraph('Total Unit', info_style), Paragraph(f': {total_data} unit', info_bold)]
    ]
    
    info_table = Table(info_data, colWidths=[page_width*0.15, page_width*0.35, page_width*0.15, page_width*0.35])
    info_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2), ('LEFTPADDING', (0, 0), (-1, -1), 0)]))
    elements.append(info_table)
    elements.append(Spacer(1, 6*mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceAfter=4*mm))
    
    is_network = 'Network' in asset.category.name
    
    if is_network:
        table_header = [Paragraph('NO', header_cell), Paragraph('KODE UNIT', header_cell), Paragraph('STATUS', header_cell), Paragraph('LOKASI (AREA)', header_cell)]
    else:
        table_header = [Paragraph('NO', header_cell), Paragraph('KODE UNIT', header_cell), Paragraph('STATUS', header_cell), Paragraph('DIPEGANG OLEH', header_cell)]
        
    col_widths = [page_width*0.08, page_width*0.25, page_width*0.25, page_width*0.42]
        
    table_data = [table_header]
    
    if total_data == 0:
        table_data.append([Paragraph('Belum ada unit untuk aset ini.', cell_center), '', '', ''])
        unit_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), navy),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('SPAN', (0, 1), (-1, 1)),
            ('TOPPADDING', (0, 1), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 15),
            ('LINEBELOW', (0, 0), (-1, 0), 1, navy),
            ('LINEBELOW', (0, -1), (-1, -1), 1, border_color),
        ]
        unit_table.setStyle(TableStyle(table_style))
    else:
        for idx, unit in enumerate(units, 1):
            if is_network:
                area = unit.area or '-'
                loc = unit.location or '-'
                holder_info = [Paragraph(f"Area: {area}", cell_bold_style), Paragraph(f"Lokasi: {loc}", cell_small)]
            else:
                if unit.assigned_to:
                    holder_info = [Paragraph(unit.assigned_to.name, cell_bold_style), Paragraph(f"NIK: {unit.assigned_to.nik}", cell_small)]
                else:
                    holder_info = Paragraph('-', cell_center)
                
            row = [
                Paragraph(str(idx), cell_center), 
                Paragraph(unit.unit_code, cell_bold_style), 
                Paragraph(unit.get_status_display(), cell_center), 
                holder_info
            ]
            table_data.append(row)
            
        unit_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), navy),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'), # NO col
            ('ALIGN', (2, 1), (2, -1), 'CENTER'), # STATUS col
            ('LINEBELOW', (0, 0), (-1, 0), 1, navy),
            ('LINEBELOW', (0, 1), (-1, -2), 0.5, HexColor('#E5E7EB')),
            ('LINEBELOW', (0, -1), (-1, -1), 1, border_color),
        ]
        
        for i in range(1, len(table_data)):
            if i % 2 == 0: table_style.append(('BACKGROUND', (0, i), (-1, i), alt_row))
                
        unit_table.setStyle(TableStyle(table_style))
        
    elements.append(unit_table)
    
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph(f'Menampilkan {total_data} unit — Dokumen ini digenerate secara otomatis oleh Sistem Manajemen Aset IT pada {tanggal_str}.', ParagraphStyle('F', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=HexColor('#999999'))))
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Laporan_Unit_Aset_{asset.asset_code}_{now.strftime("%Y%m%d")}.pdf"'
    return response


