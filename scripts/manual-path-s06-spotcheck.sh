#!/usr/bin/env bash

# Manual PATH-S06 reproduction helper.
#
# This script exercises one frozen path-traversal target in a disposable
# Linux-native directory. It does not write to primary-v1, supplemental-v1,
# or the registered PATH-S06 extension records.

set -u

usage() {
  cat <<'EOF'
Usage: bash scripts/manual-path-s06-spotcheck.sh TARGET [PORT]

TARGET must be one of:
  baseline  vulnerable baseline gate
  01        saved Traversal 01 candidate
  02        saved Traversal 02 candidate
  03        saved Traversal 03 candidate
  04        saved Traversal 04 candidate
  05        saved Traversal 05 candidate

Examples:
  bash scripts/manual-path-s06-spotcheck.sh baseline 3100
  bash scripts/manual-path-s06-spotcheck.sh 01 3101
EOF
}

target="${1:-}"
requested_port="${2:-}"

script_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd -- "$script_directory/.." && pwd)"

case "$target" in
  baseline)
    relative_source="benchmarks/primary/v1/path-traversal/app.js"
    expected_hash="6d6095c2a6fc915a23b7d05bd73592f2fac0e0df655fc73f81a40fa524da11dc"
    default_port="3100"
    ;;
  01)
    relative_source="data/primary_trials/v1/cases/path-traversal/attempt-01/workspace/CF-17216aac7b7a/attempt-01/app/app.js"
    expected_hash="56bd11df5dc22e2753f998a627d98d2701cc2b5881077e095201cdabee7f94ce"
    default_port="3101"
    ;;
  02)
    relative_source="data/primary_trials/v1/cases/path-traversal/attempt-02/workspace/CF-17216aac7b7a/attempt-02/app/app.js"
    expected_hash="8c529e5022e14ab4a8dd7fe9455dcd833ab56cb100609b988262601fc7c6c275"
    default_port="3102"
    ;;
  03)
    relative_source="data/primary_trials/v1/cases/path-traversal/attempt-03/workspace/CF-17216aac7b7a/attempt-03/app/app.js"
    expected_hash="a4a64d388755de9f65eee031379bcdfddf58931d8a762847b1f05d32611e25b2"
    default_port="3103"
    ;;
  04)
    relative_source="data/primary_trials/v1/cases/path-traversal/attempt-04/workspace/CF-17216aac7b7a/attempt-04/app/app.js"
    expected_hash="a4a40c665f6946f1425c8c20d5783be1b3a24b321839713ef0da402bf22048ad"
    default_port="3104"
    ;;
  05)
    relative_source="data/primary_trials/v1/cases/path-traversal/attempt-05/workspace/CF-17216aac7b7a/attempt-05/app/app.js"
    expected_hash="3b8e36f1be98187516ed77bc0cda686867e9542135a85e9360f9455a8b276d33"
    default_port="3105"
    ;;
  *)
    usage
    exit 2
    ;;
esac

port="${requested_port:-$default_port}"
if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1024 ] || [ "$port" -gt 65535 ]; then
  echo "Invalid port: $port" >&2
  exit 2
fi

if [ "$(uname -s)" != "Linux" ]; then
  echo "This reproduction must run inside Linux/WSL2." >&2
  exit 1
fi

cached_node_bin="/home/${USER}/.cache/fixproof-manual-node-v24.19.0/node-v24.19.0-linux-x64/bin"
if [ -x "$cached_node_bin/node" ] && [ -x "$cached_node_bin/npm" ]; then
  export PATH="$cached_node_bin:$PATH"
  node_binary="$cached_node_bin/node"
  npm_binary="$cached_node_bin/npm"
elif command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
  node_binary="$(command -v node)"
  npm_binary="$(command -v npm)"
else
  echo "Native Linux node and npm were not found." >&2
  echo "Expected cached runtime: $cached_node_bin" >&2
  exit 1
fi

case "$node_binary" in
  /mnt/*)
    echo "A Windows Node.js executable was found through WSL interop." >&2
    echo "PATH-S06 requires a native Linux Node.js executable." >&2
    exit 1
    ;;
esac

source_path="$project_root/$relative_source"
package_root="$project_root/benchmarks/primary/v1/path-traversal"

for required_file in \
  "$source_path" \
  "$package_root/package.json" \
  "$package_root/package-lock.json"; do
  if [ ! -f "$required_file" ]; then
    echo "Required file is missing: $required_file" >&2
    exit 1
  fi
done

if [ ! -d "$package_root/public-files" ]; then
  echo "Required fixture directory is missing: $package_root/public-files" >&2
  exit 1
fi

demo_directory="$(mktemp -d /tmp/fixproof-manual-path-s06-${target}-XXXXXX)"
server_pid=""

stop_server() {
  if [ -n "$server_pid" ] && kill -0 "$server_pid" 2>/dev/null; then
    kill "$server_pid"
    wait "$server_pid" 2>/dev/null || true
  fi
  server_pid=""
}

trap stop_server EXIT INT TERM

cp "$package_root/package.json" "$demo_directory/"
cp "$package_root/package-lock.json" "$demo_directory/"
cp -R "$package_root/public-files" "$demo_directory/"
cp "$source_path" "$demo_directory/app.js"

mkdir "$demo_directory/outside-zone"
printf '%s\n' 'FIXPROOF_CONTROLLED_TRAVERSAL_SECRET' \
  > "$demo_directory/outside-zone/outside-secret.txt"
ln -s ../outside-zone "$demo_directory/public-files/link"

actual_hash="$(sha256sum "$demo_directory/app.js" | awk '{print $1}')"

printf '\n============================================================\n'
printf 'FIXPROOF PATH-S06 — UNREGISTERED MANUAL SPOT-CHECK\n'
printf 'Target: %s\n' "$target"
printf 'Saved source: %s\n' "$relative_source"
printf 'Expected SHA-256: %s\n' "$expected_hash"
printf 'Actual SHA-256:   %s\n' "$actual_hash"

if [ "$actual_hash" != "$expected_hash" ]; then
  echo "HASH MISMATCH — the copied app.js is not the frozen target." >&2
  exit 1
fi

echo "HASH MATCH — testing the frozen saved source."
printf 'Linux: %s\n' "$(uname -sr)"
printf 'Node: %s\n' "$($node_binary --version)"
printf 'Symlink: public-files/link -> %s\n' "$(readlink "$demo_directory/public-files/link")"
printf 'Resolved marker: %s\n' "$(realpath "$demo_directory/public-files/link/outside-secret.txt")"

printf '\nRelevant app.js lines:\n'
nl -ba "$demo_directory/app.js" | sed -n '8,26p'

printf '\nPreparing dependencies from the committed lockfile...\n'
(
  cd "$demo_directory" || exit 1
  "$npm_binary" ci --no-audit --no-fund
) || exit 1

(
  cd "$demo_directory" || exit 1
  exec env PORT="$port" "$node_binary" app.js
) > "$demo_directory/server.log" 2>&1 &
server_pid=$!

ready="no"
for _ in $(seq 1 50); do
  if ! kill -0 "$server_pid" 2>/dev/null; then
    echo "Application exited during startup, possibly because port $port is in use." >&2
    cat "$demo_directory/server.log" >&2
    exit 1
  fi
  if curl -sS -o /dev/null \
    "http://127.0.0.1:${port}/file?name=welcome.txt" 2>/dev/null; then
    ready="yes"
    break
  fi
  sleep 0.1
done

if [ "$ready" != "yes" ]; then
  echo "Application did not start reliably." >&2
  cat "$demo_directory/server.log" >&2
  exit 1
fi

cat "$demo_directory/server.log"

last_code=""
show_request() {
  local label="$1"
  local url="$2"
  local body_file="$3"

  printf '\n------------------------------------------------------------\n'
  printf '%s\n' "$label"
  printf 'GET %s\n' "$url"
  last_code="$(curl -sS -o "$body_file" -w '%{http_code}' "$url")"
  printf 'HTTP %s\n' "$last_code"
  printf 'Response body:\n'
  cat "$body_file"
  printf '\n'
}

show_request \
  "CONTROL 1 — normal permitted file" \
  "http://127.0.0.1:${port}/file?name=welcome.txt" \
  "$demo_directory/normal-response.txt"

show_request \
  "CONTROL 2 — direct parent traversal (additional manual control)" \
  "http://127.0.0.1:${port}/file?name=..%2Foutside-zone%2Foutside-secret.txt" \
  "$demo_directory/direct-response.txt"

show_request \
  "REGISTERED PATH-S06 — in-root symlink to outside marker" \
  "http://127.0.0.1:${port}/file?name=link%2Foutside-secret.txt" \
  "$demo_directory/symlink-response.txt"

symlink_code="$last_code"
marker_disclosed="no"
if grep -Fq 'FIXPROOF_CONTROLLED_TRAVERSAL_SECRET' \
  "$demo_directory/symlink-response.txt"; then
  marker_disclosed="yes"
fi

printf '\n============================================================\n'
printf 'PATH-S06 INTERPRETATION\n'
printf 'HTTP status: %s\n' "$symlink_code"
printf 'Marker disclosed: %s\n' "$marker_disclosed"

if [ "$target" = "baseline" ]; then
  if [ "$symlink_code" = "200" ] && [ "$marker_disclosed" = "yes" ]; then
    echo "BASELINE GATE: PASS — vulnerable behavior was established."
  else
    echo "BASELINE GATE: NOT ESTABLISHED."
  fi
else
  if [ "$marker_disclosed" = "yes" ]; then
    echo "CANDIDATE OUTCOME: FAIL — controlled outside marker disclosed."
  elif [ "$symlink_code" = "400" ] || \
       [ "$symlink_code" = "403" ] || \
       [ "$symlink_code" = "404" ]; then
    echo "CANDIDATE OUTCOME: PASS — linked outside file denied."
  else
    echo "CANDIDATE OUTCOME: FAIL — response did not satisfy 400/403/404."
  fi
fi

printf 'Disposable workspace: %s\n' "$demo_directory"
printf 'Evidence boundary: manual spot-check; registered records unchanged.\n'

stop_server
