import re

with open('assets/views.py', 'r', encoding='utf-8') as f:
    c = f.read()

# remove the leftover asset_codes and asset_code_delete completely
c = re.sub(r'    \n    return render\(request, \'asset_codes\.html\'.*?return redirect\(\'asset_codes\'\)\n\n', '', c, flags=re.DOTALL)

with open('assets/views.py', 'w', encoding='utf-8') as f:
    f.write(c)
