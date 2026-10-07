#!/usr/bin/env sh
# Downloads the open-access papers cited in research/ into demo/library/ for indexing.
# They are fetched from their publishers rather than committed, to respect their licences.
set -e
cd "$(dirname "$0")/library"
while read -r name url; do
  [ -f "$name" ] && { echo "have $name"; continue; }
  curl -sSL --fail -A "Mozilla/5.0 (WAWASAN demo)" -o "$name" "$url" && echo "got  $name"
done <<'EOF'
barnett2024-seven-failure-points-rag.pdf https://arxiv.org/pdf/2401.05856
arxiv-2411.13691.pdf https://arxiv.org/pdf/2411.13691
arxiv-2601.15457.pdf https://arxiv.org/pdf/2601.15457
arxiv-2603.24580.pdf https://arxiv.org/pdf/2603.24580
arxiv-2604.27713.pdf https://arxiv.org/pdf/2604.27713
wjaets-2025-1059.pdf https://wjaets.com/sites/default/files/fulltext_pdf/WJAETS-2025-1059.pdf
ceur-vol3580-paper7.pdf https://ceur-ws.org/Vol-3580/paper7.pdf
ijisrt24apr316.pdf https://www.ijisrt.com/assets/upload/files/IJISRT24APR316.pdf
EOF
