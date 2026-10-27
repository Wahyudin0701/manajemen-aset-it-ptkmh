from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from assets.models import AssetUnit


@login_required
def status_aset_list(request):
    """Menampilkan pemantauan status seluruh unit fisik dengan paginasi dan filter kategori/status."""
    tab = request.GET.get('tab', 'tersedia')
    cat_filter = request.GET.get('cat', 'karyawan')
    search_query = request.GET.get('q', '').strip()

    units_qs = AssetUnit.objects.select_related('asset', 'assigned_to', 'asset__category').order_by('-id')

    if cat_filter == 'network':
        units_qs = units_qs.filter(asset__category__name__icontains='Network')
    else:
        units_qs = units_qs.filter(asset__category__name__icontains='Karyawan')

    counts = {
        'tersedia': units_qs.filter(status='tersedia').count(),
        'digunakan': units_qs.filter(status='digunakan').count(),
        'rusak': units_qs.filter(status='rusak').count(),
    }

    if tab == 'tersedia':
        units_qs = units_qs.filter(status='tersedia')
    elif tab == 'digunakan':
        units_qs = units_qs.filter(status='digunakan')
    elif tab == 'rusak':
        units_qs = units_qs.filter(status='rusak')
    else:
        units_qs = units_qs.filter(status='tersedia')

    if search_query:
        units_qs = units_qs.filter(
            Q(unit_code__icontains=search_query) |
            Q(serial_number__icontains=search_query) |
            Q(asset__name__icontains=search_query) |
            Q(assigned_to__name__icontains=search_query) |
            Q(assigned_to__nik__icontains=search_query) |
            Q(area__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    # Implementasi Pagination (25 unit per halaman)
    paginator = Paginator(units_qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'status_aset_list.html', {
        'units': page_obj,
        'page_obj': page_obj,
        'tab': tab,
        'cat_filter': cat_filter,
        'search_query': search_query,
        'counts': counts,
    })
