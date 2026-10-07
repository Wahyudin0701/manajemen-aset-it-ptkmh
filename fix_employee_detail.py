import re

with open('templates/employee_detail.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Update Table Headers
c = c.replace(
    '<th class="p-4 font-bold w-32">Kondisi</th>\n                </tr>',
    '<th class="p-4 font-bold w-32">Kondisi</th>\n                    <th class="p-4 font-bold text-center w-40">Aksi</th>\n                </tr>'
)

# Update the condition column and add actions
old_row = '''                    <td class="p-4">
                        <span class="bg-emerald-50 border border-emerald-100 text-emerald-600 px-2.5 py-1 rounded-md text-[10px] font-extrabold uppercase tracking-wider">
                            Sedang Digunakan
                        </span>
                    </td>
                </tr>'''

new_row = '''                    <td class="p-4">
                        {% if unit.status == 'digunakan' %}
                            <span class="bg-emerald-50 border border-emerald-100 text-emerald-600 px-2.5 py-1 rounded-md text-[10px] font-extrabold uppercase tracking-wider">
                                Sedang Digunakan
                            </span>
                        {% elif unit.status == 'rusak' %}
                            <span class="bg-amber-50 border border-amber-100 text-amber-600 px-2.5 py-1 rounded-md text-[10px] font-extrabold uppercase tracking-wider">
                                Diperbaiki
                            </span>
                        {% else %}
                            <span class="bg-gray-50 border border-gray-200 text-gray-600 px-2.5 py-1 rounded-md text-[10px] font-extrabold uppercase tracking-wider">
                                {{ unit.get_status_display }}
                            </span>
                        {% endif %}
                    </td>
                    <td class="p-4 text-center">
                        <div class="flex items-center justify-center space-x-2">
                            <a href="{% url 'unit_history' unit.id %}" class="text-xs bg-gray-50 border border-gray-200 text-gray-600 hover:bg-gray-100 px-3 py-1.5 rounded-lg font-bold transition-colors">
                                Riwayat
                            </a>
                            <button type="button" onclick="openStatusModal({{ unit.id }}, '{{ unit.unit_code }}', '{{ unit.status }}')" class="text-xs bg-kerinci-light border border-kerinci/20 text-kerinci hover:bg-kerinci hover:text-white px-3 py-1.5 rounded-lg font-bold transition-colors">
                                Ubah Status
                            </button>
                        </div>
                    </td>
                </tr>'''

c = c.replace(old_row, new_row)
c = c.replace('<td colspan="4"', '<td colspan="5"')

modal_and_script = '''
<!-- Modal Ubah Status Unit -->
<div id="statusModal" class="fixed inset-0 z-50 hidden flex items-center justify-center">
    <div class="absolute inset-0 bg-gray-900/40 backdrop-blur-sm" onclick="closeStatusModal()"></div>
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md relative z-10 p-6">
        <h3 class="text-xl font-extrabold text-gray-900 mb-4">Ubah Status Aset</h3>
        <p class="text-sm text-gray-600 mb-6">Ubah kondisi/status untuk unit <strong id="sm_unit" class="text-kerinci"></strong> yang sedang dipegang.</p>
        
        <form id="statusForm" method="POST" class="space-y-4">
            {% csrf_token %}
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-1">Status Baru</label>
                <select name="status" id="sm_status_select" required class="w-full px-4 py-2 rounded-xl border border-gray-200 text-sm focus:outline-none focus:border-kerinci focus:ring-1 focus:ring-kerinci bg-white">
                    <option value="digunakan">Sedang Digunakan (Normal/Baik)</option>
                    <option value="rusak">Diperbaiki (Rusak/Maintenance)</option>
                </select>
                <p class="text-xs text-amber-600 mt-2 font-bold">* Jika ingin mengembalikan aset (Tersedia), silakan gunakan menu Serah Terima BAST.</p>
            </div>
            
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-1">Catatan</label>
                <textarea name="notes" rows="2" class="w-full px-4 py-2 rounded-xl border border-gray-200 text-sm focus:outline-none focus:border-kerinci focus:ring-1 focus:ring-kerinci bg-white" placeholder="Contoh: Layar bergaris, sedang dibawa ke service center..."></textarea>
            </div>
            
            <div class="flex justify-end space-x-3 pt-4 border-t border-gray-100 mt-6">
                <button type="button" onclick="closeStatusModal()" class="px-5 py-2.5 border border-gray-300 text-gray-700 font-bold rounded-xl text-sm hover:bg-gray-50 transition-colors">Batal</button>
                <button type="submit" class="px-5 py-2.5 bg-kerinci text-white font-bold rounded-xl text-sm shadow-sm hover:bg-kerinci/90 transition-colors">Simpan Perubahan</button>
            </div>
        </form>
    </div>
</div>

<script>
    function openStatusModal(id, unitCode, currentStatus) {
        document.getElementById('statusModal').classList.remove('hidden');
        document.getElementById('sm_unit').textContent = unitCode;
        document.getElementById('statusForm').action = '/unit/' + id + '/status/';
        document.getElementById('sm_status_select').value = currentStatus;
    }

    function closeStatusModal() {
        document.getElementById('statusModal').classList.add('hidden');
    }
</script>
{% endblock %}
'''

c = c.replace('{% endblock %}', modal_and_script)

with open('templates/employee_detail.html', 'w', encoding='utf-8') as f:
    f.write(c)
