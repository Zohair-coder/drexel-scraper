"""One-time, idempotent upgrade of the checked-in Grafana dashboard."""
import json
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "k8s/drexel-scraper/dashboards/scheduler.json"
dashboard = json.loads(path.read_text())
query = """SELECT label AS __text, code AS __value FROM terms WHERE available
ORDER BY (code = to_char(CURRENT_DATE - interval '8 months', 'YYYY') ||
CASE WHEN extract(month FROM CURRENT_DATE) >= 9 THEN '15'
WHEN extract(month FROM CURRENT_DATE) <= 3 THEN '25'
WHEN extract(month FROM CURRENT_DATE) <= 6 THEN '35' ELSE '45' END) DESC, code DESC"""
if not any(v["name"] == "quarter" for v in dashboard["templating"]["list"]):
    dashboard["templating"]["list"].insert(0, {
        "name": "quarter", "label": "Quarter", "type": "query",
        "datasource": {"type": "postgres", "uid": "scheduler-postgres"},
        "query": query, "definition": query, "refresh": 1, "sort": 0,
        "multi": False, "includeAll": False, "current": {}, "options": []
    })
scope = """WITH courses AS (
 SELECT *, prerequisites AS prereqs,
 CASE WHEN is_full THEN 'FULL' ELSE enrolled::text END AS enroll,
 capacity::text AS max_enroll
 FROM public.courses WHERE term_code = ${quarter:sqlstring}
), instructors AS (
 SELECT DISTINCT i.* FROM public.instructors i
 JOIN public.course_instructors ci ON ci.instructor_id=i.id
 WHERE ci.term_code = ${quarter:sqlstring}
), all_course_instructor_data AS (
 SELECT * FROM public.all_course_instructor_data WHERE term_code = ${quarter:sqlstring}
)
"""
for panel in dashboard["panels"]:
    if panel["id"] == 17:
        panel["options"]["content"] = panel["options"]["content"].replace(
            'const newUrl = currentUrl.split("&")[0];\n    window.location.href = newUrl + "&kiosk";',
            'const url = new URL(currentUrl);\n    for (const key of [...url.searchParams.keys()]) {\n        if (key.startsWith("var-") && key !== "var-quarter") url.searchParams.delete(key);\n    }\n    url.searchParams.set("kiosk", "true");\n    window.location.href = url.toString();')
    for target in panel.get("targets", []):
        if panel["id"] == 19:
            target["rawSql"] = "SELECT label FROM terms WHERE code = ${quarter:sqlstring}"
        elif panel["id"] == 15:
            target["rawSql"] = "SELECT COALESCE(to_char(last_scraped_at AT TIME ZONE 'America/New_York', 'MM/DD/YY HH12:MI AM'), 'Not loaded yet') AS updated FROM terms WHERE code = ${quarter:sqlstring}"
            panel["title"] = "Selected Quarter Updated (Eastern)"
        elif target.get("rawSql") and not target["rawSql"].startswith("WITH courses AS"):
            target["rawSql"] = scope + target["rawSql"]
dashboard["version"] = 0
path.write_text(json.dumps(dashboard, indent=2) + "\n")
