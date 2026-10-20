#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
ipfs_dir="${repo_root}/ipfs"
secrets_dir="${repo_root}/secrets"

mkdir -p "${ipfs_dir}" "${secrets_dir}"
chmod 700 "${ipfs_dir}" "${secrets_dir}"

if [ ! -f "${ipfs_dir}/swarm.key" ]; then
  {
    printf '/key/swarm/psk/1.0.0/\n'
    printf '/base16/\n'
    openssl rand -hex 32
  } > "${ipfs_dir}/swarm.key"
  chmod 600 "${ipfs_dir}/swarm.key"
  printf 'Created %s\n' "${ipfs_dir}/swarm.key"
else
  printf 'Already exists: %s\n' "${ipfs_dir}/swarm.key"
fi

if [ ! -f "${secrets_dir}/fardnama_kek" ]; then
  openssl rand -base64 32 > "${secrets_dir}/fardnama_kek"
  chmod 600 "${secrets_dir}/fardnama_kek"
  printf 'Created %s\n' "${secrets_dir}/fardnama_kek"
else
  printf 'Already exists: %s\n' "${secrets_dir}/fardnama_kek"
fi

if [ ! -f "${secrets_dir}/registrar_key" ]; then
  cat > "${secrets_dir}/registrar_key" <<'EOF'
# for local Anvil only, paste Anvil dev account #0's private key here; never use a dev key on a public network.
EOF
  chmod 600 "${secrets_dir}/registrar_key"
  printf 'Created %s\n' "${secrets_dir}/registrar_key"
else
  printf 'Already exists: %s\n' "${secrets_dir}/registrar_key"
fi
