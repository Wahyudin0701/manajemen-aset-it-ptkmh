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
    """Menghasilkan laporan PDF resmi untuk Consumable Item yang seragam dengan modul lainnya."""
    import os
    import datetime
    from io import BytesIO
    from PIL import Image

    from django.conf import settings
    from django.http import HttpResponse
    from django.db.models import Q, F

    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm, cm
    from reportlab.lib.colors import HexColor, white
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.platypus import Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    search_query = request.GET.get('q', '').strip()
    category_filter = request.GET.get('category', '').strip()
    status_filter = request.GET.get('status', '').strip()
    location_filter = request.GET.get('location', '').strip()

    items_qs = ConsumableItem.objects.all().order_by('category', 'name')

    status_labels = {
        'available': 'Stok Aman',
        'low_stock': 'Stok Menipis',
        'out_of_stock': 'Stok Habis',
    }
    status_label = status_labels.get(status_filter, 'Semua Status')

    if status_filter == 'available':
        items_qs = items_qs.filter(stock_available__gt=F('minimum_stock'))
    elif status_filter == 'low_stock':
        items_qs = items_qs.filter(stock_available__gt=0, stock_available__lte=F('minimum_stock'))
    elif status_filter == 'out_of_stock':
        items_qs = items_qs.filter(stock_available__lte=0)

    cat_dict = dict(ConsumableItem.CATEGORY_CHOICES)
    cat_label = cat_dict.get(category_filter, 'Semua Kategori') if category_filter else 'Semua Kategori'
    if category_filter:
        items_qs = items_qs.filter(category=category_filter)

    if location_filter:
        items_qs = items_qs.filter(location=location_filter)

    if search_query:
        items_qs = items_qs.filter(
            Q(item_code__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(specification__icontains=search_query)
        )

    navy = HexColor('#002060')
    alt_row = HexColor('#F8F9FC')
    border_color = HexColor('#D0D5DD')

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=2 * cm
    )
    page_width = landscape(A4)[0] - 3 * cm

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=16, textColor=white, leading=20)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=HexColor('#B0C4DE'), leading=14)
    company_style = ParagraphStyle('CompanyName', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=white, alignment=TA_RIGHT, leading=14)
    company_sub_style = ParagraphStyle('CompanySub', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=HexColor('#B0C4DE'), alignment=TA_RIGHT, leading=11)

    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=11)
    cell_bold_style = ParagraphStyle('CellBoldStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=11)
    cell_small = ParagraphStyle('CellSmall', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, textColor=HexColor('#666666'), leading=9)
    header_cell = ParagraphStyle('HeaderCell', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=white, alignment=TA_CENTER, leading=11)
    cell_center = ParagraphStyle('CellCenter', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, alignment=TA_CENTER)
    info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=HexColor('#555555'))
    info_bold = ParagraphStyle('InfoBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=HexColor('#333333'))

    elements = []
    now = datetime.datetime.now()
    bulan_indo = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    tanggal_str = f"{now.day} {bulan_indo[now.month]} {now.year}"

    # Top Logos
    try:
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
            ('TOPPADDING', (0, 0), (-1, -1), 0)
        ]))
        elements.append(logo_table)
    except Exception:
        pass

    category_label = f"Status: {status_label} - Kategori: {cat_label}"

    # Navy Header Banner
    header_data = [[
        [Paragraph('Laporan Consumable Item', title_style), Paragraph(f'{category_label} - {tanggal_str}', subtitle_style)],
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
    elements.append(Spacer(1, 8 * mm))

    # Metadata Grid
    total_data = items_qs.count()
    info_data = [
        [Paragraph('Kategori', info_style), Paragraph(f': {category_label}', info_bold), Paragraph('Total Data', info_style), Paragraph(f': {total_data} item', info_bold)]
    ]
    row_2 = [Paragraph('Tanggal Cetak', info_style), Paragraph(f': {tanggal_str}, {now.strftime("%H:%M")} WIB', info_bold)]
    filters_desc = []
    if location_filter: filters_desc.append(f"Lokasi: {location_filter}")
    if search_query: filters_desc.append(f"Cari: '{search_query}'")
    if filters_desc:
        row_2.extend([Paragraph('Filter', info_style), Paragraph(f': {", ".join(filters_desc)}', info_bold)])
    else:
        row_2.extend(['', ''])
    info_data.append(row_2)

    info_table = Table(info_data, colWidths=[page_width * 0.12, page_width * 0.38, page_width * 0.12, page_width * 0.38])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0)
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6 * mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceAfter=4 * mm))

    # Table Header & Data
    table_header = [
        Paragraph('NO', header_cell),
        Paragraph('KODE ITEM', header_cell),
        Paragraph('NAMA BARANG & MEREK', header_cell),
        Paragraph('KATEGORI', header_cell),
        Paragraph('SPESIFIKASI', header_cell),
        Paragraph('SATUAN', header_cell),
        Paragraph('STOK', header_cell),
        Paragraph('STATUS', header_cell),
        Paragraph('LOKASI', header_cell)
    ]
    col_widths = [
        page_width * 0.05,
        page_width * 0.13,
        page_width * 0.24,
        page_width * 0.12,
        page_width * 0.18,
        page_width * 0.06,
        page_width * 0.07,
        page_width * 0.07,
        page_width * 0.08
    ]
    table_data = [table_header]

    for idx, itm in enumerate(items_qs, 1):
        item_info = [Paragraph(itm.name, cell_bold_style)]
        if itm.brand:
            item_info.append(Paragraph(f"Merek: {itm.brand}", cell_small))

        status_text = "Aman" if itm.stock_status == 'available' else ("Menipis" if itm.stock_status == 'low_stock' else "Habis")

        row = [
            Paragraph(str(idx), cell_center),
            Paragraph(itm.item_code, cell_bold_style),
            item_info,
            Paragraph(itm.get_category_display().split('(')[0].strip(), cell_center),
            Paragraph(itm.specification or "-", cell_small),
            Paragraph(itm.base_unit, cell_center),
            Paragraph(f"<b>{itm.formatted_stock}</b>", cell_center),
            Paragraph(status_text, cell_center),
            Paragraph(itm.location or "-", cell_center)
        ]
        table_data.append(row)

    if total_data == 0:
        table_data.append([
            Paragraph("Belum ada data Consumable Item yang cocok dengan kriteria laporan.", cell_center),
            "", "", "", "", "", "", "", ""
        ])

    data_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), navy),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, 0), (-1, 0), 1, navy),
        ('LINEBELOW', (0, 1), (-1, -2), 0.5, HexColor('#E5E7EB')),
        ('LINEBELOW', (0, -1), (-1, -1), 1, border_color),
    ]
    if total_data == 0:
        table_style.append(('SPAN', (0, 1), (-1, 1)))
        table_style.append(('ALIGN', (0, 1), (-1, 1), 'CENTER'))
        table_style.append(('TOPPADDING', (0, 1), (-1, 1), 16))
        table_style.append(('BOTTOMPADDING', (0, 1), (-1, 1), 16))
    else:
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                table_style.append(('BACKGROUND', (0, i), (-1, i), alt_row))

    data_table.setStyle(TableStyle(table_style))
    elements.append(data_table)

    elements.append(Spacer(1, 5 * mm))
    elements.append(Paragraph(
        f"Menampilkan {total_data} item — Dokumen ini digenerate secara otomatis oleh Sistem Manajemen Aset IT pada {tanggal_str}.",
        ParagraphStyle('F', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=HexColor('#999999'))
    ))

    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"Laporan_Consumable_Item_{now.strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response