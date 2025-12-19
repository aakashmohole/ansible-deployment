## MLx Ansible Deployment

This project automates deployment of Docker-based workloads (including GPU-aware Celery workers) to one or more hosts using Ansible and Docker/Docker Compose.

The repo contains:

- `deploy-playbook.yml`: main Ansible playbook that prepares the host (GPU / non-GPU), installs Docker, copies helper scripts, and runs the deployment.
- `deploy.py`: simple deployment helper that stops an existing container and starts a new one with the specified image and name.
- `deploy_docker_services.py`: generates a `docker-compose.yml` for the Celery workers and watchtower based on the number of GPUs and the chosen deploy mode.
- `docker-compose.yml`: a sample/generated compose file (watchtower service) – normally overwritten by `deploy_docker_services.py`.
- `hosts.ini`: Ansible inventory with target VM(s) and per-host `deploy_type`.
- `install_gpu.sh` / `install_docker.sh`: basic shell hooks to distinguish GPU vs non-GPU machines; can be replaced with real installers.
- `vault.yml`: Ansible Vault–encrypted variables file (secrets).
- `c.txt`: vault password is in this file.

### 1. Prerequisites

- **Local machine**
  - Python 3
  - Ansible (`ansible`, `ansible-playbook` in PATH)
  - Docker CLI if you want to run the containers locally
- **Remote hosts**
  - SSH access from the control machine
  - `python3` installed on the target (for `deploy.py`)
  - Ability to install Docker (via package manager or your own scripts)

### 2. Inventory (`hosts.ini`)

`hosts.ini` defines the Ansible inventory group `vms` and any per-host variables:

- **Group**: `vms`
- **Example entry**:
  - `aws1 ansible_host=54.252.153.17 deploy_type=small`
  - Commented example includes `ansible_user` and `ansible_ssh_private_key_file` for EC2-style access.
- You can add hosts and set `deploy_type` (`small`, `large`, `critical`) per host. The playbook uses this to compute the `deploy_flags` passed to the Python deployment logic.

### 3. Secrets and Passwords (`vault.yml`)

- `vault.yml` is **encrypted with Ansible Vault** (`$ANSIBLE_VAULT;1.1;AES256` header).
- This file is referenced in `deploy-playbook.yml` via:
  - `vars_files: - vault.yml`
- **Vault password is not stored in this repository.**
  - You must supply it at runtime with one of:
    - `ansible-playbook --ask-vault-pass ...`
    - or `ansible-playbook --vault-password-file /path/to/vault_pass.txt ...`
- To **edit** the vault file:
  - `ansible-vault edit vault.yml`
- To **view** the vault contents (for your senior):
  - `ansible-vault view vault.yml`

If you create a new vault file:

- `ansible-vault create vault.yml`
- Share the **vault password** with your senior out-of-band (not in Git), together with:
  - Location of any `vault_pass.txt` file, if used.
  - Any external secret sources (e.g. Hashicorp Vault address/token; see below).

### 4. Hashicorp Vault / Runtime Secrets (Docker services)

`deploy_docker_services.py` generates a Compose file for Celery workers and watchtower. It expects the following environment variables on the machine where Compose will run:

- `VAULT_ADDRESS`
- `VAULT_TOKEN`

These are **not stored** in this repo; set them in the host environment before starting Docker Compose:

- `export VAULT_ADDRESS="https://your-vault-server:8200"`
- `export VAULT_TOKEN="s.xxxxxxxx"` _(example only – use real token from your Vault setup)_

The script injects these into service environment:

- `VAULT_ADDR`: points services to your Vault server.
- `VAULT_TOKEN`: used by services to fetch runtime secrets.

### 5. Ansible Playbook (`deploy-playbook.yml`)

This playbook:

- Loads `vault.yml`.
- Checks `python3`, `docker`, and GPU presence (`nvidia-smi`).
- Copies and runs:
  - `install_gpu.sh` on GPU hosts.
  - `install_docker.sh` on non-GPU hosts.
- Installs and starts Docker on Debian/RedHat when missing.
- Copies `deploy.py` to the remote host.
- Sets `deploy_flags` according to `deploy_type`:
  - `large` → `--deploy_large_job`
  - `critical` → `--deploy_critical_job`
  - anything else / default → `--deploy_small_job`
- Executes `deploy.py` on the remote host:
  - `python3 /tmp/deploy.py <flags> --image <docker_image> --container-name <container_name>`
- Verifies that the container is running.

Key variables (inside the playbook):

- `docker_image`: Docker image to deploy (default `nginx:latest`).
- `container_name`: Container name (default `app-container`).
- `deploy_type`: from `hosts.ini` per host.

### 6. Deployment Helper (`deploy.py`)

`deploy.py` is a small wrapper around `docker run`:

- **Arguments:**
  - `--deploy_large_job` / `--deploy_small_job` / `--deploy_critical_job` (exactly one must be set).
  - `--image`: Docker image (required).
  - `--container-name`: container name (required).
- Behavior:
  - Determines deploy type for logging only.
  - Runs `docker rm -f <container-name>` (ignores error only if container missing when wrapped by Ansible).
  - Runs `docker run -d --name <container-name> -p 8080:80 <image>`.

This script is intended to be extended if you later need different behavior per deploy type.

### 7. Docker Services Generator (`deploy_docker_services.py`)

`deploy_docker_services.py`:

- Detects number of GPUs via `nvidia-smi -L`.
- Accepts flags:
  - `--deploy_large_job`
  - `--deploy_small_job`
  - `--deploy_critical_job`
- Builds a `docker-compose.yml` with:
  - One `watchtower` service.
  - A set of worker services (`model_processor`, `yolo_worker`, `unet_worker`, `dino_worker`, `detr_worker`) replicated per GPU.
- Filters Celery queues/keys based on deploy flags (large/small/critical).
- Injects environment like:
  - `environment=prod-secrets`, `batch_size`, `NVIDIA_DEVICE`, and `VAULT_ADDR` / `VAULT_TOKEN`.
- Writes `docker-compose.yml` in the current directory and prints status.

Currently, the `docker compose down/up` calls are commented out; you or your senior can enable them or run Compose manually:

- `docker compose up -d`

### 8. Watchtower Compose (`docker-compose.yml`)

The checked-in `docker-compose.yml` shows:

- A single `watchtower` service using `containrrr/watchtower`.
- Bind-mounts:
  - `/var/run/docker.sock`
  - `~/.docker/config.json`
- Slack notifications via:
  - `WATCHTOWER_NOTIFICATION_URL=slack://watchtower@T02DZT0TD27/B07RLPDKETB/...`

You should:

- Replace the Slack URL with your own Webhook/token before use.
- Consider generating this file only from `deploy_docker_services.py` to avoid drift.

### 9. GPU / Non-GPU Setup Scripts

- `install_gpu.sh`:
  - Currently logs `"GPU machine"`.
  - Place your GPU driver + CUDA + Docker setup commands here.
- `install_docker.sh`:
  - Currently logs `"Non-GPU machine"` and creates a `test.py` file.
  - Replace with your OS-specific Docker installation/configuration logic if you don't rely on the Ansible `yum`/`apt` tasks.

### 10. Typical Usage Workflow

1. **Prepare inventory and secrets**
   - Edit `hosts.ini` with correct hosts and `deploy_type`.
   - Ensure `vault.yml` contains any required variables and that you know the vault password.
2. **(Optional) Generate worker Compose file**
   - On the target GPU host:
     - `export VAULT_ADDRESS=...`
     - `export VAULT_TOKEN=...`
     - `python3 deploy_docker_services.py --deploy_small_job` _(or other flags)_
3. **Run Ansible playbook from control node**
   - `cd /media/aakash-mohole/C4602E3D602E3698/MLx/ansible`
   - `ansible-playbook -i hosts.ini deploy-playbook.yml --ask-vault-pass`
4. **Verify**
   - On the remote host: `docker ps` to check your container and any worker services.
   - Check watchtower and worker logs via `docker logs`.
