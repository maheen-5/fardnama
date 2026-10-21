# fardnama
AI powered cyberbullying evidence collection and reporting platform that combines automated harassment detection with tamper evident evidence preservation, and generates a formal report that can support a victim throughout the reporting process.

## Repository structure

- `.github/workflows/` contains CI and deployment automation.
- `deployment/` contains the Docker Compose stack, private IPFS bootstrap setup, and operational docs.
- `docs/` contains the architecture and design documentation.
- `backend/` is owned by the backend team and is used for the FastAPI service and runtime container.
- `frontend/`, `classifier/`, and any contract or app folders are maintained by their respective owners.

## Branches

- `main` = protected and deployable.
- `develop` = integration.
- `feature/*` = one per module.
- All changes flow via pull requests into `develop`.

## Local setup

See [deployment/README.md](deployment/README.md) for the local stack, secret generation, and deployment instructions.
