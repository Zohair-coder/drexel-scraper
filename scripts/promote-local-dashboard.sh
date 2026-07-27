#!/usr/bin/env bash

set -euo pipefail

readonly DASHBOARD_UID="db64b0ee-89cf-46ab-a3f5-af315d8e1e0f"
readonly DATASOURCE_UID="scheduler-postgres"
readonly GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly DASHBOARD_FILE="${REPO_ROOT}/k8s/drexel-scraper/dashboards/scheduler.json"

for command in curl jq; do
  if ! command -v "${command}" >/dev/null 2>&1; then
    echo "Required command not found: ${command}" >&2
    exit 1
  fi
done

temp_dir="$(mktemp -d)"
trap 'rm -rf "${temp_dir}"' EXIT

api_response="${temp_dir}/dashboard-api.json"
exported_dashboard="${temp_dir}/scheduler.json"

echo "Exporting ${DASHBOARD_UID} from ${GRAFANA_URL}..."
curl --fail --silent --show-error \
  "${GRAFANA_URL}/api/dashboards/uid/${DASHBOARD_UID}" \
  --output "${api_response}"

jq '.dashboard | del(.id) | .version = 0' \
  "${api_response}" > "${exported_dashboard}"

jq -e --arg dashboard_uid "${DASHBOARD_UID}" --arg datasource_uid "${DATASOURCE_UID}" '
  .uid == $dashboard_uid
  and .title == "Scheduler Dashboard"
  and ([
    .. | objects | .datasource? // empty
    | select(type == "object")
    | .uid? // empty
    | select(. != "-- Grafana --" and . != $datasource_uid)
  ] | length == 0)
  and ([.panels[] | select(.id == 17) | .options.content][0] | contains("posthog.init"))
  and ([.panels[] | select(.id == 17) | .options.content][0]
    | contains("if ([\"scheduler.zohair.dev\", \"www.scheduler.zohair.dev\"].includes(window.location.hostname))"))
' "${exported_dashboard}" >/dev/null

mv "${exported_dashboard}" "${DASHBOARD_FILE}"

echo "Updated ${DASHBOARD_FILE}"
echo "Review the dashboard diff, then commit it when you are ready to deploy."
