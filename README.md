# ComfyUI API Bridge Node

Install one node, ComfyUI becomes an API service.

## Install

Copy this folder to `ComfyUI/custom_nodes/comfyui-webhook-node/`:

```
ComfyUI/custom_nodes/comfyui-webhook-node/
  __init__.py
  webhook_node.py
  api_routes.py
```

Restart ComfyUI. Done.

## API Endpoints (auto-registered)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/bridge/run` | POST | Submit workflow + wait for result |
| `/api/bridge/submit` | POST | Submit workflow (async) |
| `/api/bridge/status/{id}` | GET | Check task result |
| `/api/bridge/health` | GET | Health check + queue info |

## Usage

### Health Check
```bash
curl https://your-comfyui-url/api/bridge/health
```

### Run Workflow
```bash
curl -X POST https://your-comfyui-url/api/bridge/run \
  -H "Content-Type: application/json" \
  -d '{
    "workflow": { ... },
    "text": "A cute cat"
  }'
```

The `workflow` field is the API-format JSON exported from ComfyUI (right-click -> Save API Format).

The `text` field is optional - if provided, it auto-injects into the first text input node.

### Async Submit
```bash
curl -X POST https://your-comfyui-url/api/bridge/submit \
  -H "Content-Type: application/json" \
  -d '{"workflow": { ... }, "text": "A cute cat"}'

# Returns: {"prompt_id": "xxx", "status": "queued"}

# Then check result:
curl https://your-comfyui-url/api/bridge/status/xxx
```

## Also Includes

**Webhook Callback** output node - place at the end of any workflow to POST results to a callback URL when execution completes. Search "Webhook" in the node list.
