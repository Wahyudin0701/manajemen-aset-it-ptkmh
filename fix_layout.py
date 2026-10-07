with open('templates/employee_detail.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix badges
c = c.replace('class="bg-emerald-50', 'class="whitespace-nowrap bg-emerald-50')
c = c.replace('class="bg-amber-50', 'class="whitespace-nowrap bg-amber-50')
# Only replace the badge gray-50, not the Riwayat button yet
c = c.replace('class="bg-gray-50 border border-gray-200 text-gray-600 px-2.5', 'class="whitespace-nowrap bg-gray-50 border border-gray-200 text-gray-600 px-2.5')

# Replace the Aksi column inner div completely
old_aksi = """                    <td class="p-4 text-center">
                        <div class="flex items-center justify-center space-x-2">
                            <a href="{% url 'unit_history' unit.id %}" class="text-xs bg-gray-50 border border-gray-200 text-gray-600 hover:bg-gray-100 px-3 py-1.5 rounded-lg font-bold transition-colors">
                                Riwayat
                            </a>
                            <button type="button" onclick="openStatusModal({{ unit.id }}, '{{ unit.unit_code }}', '{{ unit.status }}')" class="text-xs bg-kerinci-light border border-kerinci/20 text-kerinci hover:bg-kerinci hover:text-white px-3 py-1.5 rounded-lg font-bold transition-colors">
                                Ubah Status
                            </button>
                        </div>
                    </td>"""

new_aksi = """                    <td class="p-4 text-center">
                        <div class="flex items-center justify-center gap-2">
                            <a href="{% url 'unit_history' unit.id %}" class="whitespace-nowrap text-xs bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 px-3 py-2 rounded-lg font-bold transition-colors shadow-sm">
                                Riwayat
                            </a>
                            <button type="button" onclick="openStatusModal({{ unit.id }}, '{{ unit.unit_code }}', '{{ unit.status }}')" class="whitespace-nowrap text-xs bg-white border border-gray-200 text-kerinci hover:bg-gray-50 px-3 py-2 rounded-lg font-bold transition-colors shadow-sm">
                                Ubah Status
                            </button>
                        </div>
                    </td>"""

c = c.replace(old_aksi, new_aksi)

with open('templates/employee_detail.html', 'w', encoding='utf-8') as f:
    f.write(c)
