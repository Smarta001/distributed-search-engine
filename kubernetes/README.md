# Kubernetes manifests

Assumes a local cluster (minikube or kind) — `imagePullPolicy: Never` on the
app containers means they're expected to already exist in the cluster's own
image store, not pulled from a registry.

## 1. Build images into the cluster

With minikube:
```bash
eval $(minikube docker-env)

docker build -t crawler:latest -f crawler/Dockerfile .
docker build -t indexer:latest -f indexer/Dockerfile .
docker build -t search-api:latest -f search-api/Dockerfile .
```
(run from the repo root, since the indexer and search-api Dockerfiles need
the `shared/` package alongside their own folder)

With kind, use `kind load docker-image <name>:latest` after a normal
`docker build` instead of the `eval` step above.

## 2. Apply everything

```bash
kubectl apply -f kubernetes/
```
Files are numbered so `kubectl apply -f kubernetes/` (which applies
alphabetically) creates the namespace/secrets/config before anything that
depends on them.

## 3. Check status

```bash
kubectl get all -n search-engine
kubectl logs -n search-engine job/crawler
kubectl logs -n search-engine deployment/indexer
```

## 4. Reach search-api

```bash
minikube service search-api -n search-engine
# or: curl http://localhost:30080/health   (after `minikube tunnel` or on kind's mapped port)
```

## Known gotchas

- **Elasticsearch and `vm.max_map_count`**: if the ES pod crash-loops with a
  `max virtual memory areas vm.max_map_count [65530] is too low` error, run
  `minikube ssh -- sudo sysctl -w vm.max_map_count=262144` (or the
  equivalent on your cluster's node) before reapplying.
- **Re-running the crawler**: it's a Job, so it won't restart on its own once
  it finishes. `kubectl delete job crawler -n search-engine && kubectl apply
  -f 07-crawler-job.yaml` to run it again.
- **Secrets file**: `01-secrets.yaml` has the same dev credentials as your
  `docker-compose.yml`, in plaintext, for class-project convenience. Don't
  reuse this pattern for anything beyond local/dev use.
