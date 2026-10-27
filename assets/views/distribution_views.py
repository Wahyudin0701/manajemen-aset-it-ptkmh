import os
import datetime
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator
from assets.models import AssetAssignment, AssetUnit, Employee, UnitLog
from assets.permissions import operator_required


def validate_uploaded_document(doc):
    """Memvalidasi format dan batas ukuran berkas BAST yang diunggah."""
    ext = os.path.splitext(doc.name)[1].lower()
    allowed_ext = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
    if ext not in allowed_ext:
        return False, f'Format file tidak diizinkan. Gunakan: {", ".join(allowed_ext)}'
    if doc.size > 5 * 1024 * 1024:
        return False, 'Ukuran file maksimal 5MB.'
    return True, None


@login_required
def distribusi_list(request):
    """Menampilkan daftar riwayat transaksi serah terima, mutasi, dan pengembalian dengan paginasi."""
    tab = request.GET.get('tab', 'handover')
    if not tab:
        tab = 'handover'
    search_query = request.GET.get('q', '').strip()
    sort_order = request.GET.get('sort', 'desc')

    assignments_qs = AssetAssignment.objects.filter(type=tab).select_related(
        'unit', 'unit__asset', 'employee', 'from_employee'
    )

    if sort_order == 'asc':
        assignments_qs = assignments_qs.order_by('assigned_date', 'id')
    else:
        assignments_qs = assignments_qs.order_by('-assigned_date', '-id')

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

            year_match = re.search(r' (20\d{2}) ', query_lower)
            year_val = int(year_match.group(1)) if year_match else None

            day_match = re.search(r' (0?[1-9]|[12]\d|3[01]) ', query_lower)
            day_val = int(day_match.group(1)) if day_match and len(query_lower) <= 2 else None

            if month_val and year_val:
                date_q = Q(assigned_date__month=month_val, assigned_date__year=year_val)
            elif month_val:
                date_q = Q(assigned_date__month=month_val)
            elif year_val:
                date_q = Q(assigned_date__year=year_val)
            elif day_val:
                date_q = Q(assigned_date__day=day_val)

        assignments_qs = assignments_qs.filter(
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
    # Ambil data karyawan aktif untuk pilihan form handover & mutation
    employees = Employee.objects.filter(is_active=True).order_by('name')

    # Implementasi Pagination (25 baris per halaman)
    paginator = Paginator(assignments_qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'distribusi_list.html', {
        'assignments': page_obj,
        'page_obj': page_obj,
        'tab': tab,
        'search_query': search_query,
        'counts': counts,
        'available_units': available_units,
        'used_units': used_units,
        'employees': employees,
    })


@login_required
@operator_required
@transaction.atomic
def distribusi_handover(request):
    """Memproses transaksi serah terima aset dari gudang ke karyawan."""
    if request.method == 'POST':
        unit_id = request.POST.get('unit')
        employee_id = request.POST.get('employee')
        assigned_date = request.POST.get('assigned_date')
        notes = request.POST.get('notes', '')
        document = request.FILES.get('document')

        if document:
            is_valid, err_msg = validate_uploaded_document(document)
            if not is_valid:
                messages.error(request, err_msg)
                return redirect('/distribusi/?tab=handover')

        unit = get_object_or_404(AssetUnit, id=unit_id)
        employee = get_object_or_404(Employee, id=employee_id)

        AssetAssignment.objects.create(
            type='handover',
            unit=unit,
            employee=employee,
            assigned_date=assigned_date,
            status='aktif',
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
            notes=f"Diserahkan melalui Distribusi Aset. {notes}".strip()
        )
        messages.success(request, "Serah terima aset berhasil diproses.")
    return redirect('/distribusi/?tab=handover')


@login_required
@operator_required
@transaction.atomic
def distribusi_mutation(request):
    """Memproses transaksi mutasi aset antar karyawan."""
    if request.method == 'POST':
        unit_id = request.POST.get('unit')
        new_employee_id = request.POST.get('employee')
        assigned_date = request.POST.get('assigned_date')
        notes = request.POST.get('notes', '')
        document = request.FILES.get('document')

        if document:
            is_valid, err_msg = validate_uploaded_document(document)
            if not is_valid:
                messages.error(request, err_msg)
                return redirect('/distribusi/?tab=mutation')

        unit = get_object_or_404(AssetUnit, id=unit_id)
        old_employee = unit.assigned_to
        new_employee = get_object_or_404(Employee, id=new_employee_id)

        # Update assignment aktif sebelumnya jika ada
        AssetAssignment.objects.filter(unit=unit, status='aktif').update(
            status='dikembalikan',
            returned_date=assigned_date
        )

        AssetAssignment.objects.create(
            type='mutation',
            unit=unit,
            from_employee=old_employee,
            employee=new_employee,
            assigned_date=assigned_date,
            status='aktif',
            notes=notes,
            document=document
        )

        unit.assigned_to = new_employee
        unit.save()

        UnitLog.objects.create(
            unit=unit,
            action='returned',
            employee=old_employee,
            notes="Mutasi: Dikembalikan oleh pemegang sebelumnya."
        )
        UnitLog.objects.create(
            unit=unit,
            action='assigned',
            employee=new_employee,
            notes=f"Mutasi: Diserahkan ke pemegang baru. {notes}".strip()
        )
        messages.success(request, "Mutasi aset berhasil diproses.")
    return redirect('/distribusi/?tab=mutation')


@login_required
@operator_required
@transaction.atomic
def distribusi_return(request):
    """Memproses transaksi pengembalian aset dari karyawan kembali ke gudang."""
    if request.method == 'POST':
        unit_id = request.POST.get('unit')
        assigned_date = request.POST.get('assigned_date')
        notes = request.POST.get('notes', '')
        document = request.FILES.get('document')

        if document:
            is_valid, err_msg = validate_uploaded_document(document)
            if not is_valid:
                messages.error(request, err_msg)
                return redirect('/distribusi/?tab=return')

        unit = get_object_or_404(AssetUnit, id=unit_id)
        old_employee = unit.assigned_to

        # Tutup assignment aktif sebelumnya untuk unit ini
        AssetAssignment.objects.filter(unit=unit, status='aktif').update(
            status='dikembalikan',
            returned_date=assigned_date
        )

        AssetAssignment.objects.create(
            type='return',
            unit=unit,
            from_employee=old_employee,
            employee=old_employee,
            assigned_date=assigned_date,
            returned_date=assigned_date,
            status='dikembalikan',
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
            notes=f"Dikembalikan oleh karyawan. {notes}".strip()
        )
        messages.success(request, "Pengembalian aset berhasil diproses.")
    return redirect('/distribusi/?tab=return')


@login_required
@operator_required
def distribusi_upload_doc(request, assignment_id):
    """Menangani pengunggahan berkas susulan dokumen BAST pada transaksi distribusi."""
    if request.method == 'POST':
        assignment = get_object_or_404(AssetAssignment, id=assignment_id)
        if 'document' in request.FILES:
            doc = request.FILES['document']
            is_valid, err_msg = validate_uploaded_document(doc)
            if not is_valid:
                messages.error(request, err_msg)
                return redirect(f"/distribusi/?tab={assignment.type}")

            assignment.document = doc
            assignment.save()
            messages.success(request, "Dokumen berhasil diunggah.")
        tab = assignment.type
        return redirect(f'/distribusi/?tab={tab}')
    return redirect('/distribusi/')
