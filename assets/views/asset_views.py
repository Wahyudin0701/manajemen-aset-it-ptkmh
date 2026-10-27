import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.core.paginator import Paginator
from assets.models import Asset, AssetUnit, Category, Employee, UnitLog
from assets.permissions import operator_required


@login_required
def asset_list(request):
    """Menampilkan katalog master jenis aset dengan tab Karyawan/Network dan paginasi."""
    search_query = request.GET.get('q', '').strip()
    active_tab = request.GET.get('tab', 'karyawan')

    assets_qs = Asset.objects.select_related('category').annotate(
        unit_tersedia=Count('units', filter=Q(units__status='tersedia')),
        unit_digunakan=Count('units', filter=Q(units__status='digunakan')),
        total_units=Count('units'),
    )

    if search_query:
        assets_qs = assets_qs.filter(
            Q(asset_code__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(brand__icontains=search_query)
        )

    if active_tab == 'network':
        assets_qs = assets_qs.filter(category__name__icontains='Network')
    else:
        assets_qs = assets_qs.filter(category__name__icontains='Karyawan')

    assets_qs = assets_qs.order_by('asset_code')
    categories = Category.objects.all().order_by('name')

    counts = {
        'karyawan': Asset.objects.filter(category__name__icontains='Karyawan').count(),
        'network': Asset.objects.filter(category__name__icontains='Network').count(),
    }

    # Implementasi Pagination (25 aset per halaman)
    paginator = Paginator(assets_qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'asset_list.html', {
        'assets': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'active_tab': active_tab,
        'categories': categories,
        'counts': counts,
    })


@login_required
@operator_required
def asset_add(request):
    """Menambahkan master jenis aset baru."""
    if request.method == 'POST':
        category_id = request.POST.get('category')
        asset_code = request.POST.get('asset_code', '').strip().upper()
        name = request.POST.get('name', '').strip()
        brand = request.POST.get('brand', '').strip()
        uom = request.POST.get('uom', '').strip()

        if Asset.objects.filter(asset_code=asset_code).exists():
            return JsonResponse({'success': False, 'error': f"Kode Aset '{asset_code}' sudah digunakan. Silakan pilih kode lain."})

        Asset.objects.create(
            category_id=category_id,
            asset_code=asset_code,
            name=name,
            brand=brand,
            uom=uom
        )
        messages.success(request, f'Aset {name} berhasil ditambahkan.')
        return JsonResponse({'success': True})
    return redirect('asset_list')


@login_required
@operator_required
def asset_edit(request, asset_id):
    """Memperbarui informasi master aset dan menyinkronkan kode unit jika kode aset berubah."""
    asset = get_object_or_404(Asset, id=asset_id)
    if request.method == 'POST':
        category_id = request.POST.get('category')
        new_code = request.POST.get('asset_code', '').strip().upper()
        name = request.POST.get('name', '').strip()
        brand = request.POST.get('brand', '').strip()
        uom = request.POST.get('uom', '').strip()

        old_code = asset.asset_code
        if new_code and new_code != old_code:
            if Asset.objects.exclude(id=asset.id).filter(asset_code=new_code).exists():
                return JsonResponse({'success': False, 'error': f"Kode Aset '{new_code}' sudah digunakan oleh aset lain."})

            # Validasi benturan kode unit turunan
            for unit in asset.units.all():
                if unit.unit_code.startswith(f"{old_code}-"):
                    suffix = unit.unit_code[len(f"{old_code}-"):]
                elif '-' in unit.unit_code:
                    suffix = unit.unit_code.rsplit('-', 1)[-1]
                else:
                    suffix = unit.unit_code
                target_unit_code = f"{new_code}-{suffix}"
                if AssetUnit.objects.exclude(asset=asset).filter(unit_code=target_unit_code).exists():
                    return JsonResponse({'success': False, 'error': f"Gagal mengubah kode aset: Kode unit '{target_unit_code}' sudah digunakan oleh unit lain di sistem."})

            asset.asset_code = new_code

        asset.category_id = category_id
        asset.name = name
        asset.brand = brand
        asset.uom = uom
        asset.save()

        messages.success(request, f'Perubahan pada aset {new_code} berhasil disimpan.')
        return JsonResponse({'success': True})
    return redirect('asset_list')


@login_required
@operator_required
def asset_delete(request, asset_id):
    """Menghapus master jenis aset beserta unit fisiknya secara cascade."""
    asset = get_object_or_404(Asset, id=asset_id)
    if request.method == 'POST':
        asset.delete()
        messages.success(request, "Data aset berhasil dihapus.")
        return redirect('asset_list')
    return redirect('asset_list')


@login_required
def asset_units(request, asset_id):
    """Menampilkan seluruh unit fisik individual yang terdaftar pada jenis aset tertentu."""
    asset = get_object_or_404(Asset, id=asset_id)
    units = asset.units.all().order_by('unit_code')
    employees = Employee.objects.filter(is_active=True).order_by('name')

    tersedia = units.filter(status='tersedia').count()
    digunakan = units.filter(status='digunakan').count()

    return render(request, 'asset_units.html', {
        'asset': asset,
        'units': units,
        'employees': employees,
        'tersedia': tersedia,
        'digunakan': digunakan
    })


@login_required
@operator_required
def unit_add(request, asset_id):
    """Mendaftarkan unit fisik baru di bawah jenis aset induk."""
    if request.method == 'POST':
        asset = get_object_or_404(Asset, id=asset_id)
        suffix = request.POST.get('unit_code_suffix', '').strip()
        serial_number = request.POST.get('serial_number', '').strip()
        status = 'tersedia'

        if suffix:
            unit_code = f"{asset.asset_code}-{suffix}"
            if AssetUnit.objects.filter(unit_code=unit_code).exists():
                if request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': f'Kode Unit "{unit_code}" sudah terdaftar di sistem!'}, status=400)
                messages.error(request, f'Kode Unit "{unit_code}" sudah terdaftar di sistem!')
                return redirect('asset_units', asset_id=asset_id)
            else:
                new_unit = AssetUnit.objects.create(
                    asset=asset,
                    unit_code=unit_code,
                    serial_number=serial_number or None,
                    status=status
                )
                log_notes = "Ditambahkan ke Sistem"
                if serial_number:
                    log_notes += f" (S/N: {serial_number})"
                UnitLog.objects.create(unit=new_unit, action='created', notes=log_notes)

                asset.qty = asset.units.count()
                asset.save()
                messages.success(request, "Unit fisik berhasil ditambahkan.")

        if request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})

    return redirect('asset_units', asset_id=asset_id)


@login_required
@operator_required
def unit_edit(request, unit_id):
    """Memperbarui informasi kode unit, nomor seri (serial number), dan status operasionalnya."""
    unit = get_object_or_404(AssetUnit, id=unit_id)
    old_status = unit.status
    old_assigned = unit.assigned_to

    if request.method == 'POST':
        suffix = request.POST.get('unit_code_suffix', '').strip()
        new_unit_code = f"{unit.asset.asset_code}-{suffix}" if suffix else unit.unit_code

        if AssetUnit.objects.exclude(id=unit.id).filter(unit_code=new_unit_code).exists():
            if request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': f'Kode Unit "{new_unit_code}" sudah digunakan oleh unit lain!'}, status=400)
            messages.error(request, f'Kode Unit "{new_unit_code}" sudah digunakan oleh unit lain!')
            return redirect('asset_units', asset_id=unit.asset.id)

        old_code = unit.unit_code
        unit.unit_code = new_unit_code

        old_sn = unit.serial_number or ''
        new_sn = request.POST.get('serial_number', '').strip()
        unit.serial_number = new_sn or None

        new_status = request.POST.get('status')
        if new_status:
            unit.status = new_status
            if new_status in ['tersedia', 'pensiun']:
                unit.assigned_to = None

        unit.save()
        new_assigned = unit.assigned_to

        changes = []
        if old_code != new_unit_code:
            changes.append(f"Kode unit diubah dari {old_code} menjadi {new_unit_code}")
        if old_sn != (new_sn or ''):
            changes.append(f"Serial Number diubah dari '{old_sn or '-'}' menjadi '{new_sn or '-'}'")

        notes = request.POST.get('notes', '')
        if new_status and (old_status != new_status or old_assigned != new_assigned):
            if old_status == 'digunakan' and new_status == 'tersedia':
                UnitLog.objects.create(unit=unit, action='returned', employee=old_assigned, notes=notes or "Dikembalikan ke gudang")
            elif old_status == 'tersedia' and new_status == 'digunakan':
                UnitLog.objects.create(unit=unit, action='assigned', employee=new_assigned, notes=notes or "Diserahkan ke karyawan (Manual Edit)")
            elif old_status == 'digunakan' and new_status == 'digunakan' and old_assigned != new_assigned:
                UnitLog.objects.create(unit=unit, action='returned', employee=old_assigned, notes="Mutasi: Dikembalikan oleh pemegang sebelumnya")
                UnitLog.objects.create(unit=unit, action='assigned', employee=new_assigned, notes=notes or "Mutasi: Diserahkan ke pemegang baru")
            elif new_status == 'rusak' and old_status != 'rusak':
                UnitLog.objects.create(unit=unit, action='maintenance_in', employee=old_assigned, notes=notes or "Unit dilaporkan rusak / masuk maintenance")
            elif old_status == 'rusak' and new_status == 'tersedia':
                UnitLog.objects.create(unit=unit, action='maintenance_out', notes=notes or "Perbaikan selesai, unit kembali tersedia")
            elif old_status == 'rusak' and new_status == 'digunakan':
                UnitLog.objects.create(unit=unit, action='maintenance_out', employee=new_assigned, notes=notes or "Perbaikan selesai, unit kembali digunakan oleh karyawan")
            elif new_status == 'pensiun':
                UnitLog.objects.create(unit=unit, action='retired', notes=notes or "Unit dipensiunkan")
            elif old_status == 'pensiun' and new_status != 'pensiun':
                UnitLog.objects.create(unit=unit, action='other', notes=notes or f"Status dipulihkan dari pensiun menjadi {new_status}")
            else:
                UnitLog.objects.create(unit=unit, action='other', notes=notes or f"Status diubah dari {old_status} menjadi {new_status}")
            if changes:
                UnitLog.objects.create(unit=unit, action='other', notes="; ".join(changes))
        elif changes:
            UnitLog.objects.create(unit=unit, action='other', notes="; ".join(changes))

        messages.success(request, f"Unit {unit.unit_code} berhasil diperbarui.")
        if request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})

    return redirect('asset_units', asset_id=unit.asset.id)


@login_required
@operator_required
def unit_update_status(request, unit_id):
    """Memperbarui status unit dan metadata area lokasi untuk aset jaringan."""
    if request.method == 'POST':
        unit = get_object_or_404(AssetUnit, id=unit_id)
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        old_status = unit.status
        is_network = 'Network' in unit.asset.category.name

        new_area = request.POST.get('area')
        new_location = request.POST.get('location')

        status_changed = new_status and new_status != old_status
        location_changed = False

        if is_network and new_status in ['digunakan', 'rusak']:
            if unit.area != new_area or unit.location != new_location:
                location_changed = True

        if status_changed or location_changed:
            unit.status = new_status
            action_type = 'updated'
            log_notes = ""

            if status_changed:
                log_notes += f"Status diubah dari '{old_status}' menjadi '{new_status}'. "
                if new_status == 'rusak':
                    action_type = 'maintenance_in'
                elif old_status == 'rusak' and (new_status == 'digunakan' or new_status == 'tersedia'):
                    action_type = 'maintenance_out'
            elif location_changed:
                log_notes += "Lokasi / Area diperbarui. "

            if new_status in ['digunakan', 'rusak'] and is_network:
                unit.area = new_area
                unit.location = new_location
                log_notes += f"Pemasangan di {unit.area}, {unit.location}. "
            elif new_status == 'tersedia':
                unit.area = None
                unit.location = None

            if notes:
                log_notes += f"Catatan: {notes}"

            unit.save()

            UnitLog.objects.create(
                unit=unit,
                action=action_type,
                employee=unit.assigned_to,
                notes=log_notes.strip()
            )
            messages.success(request, "Status unit berhasil diperbarui.")

    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
@operator_required
def unit_delete(request, unit_id):
    """Menghapus unit fisik individual dan memperbarui kuantitas aset induk."""
    unit = get_object_or_404(AssetUnit, id=unit_id)
    asset_id = unit.asset.id
    if request.method == 'POST':
        unit.delete()
        asset = Asset.objects.get(id=asset_id)
        asset.qty = asset.units.count()
        asset.save()
        messages.success(request, "Unit berhasil dihapus.")
    return redirect('asset_units', asset_id=asset_id)


@login_required
def unit_history(request, unit_id):
    """Menampilkan timeline kronologis riwayat log peristiwa pada suatu unit."""
    unit = get_object_or_404(AssetUnit, id=unit_id)
    logs_qs = unit.logs.all().select_related('employee')

    logs = []
    pattern = re.compile(r"^(.+?) \((.+?)\) - (.*)$")

    for log in logs_qs:
        log.deleted_employee_name = None
        if not log.employee and log.notes:
            match = pattern.match(log.notes.strip())
            if match:
                name, nik, rest_of_notes = match.groups()
                log.deleted_employee_name = name
                log.notes = rest_of_notes.strip()
        logs.append(log)

    return render(request, 'unit_history.html', {'unit': unit, 'logs': logs})
