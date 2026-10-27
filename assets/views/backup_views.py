import io
import datetime
import os
import subprocess
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from assets.permissions import admin_required
from django.core.management import call_command
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden
from django.conf import settings


@login_required
@admin_required
def backup_database_view(request):
    """Menangani pencadangan database manual ke format JSON atau SQL."""
    if not request.user.is_superuser:
        return HttpResponseForbidden("Anda tidak memiliki akses ke halaman ini.")

    if request.method == 'POST':
        backup_format = request.POST.get('format', 'json')
        now = datetime.datetime.now().strftime('%Y-%m-%d_%H%M')

        if backup_format == 'sql':
            db = settings.DATABASES['default']
            db_engine = db.get('ENGINE', '')

            # Jika database adalah sqlite, lakukan copy database file langsung
            if 'sqlite' in db_engine:
                sqlite_path = db.get('NAME')
                if os.path.exists(sqlite_path):
                    with open(sqlite_path, 'rb') as f:
                        response = HttpResponse(f.read(), content_type='application/x-sqlite3')
                        response['Content-Disposition'] = f'attachment; filename="backup_manajemen_aset_{now}.sqlite3"'
                        return response
                return HttpResponseServerError("File database SQLite tidak ditemukan.")

            db_name = db['NAME']
            db_user = db['USER']
            db_pass = db['PASSWORD']
            db_host = db['HOST'] or '127.0.0.1'
            db_port = db['PORT'] or '3306'

            cmd = ['mysqldump', f'--user={db_user}', f'--host={db_host}', f'--port={db_port}', db_name]

            try:
                env = os.environ.copy()
                if db_pass:
                    env['MYSQL_PWD'] = db_pass
                result = subprocess.run(cmd, env=env, capture_output=True, text=False)

                if result.returncode != 0:
                    return HttpResponseServerError(
                        f"Gagal melakukan backup SQL. Pastikan 'mysqldump' tersedia di server. Error: {result.stderr.decode('utf-8', errors='ignore')}"
                    )

                response = HttpResponse(result.stdout, content_type='application/sql')
                response['Content-Disposition'] = f'attachment; filename="backup_manajemen_aset_{now}.sql"'
                return response
            except Exception as e:
                return HttpResponseServerError(f"Terjadi kesalahan saat mengeksekusi mysqldump: {str(e)}")

        else:
            # Default format JSON menggunakan dumpdata
            buffer = io.StringIO()
            call_command(
                'dumpdata',
                '--exclude', 'contenttypes',
                '--exclude', 'auth.permission',
                '--exclude', 'admin.logentry',
                '--exclude', 'sessions',
                stdout=buffer
            )
            buffer.seek(0)

            response = HttpResponse(buffer.getvalue(), content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="backup_manajemen_aset_{now}.json"'
            return response

    return render(request, 'backup.html')
