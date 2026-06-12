---
mode: 'agent'
description: 'Production Kubernetes patterns and security.'
---

# Kubernetes Engineering

## Kubernetes Best Practices
- Set resource requests and limits for all containers.
- Use namespaces for isolation.
- Never run containers as root; use securityContext.
- Use NetworkPolicies to restrict pod communication.
- Use Secrets for sensitive config; never ConfigMaps for secrets.
- Use readiness and liveness probes.
- Use PodDisruptionBudgets for availability.
- Use Helm or Kustomize for templating; avoid raw kubectl apply.
- Use RBAC with least privilege.
- Use pod anti-affinity for high availability.

> **Governance**: This skill enforces policies: INF-001, SEC-001.
