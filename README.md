# ComfyUI Webhook Callback Node

A single custom node that sends workflow results to a webhook URL when execution completes.

## Install

Copy this folder to `ComfyUI/custom_nodes/comfyui-webhook-node/`:

```
ComfyUI/custom_nodes/comfyui-webhook-node/
  __init__.py
  webhook_node.py
```

Restart ComfyUI. Search "Webhook" in the node list.

## Usage

1. Add **Webhook Callback (API Bridge)** node to your workflow
2. Connect your output (images / text / audio) to the node
3. Set `webhook_url` to your callback endpoint
4. Set `task_id` to identify the task

When the workflow finishes, the node POSTs results as JSON to your webhook URL.

## Payload Format

```json
{
  "task_id": "abc123",
  "status": "completed",
  "outputs": {
    "images": [{"filename": "output.png", "type": "image/png", "base64": "..."}],
    "text": "generated text",
    "audio": [{"filename": "output.wav", "type": "audio/wav", "base64": "..."}]
  }
}
```

## Why

ComfyUI has a built-in API (`POST /prompt`, `GET /history`) but lacks push notifications. This node fills that gap - place it at the end of any workflow to get results pushed to you instead of polling.

## Supports

- Images (PIL/torch tensor -> PNG -> base64)
- Text (string passthrough)
- Audio (torchaudio -> WAV -> base64)
