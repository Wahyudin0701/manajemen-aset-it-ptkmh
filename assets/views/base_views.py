from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from assets.models import AssetUnit, AssetAssignment


@login_required
def dashboard(request):
    """Menampilkan ringkasan statistik aset dan aktivitas distribusi terbaru."""
    count_karyawan = AssetUnit.objects.filter(asset__category__name__icontains='Karyawan').count()
    count_network = AssetUnit.objects.filter(asset__category__name__icontains='Network').count()

    count_tersedia = AssetUnit.objects.filter(status='tersedia').count()
    count_digunakan = AssetUnit.objects.filter(status='digunakan').count()
    count_maintenance = AssetUnit.objects.filter(status='rusak').count()

    recent_handovers = AssetAssignment.objects.filter(type='handover').select_related(
        'unit', 'unit__asset', 'employee'
    ).order_by('-assigned_date', '-id')[:5]

    recent_mutations = AssetAssignment.objects.filter(type='mutation').select_related(
        'unit', 'unit__asset', 'employee', 'from_employee'
    ).order_by('-assigned_date', '-id')[:3]

    recent_returns = AssetAssignment.objects.filter(type='return').select_related(
        'unit', 'unit__asset', 'employee'
    ).order_by('-assigned_date', '-id')[:3]

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


def custom_404_view(request, exception=None):
    """Handler halaman error 404 kustom."""
    return render(request, '404.html', status=404)
