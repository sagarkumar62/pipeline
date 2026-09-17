import csv

with open("docs/phase5_final_dataset_audit.csv", "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

review_rows = [r for r in rows if r["final_status"] == "REVIEW_REQUIRED"]
print(f"Total REVIEW_REQUIRED rows: {len(review_rows)}")
for r in review_rows:
    print(f"- [{r['id']}] {r['name']}: {r['issues']} | UrlClass: {r['official_url_classification']} | LogoClass: {r['logo_classification']}")
