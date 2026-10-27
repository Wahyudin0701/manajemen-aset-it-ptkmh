import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Count, Sum, Q, F
from django.core.paginator import Paginator
from django.utils import timezone

from assets.models import ConsumableItem, ConsumableTransaction, Employee, AssetUnit
from assets.permissions import operator_required

# Lokasi standar operasional PT. KMH
KMH_LOCATIONS = [
    'Gudang Induk (GI)',
    'Ruang Server / IT',
    'Regulating Weir (RW)',
    'Jakon',
    'Beringin Tunggal (BT)',
    'DAM',
    'Adit 1',
    'Adit 2',
    'Adit 3',
    'Vertical Shaft (VS)',
    'Power House (PH)',
    'Workshop IT',
    'Lain-lainnya',
]


def _generate_item_code(category):
    """Menghasilkan kode item otomatis berdasarkan kategori barang."""
    prefix_map = {
        'cable': 'CNS-CAB',
        'connector': 'CNS-CON',
        'maintenance': 'CNS-MNT',
        'fastener': 'CNS-FST',
        'electrical': 'CNS-ELC',
        'cleaning': 'CNS-CLN',
        'tools_acc': 'CNS-ACC',
    }
    prefix = prefix_map.get(category, 'CNS-IT')
    last_item = ConsumableItem.objects.filter(item_code__startswith=f"{prefix}-").order_by('-id').first()
    counter = 1
    if last_item:
        match = re.search(r'-(\d+)$', last_item.item_code)
        if match:
            counter = int(match.group(1)) + 1
    return f"{prefix}-{counter:03d}"


def _generate_trx_code(trx_type):
    """Menghasilkan kode transaksi buku besar unik (misal: TRX-IN-20261026-001)."""
    date_str = timezone.now().strftime("%Y%m%d")
    prefix = f"TRX-{trx_type.upper()}-{date_str}"
    last_trx = ConsumableTransaction.objects.filter(transaction_code__startswith=prefix).order_by('-id').first()
    counter = 1
    if last_trx:
        match = re.search(r'-(\d+)$', last_trx.transaction_code)
        if match:
            counter = int(match.group(1)) + 1
    return f"{prefix}-{counter:03d}"


@login_required
def consumable_list(request):
    """Menampilkan katalog Master Consumable Item dengan ringkasan KPI,
    filter kategori, lokasi, status persediaan, dan paginasi 25 baris.
    """
    search_query = request.GET.get('q', '').strip()
    category_filter = request.GET.get('category', '').strip()
    location_filter = request.GET.get('location', '').strip()
    status_filter = request.GET.get('status', '').strip()

    # Base queryset
    items_qs = ConsumableItem.objects.all()

    # KPI Summary Counts
    all_items = ConsumableItem.objects.all()
    total_items = all_items.count()
    
    # Agregat kuantitas stok lintas item
    total_stock_qty = all_items.aggregate(total=Sum('stock_available'))['total'] or Decimal('0.00')

    # Item dengan stok habis (<= 0)
    out_of_stock_count = all_items.filter(stock_available__lte=0).count()

    # Item dengan stok menipis (0 < stock <= minimum_stock)
    low_stock_count = all_items.filter(
        stock_available__gt=0,
        stock_available__lte=F('minimum_stock')
    ).count()

    # Item berstatus tersedia normal
    available_count = all_items.filter(
        stock_available__gt=F('minimum_stock')
    ).count()

    # Transaksi bulan berjalan
    now = timezone.now()
    current_month_trxs = ConsumableTransaction.objects.filter(
        transaction_date__year=now.year,
        transaction_date__month=now.month
    ).count()

    counts = {
        'total': total_items,
        'total_qty': total_stock_qty,
        'available': available_count,
        'low_stock': low_stock_count,
        'out_of_stock': out_of_stock_count,
        'month_trxs': current_month_trxs,
    }

    # Penerapan Filter
    if status_filter == 'available':
        items_qs = items_qs.filter(stock_available__gt=F('minimum_stock'))
    elif status_filter == 'low_stock':
        items_qs = items_qs.filter(stock_available__gt=0, stock_available__lte=F('minimum_stock'))
    elif status_filter == 'out_of_stock':
        items_qs = items_qs.filter(stock_available__lte=0)

    if category_filter:
        items_qs = items_qs.filter(category=category_filter)

    if location_filter:
        items_qs = items_qs.filter(location=location_filter)

    if search_query:
        items_qs = items_qs.filter(
            Q(item_code__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(specification__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    # Urutkan berdasarkan status stok (yang habis dan menipis di atas) lalu nama
    items_qs = items_qs.order_by('name')

    # Paginasi 25 item per halaman
    paginator = Paginator(items_qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Master data untuk modal aksi
    active_employees = Employee.objects.filter(is_active=True).order_by('name')
    active_units = AssetUnit.objects.select_related('asset').filter(
        status__in=['tersedia', 'digunakan']
    ).order_by('unit_code')
    selectable_items = ConsumableItem.objects.all().order_by('name')

    return render(request, 'consumable_list.html', {
        'page_obj': page_obj,
        'counts': counts,
        'search_query': search_query,
        'category_filter': category_filter,
        'location_filter': location_filter,
        'status_filter': status_filter,
        'categories': ConsumableItem.CATEGORY_CHOICES,
        'locations': KMH_LOCATIONS,
        'employees': active_employees,
        'units': active_units,
        'selectable_items': selectable_items,
        'today_date': date.today().strftime('%Y-%m-%d'),
    })


@login_required
def consumable_detail(request, item_id):
    """Menampilkan profil detail item consumable beserta buku besar transaksi (stock ledger),
    audit trail historis, dan ringkasan mutasi.
    """
    item = get_object_or_404(ConsumableItem, id=item_id)

    # Ledger transaksi terurut terbaru
    transactions_qs = item.transactions.select_related(
        'recipient_employee', 'related_unit', 'related_unit__asset', 'performed_by'
    ).order_by('-transaction_date', '-created_at', '-id')

    # Paginasi riwayat transaksi 25 per halaman
    paginator = Paginator(transactions_qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistik perputaran item ini
    total_in = item.transactions.filter(transaction_type='in', is_reversed=False).aggregate(
        total=Sum('quantity_base')
    )['total'] or Decimal('0.00')

    total_out = item.transactions.filter(transaction_type='out', is_reversed=False).aggregate(
        total=Sum('quantity_base')
    )['total'] or Decimal('0.00')

    last_transaction = item.transactions.first()

    active_employees = Employee.objects.filter(is_active=True).order_by('name')
    active_units = AssetUnit.objects.select_related('asset').filter(
        status__in=['tersedia', 'digunakan']
    ).order_by('unit_code')

    return render(request, 'consumable_detail.html', {
        'item': item,
        'page_obj': page_obj,
        'total_in': total_in,
        'total_out': total_out,
        'last_transaction': last_transaction,
        'categories': ConsumableItem.CATEGORY_CHOICES,
        'locations': KMH_LOCATIONS,
        'employees': active_employees,
        'units': active_units,
        'today_date': date.today().strftime('%Y-%m-%d'),
    })


@login_required
@operator_required
def consumable_create(request):
    """Menambahkan master Consumable Item baru ke katalog persediaan.
    Jika stok awal diisi > 0, otomatis mencatat transaksi awal terotorisasi pada buku besar.
    """
    if request.method == 'POST':
        item_code = request.POST.get('item_code', '').strip().upper()
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', 'cable')
        brand = request.POST.get('brand', '').strip()
        specification = request.POST.get('specification', '').strip()
        description = request.POST.get('description', '').strip()
        base_unit = request.POST.get('base_unit', '').strip() or 'pcs'
        purchase_unit = request.POST.get('purchase_unit', '').strip()
        location = request.POST.get('location', '').strip() or 'Gudang Induk (GI)'
        notes = request.POST.get('notes', '').strip()

        # Parse angka
        try:
            conversion_rate = Decimal(request.POST.get('conversion_rate', '1.00') or '1.00')
            if conversion_rate <= Decimal('0'):
                conversion_rate = Decimal('1.00')
        except (InvalidOperation, TypeError):
            conversion_rate = Decimal('1.00')

        try:
            minimum_stock = Decimal(request.POST.get('minimum_stock', '0') or '0')
            if minimum_stock < Decimal('0'):
                minimum_stock = Decimal('0')
        except (InvalidOperation, TypeError):
            minimum_stock = Decimal('0')

        try:
            initial_stock = Decimal(request.POST.get('initial_stock', '0') or '0')
            if initial_stock < Decimal('0'):
                initial_stock = Decimal('0')
        except (InvalidOperation, TypeError):
            initial_stock = Decimal('0')

        try:
            last_purchase_price = Decimal(request.POST.get('last_purchase_price', '0') or '0')
            if last_purchase_price < Decimal('0'):
                last_purchase_price = Decimal('0')
        except (InvalidOperation, TypeError):
            last_purchase_price = Decimal('0')

        if not name:
            messages.error(request, "Nama barang wajib diisi!")
            return redirect('consumable_list')

        # Auto-generate item code jika kosong
        if not item_code:
            item_code = _generate_item_code(category)

        # Cek keunikan item code
        if ConsumableItem.objects.filter(item_code=item_code).exists():
            messages.error(request, f'Kode Barang "{item_code}" sudah terdaftar di sistem!')
            return redirect('consumable_list')

        with transaction.atomic():
            item = ConsumableItem.objects.create(
                item_code=item_code,
                name=name,
                category=category,
                brand=brand,
                specification=specification,
                description=description,
                base_unit=base_unit,
                purchase_unit=purchase_unit or None,
                conversion_rate=conversion_rate,
                stock_available=initial_stock,
                minimum_stock=minimum_stock,
                location=location,
                last_purchase_price=last_purchase_price,
                notes=notes
            )

            # Jika stok awal > 0, catat mutasi masuk terotorisasi di buku besar
            if initial_stock > 0:
                trx_code = _generate_trx_code('in')
                ConsumableTransaction.objects.create(
                    transaction_code=trx_code,
                    transaction_type='in',
                    item=item,
                    quantity=initial_stock,
                    unit=base_unit,
                    conversion_rate=Decimal('1.00'),
                    quantity_base=initial_stock,
                    stock_before=Decimal('0.00'),
                    stock_after=initial_stock,
                    source_destination='Stok Awal Terotorisasi',
                    performed_by=request.user,
                    transaction_date=date.today(),
                    notes=f"Inisialisasi stok awal saat pendaftaran item: {initial_stock} {base_unit}."
                )

        messages.success(request, f'Consumable Item "{item.item_code} - {item.name}" berhasil ditambahkan.')
        return redirect('consumable_detail', item_id=item.id)

    return redirect('consumable_list')


@login_required
@operator_required
def consumable_edit(request, item_id):
    """Memperbarui informasi metadata master consumable.
    Catatan: Saldo stok TIDAK dapat diubah sembarangan di sini untuk menjaga integritas buku besar.
    Perubahan stok wajib melalui alur Barang Masuk, Barang Keluar, atau Stock Opname.
    """
    item = get_object_or_404(ConsumableItem, id=item_id)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', item.category)
        brand = request.POST.get('brand', '').strip()
        specification = request.POST.get('specification', '').strip()
        description = request.POST.get('description', '').strip()
        base_unit = request.POST.get('base_unit', item.base_unit).strip()
        purchase_unit = request.POST.get('purchase_unit', '').strip()
        location = request.POST.get('location', item.location).strip()
        notes = request.POST.get('notes', '').strip()

        try:
            conversion_rate = Decimal(request.POST.get('conversion_rate', str(item.conversion_rate)) or '1.00')
            if conversion_rate <= Decimal('0'):
                conversion_rate = Decimal('1.00')
        except (InvalidOperation, TypeError):
            conversion_rate = item.conversion_rate

        try:
            minimum_stock = Decimal(request.POST.get('minimum_stock', str(item.minimum_stock)) or '0')
            if minimum_stock < Decimal('0'):
                minimum_stock = Decimal('0')
        except (InvalidOperation, TypeError):
            minimum_stock = item.minimum_stock

        try:
            last_purchase_price = Decimal(request.POST.get('last_purchase_price', str(item.last_purchase_price)) or '0')
            if last_purchase_price < Decimal('0'):
                last_purchase_price = Decimal('0')
        except (InvalidOperation, TypeError):
            last_purchase_price = item.last_purchase_price

        if not name:
            messages.error(request, "Nama barang tidak boleh kosong!")
            return redirect('consumable_detail', item_id=item.id)

        item.name = name
        item.category = category
        item.brand = brand
        item.specification = specification
        item.description = description
        item.base_unit = base_unit
        item.purchase_unit = purchase_unit or None
        item.conversion_rate = conversion_rate
        item.minimum_stock = minimum_stock
        item.location = location
        item.last_purchase_price = last_purchase_price
        item.notes = notes
        item.save()

        messages.success(request, f'Data master "{item.item_code} - {item.name}" berhasil diperbarui.')
        return redirect('consumable_detail', item_id=item.id)

    return redirect('consumable_detail', item_id=item.id)


@login_required
@operator_required
def consumable_in(request):
    """Alur transaksi Barang Masuk (Restock / Pembelian / Retur Teknisi).
    Menerapkan penguncian baris (select_for_update) dan transaksi atomik database.
    """
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        qty_raw = request.POST.get('quantity', '0')
        unit_type = request.POST.get('unit_type', 'base')  # 'base' atau 'purchase'
        trx_date_raw = request.POST.get('transaction_date')
        source = request.POST.get('source_destination', '').strip() or 'Pembelian / Pengadaan'
        supplier = request.POST.get('supplier', '').strip()
        reference_no = request.POST.get('reference_no', '').strip()
        batch_lot = request.POST.get('batch_lot', '').strip()
        expiry_date_raw = request.POST.get('expiry_date')
        notes = request.POST.get('notes', '').strip()

        # Validasi kuantitas
        try:
            quantity = Decimal(qty_raw)
            if quantity <= Decimal('0'):
                messages.error(request, "Jumlah barang masuk harus bernilai positif lebih dari 0!")
                return redirect(request.META.get('HTTP_REFERER', 'consumable_list'))
        except (InvalidOperation, TypeError):
            messages.error(request, "Jumlah barang masuk tidak valid!")
            return redirect(request.META.get('HTTP_REFERER', 'consumable_list'))

        # Validasi tanggal transaksi
        try:
            trx_date = datetime.strptime(trx_date_raw, '%Y-%m-%d').date() if trx_date_raw else date.today()
        except ValueError:
            trx_date = date.today()

        expiry_date = None
        if expiry_date_raw:
            try:
                expiry_date = datetime.strptime(expiry_date_raw, '%Y-%m-%d').date()
            except ValueError:
                expiry_date = None

        with transaction.atomic():
            # Kunci baris item untuk mencegah race conditions
            item = ConsumableItem.objects.select_for_update().filter(id=item_id).first()
            if not item:
                messages.error(request, "Item consumable yang dipilih tidak ditemukan!")
                return redirect('consumable_list')

            # Tentukan satuan transaksi dan faktor konversi
            if unit_type == 'purchase' and item.purchase_unit:
                unit_label = item.purchase_unit
                conv_rate = item.conversion_rate
                quantity_base = quantity * conv_rate
            else:
                unit_label = item.base_unit
                conv_rate = Decimal('1.00')
                quantity_base = quantity

            stock_before = item.stock_available
            stock_after = stock_before + quantity_base

            item.stock_available = stock_after
            item.save(update_fields=['stock_available', 'updated_at'])

            trx_code = _generate_trx_code('in')
            ConsumableTransaction.objects.create(
                transaction_code=trx_code,
                transaction_type='in',
                item=item,
                quantity=quantity,
                unit=unit_label,
                conversion_rate=conv_rate,
                quantity_base=quantity_base,
                stock_before=stock_before,
                stock_after=stock_after,
                source_destination=source,
                supplier=supplier,
                reference_no=reference_no,
                batch_lot=batch_lot,
                expiry_date=expiry_date,
                performed_by=request.user,
                transaction_date=trx_date,
                notes=notes
            )

        messages.success(
            request,
            f'Barang Masuk Berhasil: +{quantity} {unit_label} ({quantity_base} {item.base_unit}) ditambahkan ke "{item.name}". Saldo sekarang: {item.formatted_stock}.'
        )
        return redirect(request.META.get('HTTP_REFERER', 'consumable_list'))

    return redirect('consumable_list')


@login_required
@operator_required
def consumable_out(request):
    """Alur transaksi Barang Keluar (Pemakaian Teknisi / Operasional Jaringan).
    Memverifikasi kecukupan stok, mengunci baris (select_for_update),
    dan mencegah saldo menjadi negatif secara atomik.
    """
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        qty_raw = request.POST.get('quantity', '0')
        unit_type = request.POST.get('unit_type', 'base')
        trx_date_raw = request.POST.get('transaction_date')
        recipient_id = request.POST.get('recipient_employee')
        related_unit_id = request.POST.get('related_unit')
        ticket_number = request.POST.get('ticket_number', '').strip()
        purpose = request.POST.get('source_destination', '').strip() or 'Kebutuhan Operasional IT'
        notes = request.POST.get('notes', '').strip()

        # Validasi kuantitas
        try:
            quantity = Decimal(qty_raw)
            if quantity <= Decimal('0'):
                messages.error(request, "Jumlah pemakaian harus lebih besar dari 0!")
                return redirect(request.META.get('HTTP_REFERER', 'consumable_list'))
        except (InvalidOperation, TypeError):
            messages.error(request, "Jumlah pemakaian tidak valid!")
            return redirect(request.META.get('HTTP_REFERER', 'consumable_list'))

        try:
            trx_date = datetime.strptime(trx_date_raw, '%Y-%m-%d').date() if trx_date_raw else date.today()
        except ValueError:
            trx_date = date.today()

        recipient = None
        if recipient_id:
            recipient = Employee.objects.filter(id=recipient_id).first()

        related_unit = None
        if related_unit_id:
            related_unit = AssetUnit.objects.filter(id=related_unit_id).first()

        with transaction.atomic():
            # Kunci baris item untuk mencegah concurrency anomaly
            item = ConsumableItem.objects.select_for_update().filter(id=item_id).first()
            if not item:
                messages.error(request, "Item consumable yang dipilih tidak ditemukan!")
                return redirect('consumable_list')

            if unit_type == 'purchase' and item.purchase_unit:
                unit_label = item.purchase_unit
                conv_rate = item.conversion_rate
                quantity_base = quantity * conv_rate
            else:
                unit_label = item.base_unit
                conv_rate = Decimal('1.00')
                quantity_base = quantity

            stock_before = item.stock_available

            # Cek kecukupan stok secara ketat
            if stock_before < quantity_base:
                messages.error(
                    request,
                    f'Pengeluaran ditolak! Stok "{item.name}" tidak mencukupi. Tersedia: {item.formatted_stock}, diminta: {quantity_base} {item.base_unit}.'
                )
                return redirect(request.META.get('HTTP_REFERER', 'consumable_list'))

            stock_after = stock_before - quantity_base
            item.stock_available = stock_after
            item.save(update_fields=['stock_available', 'updated_at'])

            trx_code = _generate_trx_code('out')
            ConsumableTransaction.objects.create(
                transaction_code=trx_code,
                transaction_type='out',
                item=item,
                quantity=quantity,
                unit=unit_label,
                conversion_rate=conv_rate,
                quantity_base=quantity_base,
                stock_before=stock_before,
                stock_after=stock_after,
                source_destination=purpose,
                recipient_employee=recipient,
                related_unit=related_unit,
                ticket_number=ticket_number,
                performed_by=request.user,
                transaction_date=trx_date,
                notes=notes
            )

        messages.success(
            request,
            f'Barang Keluar Berhasil: -{quantity} {unit_label} ({quantity_base} {item.base_unit}) dikeluarkan dari "{item.name}". Sisa stok: {item.formatted_stock}.'
        )
        return redirect(request.META.get('HTTP_REFERER', 'consumable_list'))

    return redirect('consumable_list')


@login_required
@operator_required
def consumable_adjust(request):
    """Alur penyesuaian stok fisik (Stock Opname).
    Menghitung selisih sistem vs fisik aktual, mencatat alasan audit,
    dan menyesuaikan saldo stok secara atomik.
    """
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        actual_stock_raw = request.POST.get('actual_stock', '0')
        reason = request.POST.get('reason', '').strip()
        trx_date_raw = request.POST.get('transaction_date')

        if not reason:
            messages.error(request, "Alasan penyesuaian stok / hasil stock opname wajib diisi!")
            return redirect(request.META.get('HTTP_REFERER', 'consumable_list'))

        try:
            actual_stock = Decimal(actual_stock_raw)
            if actual_stock < Decimal('0'):
                messages.error(request, "Stok fisik aktual tidak boleh negatif!")
                return redirect(request.META.get('HTTP_REFERER', 'consumable_list'))
        except (InvalidOperation, TypeError):
            messages.error(request, "Stok fisik aktual tidak valid!")
            return redirect(request.META.get('HTTP_REFERER', 'consumable_list'))

        try:
            trx_date = datetime.strptime(trx_date_raw, '%Y-%m-%d').date() if trx_date_raw else date.today()
        except ValueError:
            trx_date = date.today()

        with transaction.atomic():
            item = ConsumableItem.objects.select_for_update().filter(id=item_id).first()
            if not item:
                messages.error(request, "Item consumable tidak ditemukan!")
                return redirect('consumable_list')

            stock_before = item.stock_available
            diff = actual_stock - stock_before

            if diff == Decimal('0'):
                messages.info(request, f'Tidak ada selisih stok untuk "{item.name}". Saldo tetap {item.formatted_stock}.')
                return redirect(request.META.get('HTTP_REFERER', 'consumable_list'))

            stock_after = actual_stock
            item.stock_available = stock_after
            item.save(update_fields=['stock_available', 'updated_at'])

            trx_code = _generate_trx_code('adj')
            diff_sign = f"+{diff}" if diff > 0 else f"{diff}"

            ConsumableTransaction.objects.create(
                transaction_code=trx_code,
                transaction_type='adjustment',
                item=item,
                quantity=abs(diff),
                unit=item.base_unit,
                conversion_rate=Decimal('1.00'),
                quantity_base=abs(diff),
                stock_before=stock_before,
                stock_after=stock_after,
                source_destination='Stock Opname / Penyesuaian Fisik',
                performed_by=request.user,
                transaction_date=trx_date,
                notes=f"Penyesuaian Fisik: Selisih {diff_sign} {item.base_unit}. Alasan: {reason}"
            )

        messages.success(
            request,
            f'Penyesuaian Stok Berhasil: Saldo "{item.name}" disesuaikan dari {stock_before} menjadi {stock_after} {item.base_unit} (Selisih: {diff_sign} {item.base_unit}).'
        )
        return redirect(request.META.get('HTTP_REFERER', 'consumable_list'))

    return redirect('consumable_list')


@login_required
@operator_required
def consumable_transaction_reverse(request, trx_id):
    """Membatalkan/membalik transaksi yang telah diposting (Reversal Transaction).
    Alih-alih menghapus data riwayat yang dapat merusak audit trail,
    sistem membuat transaksi pembalik dan menandai transaksi lama sebagai is_reversed=True.
    """
    if request.method == 'POST':
        reversal_reason = request.POST.get('reversal_reason', '').strip()
        if not reversal_reason:
            messages.error(request, "Alasan pembatalan / reversal wajib diisi!")
            return redirect(request.META.get('HTTP_REFERER', 'consumable_list'))

        with transaction.atomic():
            trx = ConsumableTransaction.objects.select_for_update().filter(id=trx_id).first()
            if not trx:
                messages.error(request, "Transaksi tidak ditemukan!")
                return redirect('consumable_list')

            if trx.is_reversed:
                messages.error(request, "Transaksi ini sudah pernah dibatalkan (dibalik) sebelumnya!")
                return redirect(request.META.get('HTTP_REFERER', 'consumable_list'))

            if trx.transaction_type == 'reversal':
                messages.error(request, "Transaksi reversal tidak dapat dibalik kembali!")
                return redirect(request.META.get('HTTP_REFERER', 'consumable_list'))

            item = ConsumableItem.objects.select_for_update().get(id=trx.item_id)
            stock_before = item.stock_available

            # Hitung efek pembalik
            if trx.transaction_type == 'in':
                # Barang masuk dibatalkan -> kurangi stok
                if stock_before < trx.quantity_base:
                    messages.error(
                        request,
                        f'Pembatalan gagal! Stok "{item.name}" saat ini ({stock_before}) lebih kecil dari kuantitas yang hendak dibalik ({trx.quantity_base}).'
                    )
                    return redirect(request.META.get('HTTP_REFERER', 'consumable_list'))
                stock_after = stock_before - trx.quantity_base

            elif trx.transaction_type == 'out':
                # Barang keluar dibatalkan -> kembalikan stok
                stock_after = stock_before + trx.quantity_base

            elif trx.transaction_type == 'adjustment':
                # Penyesuaian dibatalkan -> kembalikan ke stock_before sebelum penyesuaian
                stock_after = trx.stock_before

            else:
                messages.error(request, "Tipe transaksi tidak valid untuk dibalik!")
                return redirect(request.META.get('HTTP_REFERER', 'consumable_list'))

            item.stock_available = stock_after
            item.save(update_fields=['stock_available', 'updated_at'])

            # Buat entri transaksi reversal
            rev_code = _generate_trx_code('rev')
            rev_trx = ConsumableTransaction.objects.create(
                transaction_code=rev_code,
                transaction_type='reversal',
                item=item,
                quantity=trx.quantity,
                unit=trx.unit,
                conversion_rate=trx.conversion_rate,
                quantity_base=trx.quantity_base,
                stock_before=stock_before,
                stock_after=stock_after,
                source_destination=f"Reversal dari {trx.transaction_code}",
                performed_by=request.user,
                transaction_date=date.today(),
                notes=f"Pembalikan transaksi {trx.transaction_code}. Alasan: {reversal_reason}"
            )

            # Tandai transaksi asal
            trx.is_reversed = True
            trx.reversed_by = rev_trx
            trx.save(update_fields=['is_reversed', 'reversed_by'])

        messages.success(
            request,
            f'Transaksi "{trx.transaction_code}" berhasil dibalik. Saldo stok "{item.name}" disesuaikan menjadi {stock_after} {item.base_unit}.'
        )
        return redirect(request.META.get('HTTP_REFERER', 'consumable_list'))

    return redirect('consumable_list')


@login_required
def consumable_export_excel(request):
    """Menghasilkan laporan Excel profesional untuk katalog persediaan consumable item."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

    search_query = request.GET.get('q', '').strip()
    category_filter = request.GET.get('category', '').strip()
    status_filter = request.GET.get('status', '').strip()

    items_qs = ConsumableItem.objects.all().order_by('category', 'name')

    if status_filter == 'available':
        items_qs = items_qs.filter(stock_available__gt=F('minimum_stock'))
    elif status_filter == 'low_stock':
        items_qs = items_qs.filter(stock_available__gt=0, stock_available__lte=F('minimum_stock'))
    elif status_filter == 'out_of_stock':
        items_qs = items_qs.filter(stock_available__lte=0)

    if category_filter:
        items_qs = items_qs.filter(category=category_filter)

    if search_query:
        items_qs = items_qs.filter(
            Q(item_code__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(specification__icontains=search_query)
        )

    wb = Workbook()
    ws = wb.active
    ws.title = "Katalog Consumable"

    # Styling
    title_font = Font(size=14, bold=True, color="1B5E20")
    subtitle_font = Font(size=10, italic=True, color="555555")
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1B5E20", end_color="1B5E20", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")
    thin_border = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )

    # Header Title
    ws.merge_cells('A1:I1')
    ws['A1'] = "LAPORAN PERSEDIAAN CONSUMABLE ITEM - PT. KERINCI HYDROPOWER"
    ws['A1'].font = title_font
    ws['A1'].alignment = left_align

    ws.merge_cells('A2:I2')
    ws['A2'] = f"Tanggal Ekspor: {datetime.now().strftime('%d %B %Y %H:%M')} WIB | Dicetak oleh: {request.user.get_full_name() or request.user.username}"
    ws['A2'].font = subtitle_font
    ws['A2'].alignment = left_align

    # Table Columns
    headers = [
        "No", "Kode Barang", "Nama Barang", "Kategori", "Merek / Spesifikasi",
        "Satuan", "Stok Tersedia", "Stok Minimum", "Status Persediaan", "Lokasi"
    ]
    
    ws.append([]) # Row 3 blank
    ws.append(headers) # Row 4 header

    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    for idx, item in enumerate(items_qs, 1):
        status_disp = item.stock_status_display
        row_data = [
            idx,
            item.item_code,
            item.name,
            item.get_category_display(),
            f"{item.brand or '-'} / {item.specification or '-'}",
            item.base_unit,
            float(item.stock_available),
            float(item.minimum_stock),
            status_disp,
            item.location
        ]
        ws.append(row_data)
        curr_row = 4 + idx

        # Set alignments & borders
        ws.cell(row=curr_row, column=1).alignment = center_align
        ws.cell(row=curr_row, column=2).alignment = center_align
        ws.cell(row=curr_row, column=3).alignment = left_align
        ws.cell(row=curr_row, column=4).alignment = left_align
        ws.cell(row=curr_row, column=5).alignment = left_align
        ws.cell(row=curr_row, column=6).alignment = center_align
        ws.cell(row=curr_row, column=7).alignment = right_align
        ws.cell(row=curr_row, column=8).alignment = right_align
        ws.cell(row=curr_row, column=9).alignment = center_align
        ws.cell(row=curr_row, column=10).alignment = left_align

        for c in range(1, 11):
            ws.cell(row=curr_row, column=c).border = thin_border

        # Highlight out of stock / low stock
        if item.stock_available <= 0:
            ws.cell(row=curr_row, column=9).fill = PatternFill(start_color="FFEBEE", end_color="FFEBEE", fill_type="solid")
            ws.cell(row=curr_row, column=9).font = Font(color="C62828", bold=True)
        elif item.stock_available <= item.minimum_stock:
            ws.cell(row=curr_row, column=9).fill = PatternFill(start_color="FFF8E1", end_color="FFF8E1", fill_type="solid")
            ws.cell(row=curr_row, column=9).font = Font(color="E65100", bold=True)

    # Column widths
    col_widths = [6, 16, 30, 24, 30, 10, 14, 14, 18, 22]
    for i, w in enumerate(col_widths, 1):
        from openpyxl.utils import get_column_letter
        ws.column_dimensions[get_column_letter(i)].width = w

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"Laporan_Consumable_PTKMH_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


@login_required
def consumable_export_pdf(request):
    """Menghasilkan laporan PDF ringkasan status persediaan consumable."""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor, white, black
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from io import BytesIO

    search_query = request.GET.get('q', '').strip()
    category_filter = request.GET.get('category', '').strip()
    status_filter = request.GET.get('status', '').strip()

    items_qs = ConsumableItem.objects.all().order_by('category', 'name')

    if status_filter == 'available':
        items_qs = items_qs.filter(stock_available__gt=F('minimum_stock'))
    elif status_filter == 'low_stock':
        items_qs = items_qs.filter(stock_available__gt=0, stock_available__lte=F('minimum_stock'))
    elif status_filter == 'out_of_stock':
        items_qs = items_qs.filter(stock_available__lte=0)

    if category_filter:
        items_qs = items_qs.filter(category=category_filter)

    if search_query:
        items_qs = items_qs.filter(
            Q(item_code__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(specification__icontains=search_query)
        )

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=HexColor('#1b5e20'),
        alignment=TA_LEFT
    )
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=HexColor('#555555'),
        alignment=TA_LEFT
    )
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        alignment=TA_LEFT
    )
    cell_center = ParagraphStyle(
        'CellCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        alignment=TA_CENTER
    )
    header_style = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=white,
        alignment=TA_CENTER
    )

    story = []
    story.append(Paragraph("LAPORAN PERSEDIAAN CONSUMABLE ITEM - PT. KERINCI HYDROPOWER", title_style))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        f"Dicetak: {datetime.now().strftime('%d/%m/%Y %H:%M')} WIB | Oleh: {request.user.get_full_name() or request.user.username} | Total: {items_qs.count()} item",
        meta_style
    ))
    story.append(Spacer(1, 5 * mm))

    table_data = [[
        Paragraph("No", header_style),
        Paragraph("Kode", header_style),
        Paragraph("Nama Barang", header_style),
        Paragraph("Kategori", header_style),
        Paragraph("Merek & Spesifikasi", header_style),
        Paragraph("Satuan", header_style),
        Paragraph("Stok", header_style),
        Paragraph("Min", header_style),
        Paragraph("Status", header_style),
        Paragraph("Lokasi", header_style),
    ]]

    for idx, itm in enumerate(items_qs, 1):
        status_text = itm.stock_status_display
        status_color = "#1b5e20" if itm.stock_status == 'available' else ("#e65100" if itm.stock_status == 'low_stock' else "#c62828")
        status_cell = f"<font color='{status_color}'><b>{status_text}</b></font>"

        table_data.append([
            Paragraph(str(idx), cell_center),
            Paragraph(itm.item_code, cell_center),
            Paragraph(itm.name, cell_style),
            Paragraph(itm.get_category_display().split('(')[0].strip(), cell_style),
            Paragraph(f"{itm.brand or '-'} / {itm.specification or '-'}", cell_style),
            Paragraph(itm.base_unit, cell_center),
            Paragraph(f"<b>{itm.stock_available}</b>", cell_center),
            Paragraph(str(itm.minimum_stock), cell_center),
            Paragraph(status_cell, cell_center),
            Paragraph(itm.location, cell_style),
        ])

    col_widths = [10 * mm, 25 * mm, 50 * mm, 38 * mm, 50 * mm, 16 * mm, 18 * mm, 16 * mm, 22 * mm, 28 * mm]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1b5e20')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e0e0e0')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t)

    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"Laporan_Consumable_PTKMH_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response
