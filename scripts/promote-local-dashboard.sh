#!/usr/bin/env bash

set -euo pipefail

readonly DASHBOARD_UID="db64b0ee-89cf-46ab-a3f5-af315d8e1e0f"
readonly DATASOURCE_UID="scheduler-postgres"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly DASHBOARD_FILE="${REPO_ROOT}/k8s/drexel-scraper/dashboards/scheduler.json"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/promote-local-dashboard.sh --clipboard
  ./scripts/promote-local-dashboard.sh PATH_TO_EXPORTED_JSON
  ./scripts/promote-local-dashboard.sh -

Sources:
  --clipboard  Read dashboard JSON from the macOS clipboard using pbpaste.
  PATH         Read dashboard JSON exported to a file by Grafana.
  -            Read dashboard JSON from standard input.
EOF
}

if (( $# != 1 )); then
  usage >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "Required command not found: jq" >&2
  exit 1
fi

temp_dir="$(mktemp -d)"
trap 'rm -rf "${temp_dir}"' EXIT

source_json="${temp_dir}/dashboard-source.json"
exported_dashboard="${temp_dir}/scheduler.json"

source_mode="${1}"

case "${source_mode}" in
  --clipboard)
    if (( $# != 1 )); then
      usage >&2
      exit 1
    fi
    if ! command -v pbpaste >/dev/null 2>&1; then
      echo "Required command not found: pbpaste (use a file path or '-' instead)" >&2
      exit 1
    fi
    echo "Reading dashboard JSON from the macOS clipboard..."
    pbpaste > "${source_json}"
    ;;
  -)
    if (( $# != 1 )); then
      usage >&2
      exit 1
    fi
    echo "Reading dashboard JSON from standard input..."
    cp /dev/stdin "${source_json}"
    ;;
  --help|-h)
    usage
    exit 0
    ;;
  --*)
    echo "Unknown option: ${source_mode}" >&2
    usage >&2
    exit 1
    ;;
  *)
    if (( $# != 1 )); then
      usage >&2
      exit 1
    fi
    if [[ ! -f "${source_mode}" ]]; then
      echo "Dashboard JSON file not found: ${source_mode}" >&2
      exit 1
    fi
    echo "Reading dashboard JSON from ${source_mode}..."
    cp "${source_mode}" "${source_json}"
    ;;
esac

jq '
  (if type == "object" and (.dashboard? | type) == "object"
   then .dashboard
   else .
   end)
  | del(.id)
  | .version = 0
' "${source_json}" > "${exported_dashboard}"

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
