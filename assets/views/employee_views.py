from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.core.paginator import Paginator
from assets.models import Employee, UnitLog
from assets.permissions import operator_required


@login_required
def employee_list(request):
    """Menampilkan daftar karyawan dengan jumlah unit aset yang sedang dipegang dan dukungan pagination & soft delete."""
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', 'aktif')

    base_qs = Employee.objects.annotate(
        active_assets=Count('held_units')
    ).order_by('name')

    count_active = Employee.objects.filter(is_active=True).count()
    count_inactive = Employee.objects.filter(is_active=False).count()
    count_all = count_active + count_inactive

    if status_filter == 'aktif':
        employees_qs = base_qs.filter(is_active=True)
    elif status_filter == 'nonaktif':
        employees_qs = base_qs.filter(is_active=False)
    else:
        employees_qs = base_qs

    if search_query:
        employees_qs = employees_qs.filter(
            Q(name__icontains=search_query) |
            Q(nik__icontains=search_query)
        )

    paginator = Paginator(employees_qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'employee_list.html', {
        'employees': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'count_active': count_active,
        'count_inactive': count_inactive,
        'count_all': count_all,
    })


@login_required
def employee_detail(request, emp_id):
    """Menampilkan rincian profil karyawan dan unit aset spesifik yang sedang dipinjam."""
    employee = get_object_or_404(Employee, id=emp_id)
    units = employee.held_units.select_related('asset').all()
    return render(request, 'employee_detail.html', {
        'employee': employee,
        'units': units
    })


@login_required
@operator_required
def employee_create(request):
    """Menambahkan data karyawan baru."""
    if request.method == 'POST':
        nik = request.POST.get('nik', '').strip()
        name = request.POST.get('name', '').strip()
        position = request.POST.get('position', '').strip()

        if Employee.objects.filter(nik=nik).exists():
            if request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': f'NIK "{nik}" sudah terdaftar!'}, status=400)
            messages.error(request, f'NIK "{nik}" sudah terdaftar!')
            return redirect('employee_list')

        Employee.objects.create(nik=nik, name=name, position=position, is_active=True)
        messages.success(request, "Data karyawan berhasil ditambahkan.")

        if request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})

    return redirect('employee_list')


@login_required
@operator_required
def employee_edit(request, emp_id):
    """Memperbarui informasi data karyawan."""
    employee = get_object_or_404(Employee, id=emp_id)
    if request.method == 'POST':
        nik = request.POST.get('nik', '').strip()
        name = request.POST.get('name', '').strip()
        position = request.POST.get('position', '').strip()

        if Employee.objects.filter(nik=nik).exclude(id=emp_id).exists():
            if request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': f'NIK "{nik}" sudah terdaftar pada karyawan lain!'}, status=400)
            messages.error(request, f'NIK "{nik}" sudah terdaftar pada karyawan lain!')
            return redirect('employee_list')

        employee.nik = nik
        employee.name = name
        employee.position = position
        employee.save()
        messages.success(request, "Perubahan data karyawan berhasil disimpan.")

        if request.headers.get('Accept') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})

    return redirect('employee_list')


@login_required
@operator_required
def employee_delete(request, emp_id):
    """Menonaktifkan data karyawan (soft delete) untuk menjaga integritas riwayat transaksi."""
    employee = get_object_or_404(Employee, id=emp_id)
    if request.method == 'POST':
        # Larang penonaktifan jika karyawan masih memegang unit aktif
        if employee.held_units.count() > 0:
            messages.error(request, "Karyawan tidak dapat dinonaktifkan karena masih memegang unit aset.")
            return redirect('employee_list')

        # Soft delete: tandai is_active = False tanpa menghapus baris riwayat di database
        employee.is_active = False
        employee.save()
        messages.success(request, f"Data karyawan {employee.name} berhasil dinonaktifkan.")
    return redirect('employee_list')


@login_required
@operator_required
def employee_activate(request, emp_id):
    """Mengaktifkan kembali data karyawan yang sebelumnya dinonaktifkan."""
    employee = get_object_or_404(Employee, id=emp_id)
    if request.method == 'POST':
        employee.is_active = True
        employee.save()
        messages.success(request, f"Data karyawan {employee.name} berhasil diaktifkan kembali.")
    return redirect('employee_list')
