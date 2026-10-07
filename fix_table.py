import re

with open('templates/asset_list.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Update Table Headers
c = c.replace(
    '<th class="p-4 font-bold text-center w-16">No</th>\n                    <th class="p-4 font-bold">Nama Aset</th>',
    '<th class="p-4 font-bold text-center w-16">No</th>\n                    <th class="p-4 font-bold w-32">Kode Aset</th>\n                    <th class="p-4 font-bold">Nama Aset</th>'
)

# Update Table Body
c = c.replace(
    '<td class="p-4 text-center text-gray-500">{{ forloop.counter }}</td>\n                    <td class="p-4">',
    '<td class="p-4 text-center text-gray-500">{{ forloop.counter }}</td>\n                    <td class="p-4 font-bold text-gray-600">{{ asset.asset_code }}</td>\n                    <td class="p-4">'
)

# Update empty colspan just in case
c = c.replace('<td colspan="6"', '<td colspan="7"')
c = c.replace('<td colspan="5"', '<td colspan="6"')

with open('templates/asset_list.html', 'w', encoding='utf-8') as f:
    f.write(c)
