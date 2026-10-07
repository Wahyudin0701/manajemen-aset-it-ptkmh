import re

with open('assets/models.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = re.sub(r'class MasterAssetCode\(models\.Model\):.*?return self\.code\n\n', '', c, flags=re.DOTALL)

with open('assets/models.py', 'w', encoding='utf-8') as f:
    f.write(c)
