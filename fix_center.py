with open('templates/employee_detail.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix header
c = c.replace('<th class="p-4 font-bold w-32">Kondisi</th>', '<th class="p-4 font-bold text-center w-32">Kondisi</th>')

# Fix cell
old_td = '''                    <td class="p-4">
                        {% if unit.status == 'digunakan' %}'''

new_td = '''                    <td class="p-4 text-center">
                        {% if unit.status == 'digunakan' %}'''

c = c.replace(old_td, new_td)

with open('templates/employee_detail.html', 'w', encoding='utf-8') as f:
    f.write(c)
