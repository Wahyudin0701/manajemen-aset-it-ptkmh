from django.db import transaction
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
import qrcode
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count

import datetime
import re
from django.http import JsonResponse
from .models import Asset, AssetUnit, UnitLog, Category, Employee, AssetAssignment

@login_required
def dashboard(request):
    # Top 2 cards: Aset Karyawan & Aset Network
    count_karyawan = AssetUnit.objects.filter(asset__category__name__icontains='Karyawan').count()
    count_network = AssetUnit.objects.filter(asset__category__name__icontains='Network').count()
    
    # 3 Status cards
    count_tersedia = AssetUnit.objects.filter(status='tersedia').count()
    count_digunakan = AssetUnit.objects.filter(status='digunakan').count()
    count_maintenance = AssetUnit.objects.filter(status='rusak').count()
    
    # Recent logs for the 3 lists
    recent_handovers = AssetAssignment.objects.filter(type='handover').select_related('unit', 'unit__asset', 'employee').order_by('-assigned_date', '-id')[:5]
    recent_mutations = AssetAssignment.objects.filter(type='mutation').select_related('unit', 'unit__asset', 'employee', 'from_employee').order_by('-assigned_date', '-id')[:3]
    recent_returns = AssetAssignment.objects.filter(type='return').select_related('unit', 'unit__asset', 'employee').order_by('-assigned_date', '-id')[:3]
    
    context = {
        'count_karyawan': count_karyawan,
        'count_network': count_network,
        'count_tersedia': count_tersedia,
        'count_digunakan': count_digunakan,
        'count_maintenance': count_maintenance,
        'recent_handovers': recent_handovers,
        'recent_mutations': recent_mutations,
        'recent_returns': recent_returns,
    }
    return render(request, 'dashboard.html', context)

@login_required
def asset_list(request):
    search_query = request.GET.get('q', '')
    active_tab = request.GET.get('tab', 'karyawan') # Default tab
    
    # Query dasar beserta perhitungan anotasi unit
    assets = Asset.objects.select_related('category').annotate(
        unit_tersedia=Count('units', filter=Q(units__status='tersedia')),
        unit_digunakan=Count('units', filter=Q(units__status='digunakan')),
        total_units=Count('units'),
    )
    
    if search_query:
        assets = assets.filter(
            Q(asset_code__icontains=search_query) | 
            Q(name__icontains=search_query) |
            Q(brand__icontains=search_query)
        )
        
    if active_tab == 'network':
        assets = assets.filter(category__name__icontains='Network')
    else:
        assets = assets.filter(category__name__icontains='Karyawan')

    assets = assets.order_by('asset_code')
    categories = Category.objects.all().order_by('name')
    
    counts = {
        'karyawan': Asset.objects.filter(category__name__icontains='Karyawan').count(),
        'network': Asset.objects.filter(category__name__icontains='Network').count(),
    }
    
    return render(request, 'asset_list.html', {
        'assets': assets,
        'search_query': search_query,
        'active_tab': active_tab,
        'categories': categories,
        'counts': counts,
    })

@login_required
def asset_add(request):
    if request.method == 'POST':
        category_id = request.POST.get('category')
        asset_code = request.POST.get('asset_code').strip().upper()
        name = request.POST.get('name').strip()
        brand = request.POST.get('brand').strip()
        uom = request.POST.get('uom').strip()
        
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
def asset_edit(request, asset_id):
    asset = get_object_or_404(Asset, id=asset_id)
    if request.method == 'POST':
        category_id = request.POST.get('category')
        new_code = request.POST.get('asset_code').strip().upper()
        name = request.POST.get('name').strip()
        brand = request.POST.get('brand').strip()
        uom = request.POST.get('uom').strip()
        
        old_code = asset.asset_code
        if new_code and new_code != old_code:
            if Asset.objects.exclude(id=asset.id).filter(asset_code=new_code).exists():
                return JsonResponse({'success': False, 'error': f"Kode Aset '{new_code}' sudah digunakan oleh aset lain."})
            asset.asset_code = new_code
            
        asset.category_id = category_id
        asset.name = name
        asset.brand = brand
        asset.uom = uom
        asset.save()
        
        messages.success(request, f'Perubahan pada aset {old_code} berhasil disimpan.')
        return JsonResponse({'success': True})
    return redirect('asset_list')
@login_required
def asset_delete(request, asset_id):
    asset = get_object_or_404(Asset, id=asset_id)
    if request.method == 'POST':
        asset.delete()
        messages.success(request, "Data aset berhasil dihapus.")
        return redirect('asset_list')
    return redirect('asset_list')

@login_required
def asset_units(request, asset_id):
    asset = get_object_or_404(Asset, id=asset_id)
    units = asset.units.all().order_by('unit_code')
    employees = Employee.objects.all().order_by('name')
    
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
def unit_add(request, asset_id):
    if request.method == 'POST':
        asset = get_object_or_404(Asset, id=asset_id)
        suffix = request.POST.get('unit_code_suffix')
        status = 'tersedia'
        
        if suffix:
            unit_code = f"{asset.asset_code}-{suffix}"
            if AssetUnit.objects.filter(unit_code=unit_code).exists():
                if request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': f'Kode Unit "{unit_code}" sudah terdaftar di sistem!'}, status=400)
            else:
                new_unit = AssetUnit.objects.create(asset=asset, unit_code=unit_code, status=status)
                UnitLog.objects.create(unit=new_unit, action='created', notes="Ditambahkan ke Sistem")
                
                asset.qty = asset.units.count()
                asset.save()
                messages.success(request, "Unit fisik berhasil ditambahkan.")
        
        if request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
            
    return redirect('asset_units', asset_id=asset_id)

@login_required
def unit_edit(request, unit_id):
    unit = get_object_or_404(AssetUnit, id=unit_id)
    old_status = unit.status
    old_assigned = unit.assigned_to

    if request.method == 'POST':
        suffix = request.POST.get('unit_code_suffix')
        new_unit_code = f"{unit.asset.asset_code}-{suffix}" if suffix else unit.unit_code
        
        if AssetUnit.objects.exclude(id=unit.id).filter(unit_code=new_unit_code).exists():
            if request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': f'Kode Unit "{new_unit_code}" sudah digunakan oleh unit lain!'}, status=400)
        
        unit.unit_code = new_unit_code
        new_status = request.POST.get('status')
        unit.status = new_status
        
        if new_status in ['tersedia', 'pensiun']:
            unit.assigned_to = None
            
        unit.save()
        new_assigned = unit.assigned_to

        notes = request.POST.get('notes', '')
        if old_status != new_status or old_assigned != new_assigned:
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

        if request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})

    return redirect('asset_units', asset_id=unit.asset.id)

@login_required
def unit_update_status(request, unit_id):
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
def unit_delete(request, unit_id):
    unit = get_object_or_404(AssetUnit, id=unit_id)
    asset_id = unit.asset.id
    if request.method == 'POST':
        unit.delete()
        asset = Asset.objects.get(id=asset_id)
        asset.qty = asset.units.count()
        asset.save()
        messages.success(request, "Perubahan aset berhasil disimpan.")
    return redirect('asset_units', asset_id=asset_id)

@login_required
def unit_history(request, unit_id):
    import re
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

@login_required
def status_aset_list(request):
    tab = request.GET.get('tab', 'tersedia')
    cat_filter = request.GET.get('cat', 'karyawan')
    search_query = request.GET.get('q', '')
    
    units = AssetUnit.objects.select_related('asset', 'assigned_to', 'asset__category').order_by('-id')
    
    if cat_filter == 'network':
        units = units.filter(asset__category__name__icontains='Network')
    else:
        units = units.filter(asset__category__name__icontains='Karyawan')
        
    counts = {
        'tersedia': units.filter(status='tersedia').count(),
        'digunakan': units.filter(status='digunakan').count(),
        'rusak': units.filter(status='rusak').count(),
    }
    
    if tab == 'tersedia':
        units = units.filter(status='tersedia')
    elif tab == 'digunakan':
        units = units.filter(status='digunakan')
    elif tab == 'rusak':
        units = units.filter(status='rusak')
    else:
        units = units.filter(status='tersedia')
        
    if search_query:
        from django.db.models import Q
        units = units.filter(
            Q(unit_code__icontains=search_query) |
            Q(asset__name__icontains=search_query) |
            Q(assigned_to__name__icontains=search_query) |
            Q(assigned_to__nik__icontains=search_query) |
            Q(area__icontains=search_query) |
            Q(location__icontains=search_query)
        )
        
    return render(request, 'status_aset_list.html', {
        'units': units,
        'tab': tab, 'cat_filter': cat_filter,
        'search_query': search_query,
        'counts': counts,
    })

from django.db.models import Q

@login_required
def distribusi_list(request):
    tab = request.GET.get('tab', 'handover')
    if not tab:
        tab = 'handover'
    search_query = request.GET.get('q', '')
    sort_order = request.GET.get('sort', 'desc')
    
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
            # Check exactly for "07 Oct 2026" or "7 Oct 2026"
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
            day_val = int(day_match.group(1)) if day_match and len(query_lower) <= 2 else None

            if month_val and year_val:
                date_q = Q(assigned_date__month=month_val, assigned_date__year=year_val)
            elif month_val:
                date_q = Q(assigned_date__month=month_val)
            elif year_val:
                date_q = Q(assigned_date__year=year_val)
            elif day_val:
                date_q = Q(assigned_date__day=day_val)

        assignments = assignments.filter(
            Q(unit__unit_code__icontains=search_query) |
            Q(unit__asset__name__icontains=search_query) |
            Q(employee__name__icontains=search_query) |
            Q(employee__nik__icontains=search_query) |
            Q(from_employee__name__icontains=search_query) |
            Q(from_employee__nik__icontains=search_query) |
            date_q
        )
    
    counts = {
        'handover': AssetAssignment.objects.filter(type='handover').count(),
        'mutation': AssetAssignment.objects.filter(type='mutation').count(),
        'return': AssetAssignment.objects.filter(type='return').count(),
    }
    
    available_units = AssetUnit.objects.filter(
        status='tersedia', asset__category__name__icontains='Karyawan'
    ).select_related('asset').order_by('asset__name', 'unit_code')
    
    used_units = AssetUnit.objects.filter(
        status='digunakan', asset__category__name__icontains='Karyawan'
    ).select_related('asset', 'assigned_to').order_by('asset__name', 'unit_code')
    employees = Employee.objects.all().order_by('name')
    
    return render(request, 'distribusi_list.html', {
        'assignments': assignments,
        'tab': tab,
        'search_query': search_query,
        'counts': counts,
        'available_units': available_units,
        'used_units': used_units,
        'employees': employees,
    })

@login_required
@transaction.atomic
def distribusi_handover(request):
    if request.method == 'POST':
        unit_id = request.POST.get('unit')
        employee_id = request.POST.get('employee')
        assigned_date = request.POST.get('assigned_date')
        notes = request.POST.get('notes', '')
        document = request.FILES.get('document')
        
        unit = get_object_or_404(AssetUnit, id=unit_id)
        employee = get_object_or_404(Employee, id=employee_id)

        AssetAssignment.objects.create(
            type='handover',
            unit=unit,
            employee=employee,
            assigned_date=assigned_date,
            notes=notes,
            document=document
        )

        unit.status = 'digunakan'
        unit.assigned_to = employee
        unit.save()

        UnitLog.objects.create(
            unit=unit,
            action='assigned',
            employee=employee,
            notes=f"Diserahkan melalui Distribusi Aset. {notes}"
        )
        messages.success(request, "Serah terima aset berhasil diproses.")
    return redirect('/distribusi/?tab=handover')

@login_required
@transaction.atomic
def distribusi_mutation(request):
    if request.method == 'POST':
        unit_id = request.POST.get('unit')
        new_employee_id = request.POST.get('employee')
        assigned_date = request.POST.get('assigned_date')
        notes = request.POST.get('notes', '')
        document = request.FILES.get('document')
        
        unit = get_object_or_404(AssetUnit, id=unit_id)
        old_employee = unit.assigned_to
        new_employee = get_object_or_404(Employee, id=new_employee_id)

        AssetAssignment.objects.create(
            type='mutation',
            unit=unit,
            from_employee=old_employee,
            employee=new_employee,
            assigned_date=assigned_date,
            notes=notes,
            document=document
        )

        unit.assigned_to = new_employee
        unit.save()

        UnitLog.objects.create(
            unit=unit,
            action='returned',
            employee=old_employee,
            notes=f"Mutasi: Dikembalikan oleh pemegang sebelumnya."
        )
        UnitLog.objects.create(
            unit=unit,
            action='assigned',
            employee=new_employee,
            notes=f"Mutasi: Diserahkan ke pemegang baru. {notes}"
        )
        messages.success(request, "Mutasi aset berhasil diproses.")
    return redirect('/distribusi/?tab=mutation')

@login_required
@transaction.atomic
def distribusi_return(request):
    if request.method == 'POST':
        unit_id = request.POST.get('unit')
        assigned_date = request.POST.get('assigned_date')
        notes = request.POST.get('notes', '')
        document = request.FILES.get('document')
        
        unit = get_object_or_404(AssetUnit, id=unit_id)
        old_employee = unit.assigned_to

        AssetAssignment.objects.create(
            type='return',
            unit=unit,
            from_employee=old_employee,
            employee=old_employee,
            assigned_date=assigned_date,
            notes=notes,
            document=document
        )

        unit.status = 'tersedia'
        unit.assigned_to = None
        unit.save()

        UnitLog.objects.create(
            unit=unit,
            action='returned',
            employee=old_employee,
            notes=f"Dikembalikan oleh karyawan. {notes}"
        )
        messages.success(request, "Pengembalian aset berhasil diproses.")
    return redirect('/distribusi/?tab=return')

@login_required
def distribusi_upload_doc(request, assignment_id):
    if request.method == 'POST':
        assignment = get_object_or_404(AssetAssignment, id=assignment_id)
        if 'document' in request.FILES:
            doc = request.FILES['document']
            import os
            ext = os.path.splitext(doc.name)[1].lower()
            allowed_ext = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
            if ext not in allowed_ext:
                messages.error(request, f'Format file tidak diizinkan. Gunakan: {", ".join(allowed_ext)}')
                return redirect(f"/distribusi/?tab={assignment.type}")
            if doc.size > 5 * 1024 * 1024:
                messages.error(request, 'Ukuran file maksimal 5MB.')
                return redirect(f"/distribusi/?tab={assignment.type}")
            
            assignment.document = doc
            assignment.save()
            messages.success(request, "Dokumen berhasil diunggah.")
        tab = assignment.type
        return redirect(f'/distribusi/?tab={tab}')
    return redirect('/distribusi/')

@login_required
def employee_list(request):
    search_query = request.GET.get('q', '')
    employees = Employee.objects.annotate(
        active_assets=Count('held_units')
    ).order_by('name')
    
    if search_query:
        from django.db.models import Q
        employees = employees.filter(
            Q(name__icontains=search_query) |
            Q(nik__icontains=search_query)
        )
        
    return render(request, 'employee_list.html', {
        'employees': employees,
        'search_query': search_query
    })

@login_required
def employee_detail(request, emp_id):
    employee = get_object_or_404(Employee, id=emp_id)
    units = employee.held_units.select_related('asset').all()
    return render(request, 'employee_detail.html', {
        'employee': employee,
        'units': units
    })

from django.http import JsonResponse

@login_required
def employee_create(request):
    if request.method == 'POST':
        nik = request.POST.get('nik')
        name = request.POST.get('name')
        position = request.POST.get('position', '')
        
        if Employee.objects.filter(nik=nik).exists():
            if request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': f'NIK "{nik}" sudah terdaftar!'}, status=400)
                
        Employee.objects.create(nik=nik, name=name, position=position)
        messages.success(request, "Data karyawan berhasil ditambahkan.")
        
        if request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
            
    return redirect('employee_list')

@login_required
def employee_edit(request, emp_id):
    employee = get_object_or_404(Employee, id=emp_id)
    if request.method == 'POST':
        nik = request.POST.get('nik')
        name = request.POST.get('name')
        position = request.POST.get('position', '')
        
        if Employee.objects.filter(nik=nik).exclude(id=emp_id).exists():
            if request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': f'NIK "{nik}" sudah terdaftar pada karyawan lain!'}, status=400)
                
        employee.nik = nik
        employee.name = name
        employee.position = position
        employee.save()
        messages.success(request, "Perubahan data karyawan berhasil disimpan.")
        
        if request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
            
    return redirect('employee_list')

@login_required
def employee_delete(request, emp_id):
    employee = get_object_or_404(Employee, id=emp_id)
    if request.method == 'POST':
        # Cannot delete if holding assets
        if employee.held_units.count() > 0:
            return redirect('employee_list')
            
        # Preserve employee name in UnitLog notes before deletion
        logs = UnitLog.objects.filter(employee=employee)
        for log in logs:
            prefix = f"{employee.name} ({employee.nik})"
            log.notes = f"{prefix} - {log.notes}" if log.notes else prefix
            log.save()
            
        employee.delete()
        messages.success(request, "Data karyawan berhasil dihapus.")
    return redirect('employee_list')

from PIL import Image, ImageDraw, ImageFont

def unit_qr_code(request, uuid):
    unit = get_object_or_404(AssetUnit, id_uuid=uuid)
    url = request.build_absolute_uri(f'/public/unit/{uuid}/')
    
    qr = qrcode.QRCode(version=1, box_size=12, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    text = f"{unit.asset.name} - {unit.unit_code}"
    
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()

    qr_w, qr_h = qr_img.size
    
    # PIL 9.2.0+ uses getbbox. Fallback to textsize for older versions if needed, but getbbox is standard now.
    try:
        bbox = font.getbbox(text)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except AttributeError:
        text_w, text_h = font.getsize(text)
        
    padding = 20
    new_h = qr_h + text_h + padding * 2
    new_w = max(qr_w, text_w + padding * 2)
    
    img = Image.new('RGB', (new_w, new_h), color='white')
    img.paste(qr_img, ((new_w - qr_w) // 2, padding // 2))
    
    draw = ImageDraw.Draw(img)
    text_x = (new_w - text_w) // 2
    text_y = qr_h + (padding // 2) + 5
    draw.text((text_x, text_y), text, font=font, fill="black")
    
    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    return response

def unit_public_detail(request, uuid):
    unit = get_object_or_404(AssetUnit, id_uuid=uuid)
    logs = UnitLog.objects.filter(unit=unit).order_by('-timestamp')
    
    return render(request, 'unit_public_detail.html', {
        'unit': unit,
        'logs': logs
    })


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


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        from django.contrib.auth.models import User
        u = request.POST.get('username')
        p = request.POST.get('password')
        
        # Allow login using email
        login_username = u
        if '@' in u:
            try:
                user_obj = User.objects.get(email=u)
                login_username = user_obj.username
            except User.DoesNotExist:
                pass
        
        user = authenticate(request, username=login_username, password=p)
        if user is not None:
            login(request, user)
            from django.utils.http import url_has_allowed_host_and_scheme
            next_url = request.GET.get('next', '')
            if not next_url or not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                next_url = 'dashboard'
            return redirect(next_url)
        else:
            messages.error(request, 'Username / Email atau password salah.')
            
    return render(request, 'login.html')

def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('login')

def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)

from django.contrib.auth import update_session_auth_hash
from django.contrib import messages

@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_info':
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            email = request.POST.get('email', '')
            username = request.POST.get('username', '')
            
            if not username:
                messages.error(request, "Username tidak boleh kosong.")
            else:
                try:
                    user.first_name = first_name
                    user.last_name = last_name
                    user.email = email
                    user.username = username
                    user.save()
                    messages.success(request, "Informasi profil berhasil diperbarui.")
                except Exception as e:
                    messages.error(request, "Gagal memperbarui profil. Username mungkin sudah digunakan.")
                    
        elif action == 'update_password':
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not user.check_password(old_password):
                messages.error(request, "Password lama salah.")
            elif new_password != confirm_password:
                messages.error(request, "Konfirmasi password baru tidak cocok.")
            else:
                from django.contrib.auth.password_validation import validate_password
                try:
                    validate_password(new_password, user)
                    user.set_password(new_password)
                    user.save()
                    update_session_auth_hash(request, user)
                    messages.success(request, "Password berhasil diubah.")
                except Exception as e:
                    for error in getattr(e, 'messages', [str(e)]):
                        messages.error(request, error)
                
        return redirect('profile')
        
    return render(request, 'profile.html')


@login_required
def backup_database_view(request):
    """View to handle manual database backup."""
    if not request.user.is_superuser:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Anda tidak memiliki akses ke halaman ini.")
        
    if request.method == 'POST':
        import io
        import datetime
        from django.core.management import call_command
        from django.http import HttpResponse, HttpResponseServerError
        
        backup_format = request.POST.get('format', 'json')
        now = datetime.datetime.now().strftime('%Y-%m-%d_%H%M')
        
        if backup_format == 'sql':
            import subprocess
            import os
            from django.conf import settings
            
            db = settings.DATABASES['default']
            db_name = db['NAME']
            db_user = db['USER']
            db_pass = db['PASSWORD']
            db_host = db['HOST'] or '127.0.0.1'
            db_port = db['PORT'] or '3306'
            
            cmd = ['mysqldump', f'--user={db_user}', f'--host={db_host}', f'--port={db_port}']
            # Don't include password parameter if empty
            if db_pass:
                cmd.append(f'--password={db_pass}')
            cmd.append(db_name)
            
            try:
                # Add mysqldump to PATH if running in Laragon on Windows
                env = os.environ.copy()
                result = subprocess.run(cmd, env=env, capture_output=True, text=False)
                
                if result.returncode != 0:
                    return HttpResponseServerError(f"Gagal melakukan backup SQL. Pastikan 'mysqldump' tersedia di server. Error: {result.stderr.decode('utf-8', errors='ignore')}")
                
                response = HttpResponse(result.stdout, content_type='application/sql')
                response['Content-Disposition'] = f'attachment; filename="backup_manajemen_aset_{now}.sql"'
                return response
            except Exception as e:
                return HttpResponseServerError(f"Terjadi kesalahan saat mengeksekusi mysqldump: {str(e)}")
                
        else:
            # Default JSON
            buffer = io.StringIO()
            # Exclude contenttypes and auth permissions which can cause issues on restore
            call_command('dumpdata', '--exclude', 'contenttypes', '--exclude', 'auth.permission', '--exclude', 'admin.logentry', '--exclude', 'sessions', stdout=buffer)
            buffer.seek(0)
            
            response = HttpResponse(buffer.getvalue(), content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="backup_manajemen_aset_{now}.json"'
            return response
        
    return render(request, 'backup.html')
