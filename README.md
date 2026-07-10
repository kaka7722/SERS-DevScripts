# SERS-DevScripts

Deployment and local development helper scripts for **SERS-MAKERHUB**.

## Folder Layout

| Folder | Original Location | Purpose |
|--------|-------------------|---------|
| `nas-scripts/` | `SERS_Dev_Scripts/NAS开启关闭前后端` | Deploy / start / stop / restart SERS-MAKERHUB on the UGREEN DXP4800 NAS |
| `local-scripts/` | `SERS_Dev_Scripts/本地开启关闭前后端` | Start / stop the frontend and backend on a local Windows dev machine |

## Security Notice

- **No passwords or secrets are stored in this repository.**
- NAS scripts read the password from the `NAS_PASSWORD` environment variable or prompt interactively.
- For first-time setup, run `nas-scripts/setup-env.ps1` to create the local Python virtual environment.

## Quick Start

### NAS Deployment

```powershell
cd nas-scripts
.\setup-env.ps1      # one-time
.\deploy-nas.ps1     # build frontend, upload, and restart NAS services
```

### Local Development

```powershell
cd local-scripts
.\start-all.ps1      # opens backend (localhost:5000) and frontend (localhost:5173)
.\stop-all.ps1       # stops all local dev processes
```

See the `README.md` inside each folder for detailed usage.
