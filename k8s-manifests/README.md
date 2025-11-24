
# Kanchi: Kubernetes Deployment Guide

This short guide provides step-by-step instructions for deploying a basic Kanchi instance on a Kubernetes cluster within a single namespace.

---

## Configuration

The manifest files in this directory use **placeholders** (enclosed in double curly braces, e.g., `{{YOUR_K8S_NAMESPACE}}`). Replace these with your actual configuration values. Optional placeholders are marked in the lists below and in the manifest comments.

### Global Placeholders

- **`{{YOUR_K8S_NAMESPACE}}`**: The Kubernetes namespace where Kanchi will be deployed.

---

### Deployment (`deploy.yml`)

- **`{{YOUR_CELERY_BROKER_URL}}`**: The URL of your Celery Broker.
- **`{{YOUR_KANCHI_USER}}`** *(Optional)*: Username for basic authentication.
- **`{{YOUR_DATABASE_URL}}`** *(Optional)*: Database URL string (including authentication and database name) for persistent storage. If not provided, Kanchi will use an ephemeral SQLite database.
  - For MySQL, use the following placeholders:
    - **`{{MYSQL_USER}}`**, **`{{MYSQL_PASS}}`**, **`{{MYSQL_HOST}}`**, **`{{MYSQL_PORT}}`**, **`{{MYSQL_DB}}`**
- **`{{YOUR_KANCHI_HOST}}`** *(Optional)*: DNS name for accessing Kanchi via an Ingress.

---

### Persistent Volume Claim (`pvc.yml`)
- **`{{YOUR_K8S_STORAGE_CLASS}}`** *(Optional)*: Name of the storage class. If your cluster has a default storage class, this can be omitted.

---

### Ingress (`ingress.yml`)

- **`{{YOUR_INGRESS_CONTROLLER_CLASS}}`** *(Optional)*: Name of the Ingress controller class. If your cluster has a default Ingress controller, this can be omitted.
- **`{{YOUR_KANCHI_HOST}}`** *(Optional)*: DNS name for accessing Kanchi via an Ingress.

---

### Secret (`secret.yml`)

- **`{{YOUR_KANCHI_PASSWORD}}`** *(Optional)*: Password for basic authentication.

---

## Deployment Instructions

1. **Configure the Manifests**:
   Replace all placeholders in the manifest files with your actual values.

2. **Apply the Manifests**:
   Use `kubectl` to apply each manifest:
   ```bash
   kubectl apply -f {{MANIFEST_FILE}}

3. If you decide against using an ingress, you will not be able to access Kanchi through a regular (/public) URL. In that case, you will need to run two port-forwards so that you can access Kanchi through a "localhost" URL. In that case you will access it through "http://localhost:3000"
For the UI: `kubectl -n {{YOUR_K8S_NAMESPACE}} port-forward service/kanchi 3000:3000`
For the Websockets: `kubectl -n {{YOUR_K8S_NAMESPACE}} port-forward service/kanchi 8765:8765`
