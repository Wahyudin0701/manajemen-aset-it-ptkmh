import re

with open('assets/views.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(', MasterAssetCode', '')
c = re.sub(r'def asset_codes\(request\):.*?return redirect\(\'asset_codes\'\)\n', '', c, flags=re.DOTALL)
c = c.replace("codes = MasterAssetCode.objects.all().order_by('code')\n    ", "")
c = c.replace(", 'codes': codes", "")

with open('assets/views.py', 'w', encoding='utf-8') as f:
    f.write(c)
