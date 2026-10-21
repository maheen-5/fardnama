# Deployment guide

## Purpose

This deployment config runs the FardNama evidence pipeline in a private, self-hosted environment for the Final Year Project. It includes five containers that work together to collect, store, verify, and expose evidence metadata:

- `postgres` stores relational metadata and vector embeddings in PostgreSQL 16 with pgvector.
- `redis` stores short-lived caching and task coordination state for the backend.
- `ipfs` stores encrypted/private evidence payloads on a private Kubo IPFS network.
- `ethereum` runs a local Anvil chain for the EvidenceRegistry contract and local blockchain state.
- `backend` runs the FastAPI service exposing the application API and health endpoint.

For the broader architecture background, see [docs/architecture/ipfs-ethereum-design.md](../docs/architecture/ipfs-ethereum-design.md).

## Local quick start

```bash
cp .env.example .env
bash deployment/scripts/gen-secrets.sh
cd deployment
docker compose up -d
docker compose ps
docker compose logs -f backend
```

## Oracle VM setup

1. Create an Oracle Cloud Always Free Ampere A1 (ARM64) Ubuntu 22.04 VM with SSH-key login enabled.
2. Install Docker Engine and the Compose v2 plugin.
3. Add the deploy user to the `docker` group.
4. Clone the repository into `~/fardnama`.
5. Create a `.env` file at the repo root and run `bash deployment/scripts/gen-secrets.sh` on the VM.
6. Open only port `22` (SSH) and port `8000` (temporary, until the HTTPS reverse proxy is added in Final-1) in both the VCN security list and the Ubuntu host firewall. Oracle Ubuntu images use `iptables`.

## GitHub secrets for CD

Add these repository secrets under Settings -> Secrets and variables -> Actions -> New repository secret:

- `ORACLE_VM_HOST`
- `ORACLE_VM_USER`
- `ORACLE_VM_SSH_KEY`

This allows the deployment workflow to connect to the Ubuntu VM and pull the backend image from GHCR.

## How CI and CD work

- CI runs on pull requests into `develop` and on pushes to `develop`, `main`, and `feature/*` branches.
- CD runs on pushes to `main` and via `workflow_dispatch`.
- The deployment workflow validates the backend artifact, builds the image for `linux/arm64` and `linux/amd64`, pushes it to GHCR, and then deploys from the VM using Docker Compose.

## Backups

- Schedule a PostgreSQL backup using `pg_dump` and store it off-host in encrypted form.
- Snapshot the IPFS volume regularly; because the IPFS network is private, the data remains ciphertext-only from the application perspective.
- Test restore procedures for both the database and the IPFS volume on a regular basis to confirm recovery time objectives.

## Host-hardening checklist

Risk R1 checklist:

- SSH keys only; disable password login.
- Disable unattended upgrades if the VM is not managed centrally, or ensure they remain enabled.
- Never expose ports `5001`, `8080`, `8545`, `5432`, or `6379` to the public network.
- Run containers as non-root where possible.
- Keep only port `22` and temporary port `8000` open until the reverse proxy is added.

## Known limitations

- The local chain is operator-controlled for the project prototype.
- There is a single IPFS node in this deployment.
- HTTPS reverse proxy support is not yet in place.
- The backend owner must provide the `GET /health` endpoint.
- EvidenceRegistry deployment occurs in Final-1.
