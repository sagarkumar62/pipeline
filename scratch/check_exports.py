import json
import csv

with open('data/exports/tools.json', 'r', encoding='utf-8') as f:
    tj = json.load(f)

with open('data/exports/tools.jsonl', 'r', encoding='utf-8') as f:
    tjl = [json.loads(l) for l in f if l.strip()]

with open('data/exports/tools.csv', 'r', encoding='utf-8') as f:
    tcsv = list(csv.DictReader(f))

print('Length check:', len(tj), len(tjl), len(tcsv))

mismatches = 0
for r1, r2, r3 in zip(tj, tjl, tcsv):
    id_match = (r1['id'] == r2['id'] == r3['id'])
    name_match = (r1['name'] == r2['name'] == r3['name'])
    desc_match = (r1['description'] == r2['description'] == r3['description'])
    
    u1 = r1.get('official_url')
    u2 = r2.get('official_url')
    u3 = r3.get('official_url') or None
    url_match = (u1 == u2 == u3)
    
    l1 = r1.get('logo_url')
    l2 = r2.get('logo_url')
    l3 = r3.get('logo_url') or None
    logo_match = (l1 == l2 == l3)
    
    if not (id_match and name_match and desc_match and url_match and logo_match):
        mismatches += 1
        print(f"Mismatch in {r1['id']} ({r1['name']}): id={id_match}, name={name_match}, desc={desc_match}, url={url_match}, logo={logo_match}")

print('Export Mismatches Total:', mismatches)
