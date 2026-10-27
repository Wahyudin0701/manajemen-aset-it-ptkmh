from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme


def login_view(request):
    """Menangani autentikasi login via username atau email."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '')

        # Izinkan login menggunakan email
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
            next_url = request.GET.get('next', '')
            if not next_url or not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                next_url = 'dashboard'
            return redirect(next_url)
        else:
            messages.error(request, 'Username / Email atau password salah.')

    return render(request, 'login.html')


def logout_view(request):
    """Mengakhiri sesi pengguna."""
    if request.method == 'POST':
        logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    """Mengelola pembaruan data profil akun dan perubahan kata sandi."""
    user = request.user
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_info':
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            email = request.POST.get('email', '')
            username = request.POST.get('username', '').strip()

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
                except Exception:
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
