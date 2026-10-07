import re

with open('templates/asset_units.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace the edit status select and employee div
old_edit_html = '''            <div>
                <label class="block text-sm font-bold text-gray-700 mb-1">Status</label>
                <select id="eu_status" name="status" onchange="toggleEmployeeSelect()" class="w-full px-4 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:border-kerinci focus:ring-1 focus:ring-kerinci bg-gray-50">
                    <option value="tersedia">Tersedia</option>
                    {% if 'Karyawan' in asset.category.name %}
                    <option value="digunakan">Digunakan</option>
                    {% endif %}
                    <option value="rusak">Rusak / Maintenance</option>
                    <option value="pensiun">Dipensiunkan</option>
                </select>
            </div>
            <div id="eu_employee_div" class="hidden">
                <label class="block text-sm font-bold text-gray-700 mb-1">Dipegang Oleh <span class="text-red-500">*</label>
                <select id="eu_assigned_to" name="assigned_to" class="w-full px-4 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:border-kerinci focus:ring-1 focus:ring-kerinci bg-gray-50">
                    <option value="">-- Pilih Karyawan --</option>
                    {% for emp in employees %}
                        <option value="{{ emp.id }}">{{ emp.nik }} - {{ emp.name }}</option>
                    {% endfor %}
                </select>
            </div>'''

new_edit_html = '''            <div>
                <label class="block text-sm font-bold text-gray-700 mb-1">Status</label>
                <select id="eu_status" name="status" class="w-full px-4 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:border-kerinci focus:ring-1 focus:ring-kerinci bg-gray-50">
                    <option value="tersedia" id="opt_tersedia">Tersedia</option>
                    <option value="digunakan" id="opt_digunakan" class="hidden" disabled>Digunakan</option>
                    <option value="rusak">Diperbaiki (Rusak / Maintenance)</option>
                    <option value="pensiun">Dipensiunkan</option>
                </select>
                <p id="eu_bast_warning" class="text-xs text-amber-600 mt-1 hidden font-bold">* Aset sedang digunakan. Pengembalian atau Mutasi harus melalui menu Serah Terima BAST.</p>
            </div>
            <!-- Employee div is completely removed because direct assignment is disabled -->'''

c = c.replace(old_edit_html, new_edit_html)

# Now remove the onchange for add unit as well if it existed? Wait, Add unit has it too? Let's check:
# Actually Add Unit had 'digunakan' too?
old_add_html = '''                <select id="au_status" name="status" onchange="toggleEmployeeSelectAdd()" class="w-full px-4 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:border-kerinci focus:ring-1 focus:ring-kerinci bg-gray-50">
                    <option value="tersedia">Tersedia</option>
                    {% if 'Karyawan' in asset.category.name %}
                    <option value="digunakan">Digunakan</option>
                    {% endif %}
                    <option value="rusak">Rusak / Maintenance</option>
                    <option value="pensiun">Dipensiunkan</option>
                </select>'''
new_add_html = '''                <select id="au_status" name="status" class="w-full px-4 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:border-kerinci focus:ring-1 focus:ring-kerinci bg-gray-50">
                    <option value="tersedia">Tersedia</option>
                    <option value="rusak">Diperbaiki (Rusak / Maintenance)</option>
                    <option value="pensiun">Dipensiunkan</option>
                </select>'''
c = c.replace(old_add_html, new_add_html)

# Let's remove the au_employee_div if it exists.
c = re.sub(r'<div id="au_employee_div".*?</div>', '', c, flags=re.DOTALL|re.IGNORECASE)

# Update the toggleEmployeeSelect JS functions.
# Replace openEditUnitModal completely.
old_js = '''    function openEditUnitModal(id, fullCode, label, status, assignedTo) {
        // Ekstraksi suffix (pisahkan kode induk)
        const prefix = "{{ asset.asset_code }}-";
        let suffix = fullCode;
        if (fullCode.startsWith(prefix)) {
            suffix = fullCode.substring(prefix.length);
        }
        document.getElementById('eu_error').classList.add('hidden');
        document.getElementById('editUnitForm').action = '/unit/' + id + '/edit/';
        document.getElementById('eu_code_suffix').value = suffix;
        document.getElementById('eu_label').value = label;
        document.getElementById('eu_status').value = status;
        document.getElementById('eu_assigned_to').value = assignedTo || '';
        toggleEmployeeSelect();
        document.getElementById('editUnitModal').classList.remove('hidden');
    }'''

new_js = '''    function openEditUnitModal(id, fullCode, label, status, assignedTo) {
        const prefix = "{{ asset.asset_code }}-";
        let suffix = fullCode;
        if (fullCode.startsWith(prefix)) {
            suffix = fullCode.substring(prefix.length);
        }
        document.getElementById('eu_error').classList.add('hidden');
        document.getElementById('editUnitForm').action = '/unit/' + id + '/edit/';
        document.getElementById('eu_code_suffix').value = suffix;
        document.getElementById('eu_label').value = label;
        
        // Handle dropdown lock
        const statSelect = document.getElementById('eu_status');
        const optTersedia = document.getElementById('opt_tersedia');
        const optDigunakan = document.getElementById('opt_digunakan');
        const warnText = document.getElementById('eu_bast_warning');
        
        if (status === 'digunakan') {
            optDigunakan.disabled = false;
            optDigunakan.classList.remove('hidden');
            optTersedia.disabled = true;
            optTersedia.classList.add('hidden');
            warnText.classList.remove('hidden');
            statSelect.value = 'digunakan';
        } else {
            optDigunakan.disabled = true;
            optDigunakan.classList.add('hidden');
            optTersedia.disabled = false;
            optTersedia.classList.remove('hidden');
            warnText.classList.add('hidden');
            statSelect.value = status;
        }

        document.getElementById('editUnitModal').classList.remove('hidden');
    }'''
c = c.replace(old_js, new_js)

with open('templates/asset_units.html', 'w', encoding='utf-8') as f:
    f.write(c)
