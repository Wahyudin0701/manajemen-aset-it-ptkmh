from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Q
from django.http import JsonResponse
from .models import Asset, AssetUnit, UnitLog, Category, Employee, AssetAssignment

def dashboard(request):
    return render(request, 'dashboard.html')

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
        
    if active_tab == 'networking':
        assets = assets.filter(category__name__icontains='Networking')
    else:
        assets = assets.filter(category__name__icontains='Karyawan')

    assets = assets.order_by('asset_code')
    
    return render(request, 'asset_list.html', {
        'assets': assets,
        'search_query': search_query,
        'active_tab': active_tab
    })

def asset_add(request):
    categories = Category.objects.all()
    context = {'categories': categories}
    
    if request.method == 'POST':
        category_id = request.POST.get('category')
        asset_code = request.POST.get('asset_code')
        name = request.POST.get('name')
        brand = request.POST.get('brand')
        uom = request.POST.get('uom')
        
        if Asset.objects.filter(asset_code=asset_code).exists():
            context['error'] = f"Kode Aset '{asset_code}' sudah digunakan. Silakan pilih kode lain."
            context['old_data'] = {
                'category_id': int(category_id) if category_id else '',
                'asset_code': asset_code,
                'name': name,
                'brand': brand,
                'uom': uom
            }
            return render(request, 'asset_add.html', context)
        
        Asset.objects.create(
            category_id=category_id,
            asset_code=asset_code,
            name=name,
            brand=brand,
            qty=0,
            uom=uom,
            price=0,
            total_price=0,
            notes=''
        )
        return redirect('asset_list')
        
    return render(request, 'asset_add.html', context)

def asset_edit(request, asset_id):
    asset = get_object_or_404(Asset, id=asset_id)
    categories = Category.objects.all()
    context = {'asset': asset, 'categories': categories}
    
    if request.method == 'POST':
        category_id = request.POST.get('category')
        new_code = request.POST.get('asset_code')
        name = request.POST.get('name')
        brand = request.POST.get('brand')
        uom = request.POST.get('uom')
        
        old_code = asset.asset_code
        
        if new_code:
            if Asset.objects.exclude(id=asset.id).filter(asset_code=new_code).exists():
                context['error'] = f"Kode Aset '{new_code}' sudah digunakan oleh aset lain."
                asset.category_id = int(category_id) if category_id else None
                asset.asset_code = new_code
                asset.name = name
                asset.brand = brand
                asset.uom = uom
                return render(request, 'asset_edit.html', context)
            asset.asset_code = new_code
            
        asset.category_id = category_id
        asset.name = name
        asset.brand = brand
        asset.uom = uom
        
        asset.save()
        
        # Update unit_code for all related units if asset_code changed
        if new_code and old_code != new_code:
            for unit in asset.units.all():
                if unit.unit_code.startswith(f"{old_code}-"):
                    suffix = unit.unit_code[len(old_code)+1:]
                    unit.unit_code = f"{new_code}-{suffix}"
                    unit.save()
                    
        return redirect('asset_list')
        
    return render(request, 'asset_edit.html', context)

def asset_delete(request, asset_id):
    asset = get_object_or_404(Asset, id=asset_id)
    if request.method == 'POST':
        asset.delete()
        return redirect('asset_list')
    return redirect('asset_list')

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
        
        if request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
            
    return redirect('asset_units', asset_id=asset_id)

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

def unit_update_status(request, unit_id):
    if request.method == 'POST':
        unit = get_object_or_404(AssetUnit, id=unit_id)
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        old_status = unit.status

        if new_status and new_status != old_status:
            unit.status = new_status
            unit.save()
            
            action_type = 'updated'
            if new_status == 'rusak':
                action_type = 'maintenance_in'
            elif old_status == 'rusak' and (new_status == 'digunakan' or new_status == 'tersedia'):
                action_type = 'maintenance_out'
                
            UnitLog.objects.create(
                unit=unit,
                action=action_type,
                employee=unit.assigned_to,
                notes=f"Status diubah dari '{old_status}' menjadi '{new_status}'. {notes}"
            )
            
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

def unit_delete(request, unit_id):
    unit = get_object_or_404(AssetUnit, id=unit_id)
    asset_id = unit.asset.id
    if request.method == 'POST':
        unit.delete()
        asset = Asset.objects.get(id=asset_id)
        asset.qty = asset.units.count()
        asset.save()
    return redirect('asset_units', asset_id=asset_id)

def unit_history(request, unit_id):
    unit = get_object_or_404(AssetUnit, id=unit_id)
    logs = unit.logs.all().select_related('employee')
    return render(request, 'unit_history.html', {'unit': unit, 'logs': logs})

def status_aset_list(request):
    tab = request.GET.get('tab', 'tersedia')
    search_query = request.GET.get('q', '')
    
    units = AssetUnit.objects.select_related('asset', 'assigned_to').order_by('-id')
    
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
            Q(assigned_to__name__icontains=search_query)
        )
        
    return render(request, 'status_aset_list.html', {
        'units': units,
        'tab': tab,
        'search_query': search_query,
        'counts': counts,
    })

from django.db.models import Q

def distribusi_list(request):
    tab = request.GET.get('tab', 'handover')
    search_query = request.GET.get('q', '')
    
    assignments = AssetAssignment.objects.filter(type=tab).select_related(
        'unit', 'unit__asset', 'employee', 'from_employee'
    ).order_by('-assigned_date')
    
    if search_query:
        assignments = assignments.filter(
            Q(unit__unit_code__icontains=search_query) |
            Q(unit__asset__name__icontains=search_query) |
            Q(employee__name__icontains=search_query) |
            Q(from_employee__name__icontains=search_query)
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
    return redirect('/distribusi/?tab=handover')

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
    return redirect('/distribusi/?tab=mutation')

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
    return redirect('/distribusi/?tab=return')

def distribusi_upload_doc(request, assignment_id):
    if request.method == 'POST':
        assignment = get_object_or_404(AssetAssignment, id=assignment_id)
        if 'document' in request.FILES:
            assignment.document = request.FILES['document']
            assignment.save()
        tab = assignment.type
        return redirect(f'/distribusi/?tab={tab}')
    return redirect('/distribusi/')

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

def employee_detail(request, emp_id):
    employee = get_object_or_404(Employee, id=emp_id)
    units = employee.held_units.select_related('asset').all()
    return render(request, 'employee_detail.html', {
        'employee': employee,
        'units': units
    })

def employee_create(request):
    if request.method == 'POST':
        nik = request.POST.get('nik')
        name = request.POST.get('name')
        Employee.objects.create(nik=nik, name=name)
    return redirect('employee_list')

def employee_edit(request, emp_id):
    employee = get_object_or_404(Employee, id=emp_id)
    if request.method == 'POST':
        employee.nik = request.POST.get('nik')
        employee.name = request.POST.get('name')
        employee.save()
    return redirect('employee_list')

def employee_delete(request, emp_id):
    employee = get_object_or_404(Employee, id=emp_id)
    if request.method == 'POST':
        # Cannot delete if holding assets
        if employee.held_units.count() > 0:
            return redirect('employee_list')
            
        # Preserve employee name in UnitLog notes before deletion
        logs = UnitLog.objects.filter(employee=employee)
        for log in logs:
            prefix = f"[Data Dihapus] {employee.name} ({employee.nik})"
            log.notes = f"{prefix} - {log.notes}" if log.notes else prefix
            log.save()
            
        employee.delete()
    return redirect('employee_list')
