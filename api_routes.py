"""
API Routes - Auto-registered on ComfyUI's web server when node is installed.

Endpoints:
  POST /api/bridge/run              Submit workflow JSON + text, wait for result
  POST /api/bridge/submit           Submit workflow JSON + text, return immediately
  GET  /api/bridge/status/{id}      Get result for a prompt_id
  GET  /api/bridge/health           Health check + queue info

Usage (from anywhere):
  curl -X POST https://your-comfyui-url/api/bridge/run \
    -H "Content-Type: application/json" \
    -d '{"workflow": {...}, "text": "A cute cat"}'
"""

import json
import uuid
import time
import asyncio
from aiohttp import web

try:
    import server as comfy_server
    import execution

    routes = comfy_server.PromptServer.instance.routes

    @routes.post('/api/bridge/run')
    async def bridge_run(request):
        """Submit workflow and wait for result (synchronous)."""
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        workflow = data.get("workflow") or data.get("prompt")
        text = data.get("text")
        timeout = data.get("timeout", 300)

        if not workflow:
            return web.json_response({"error": "Missing 'workflow' field"}, status=400)

        # Inject text into first text node
        if text:
            _inject_text(workflow, text)

        # Submit to queue
        prompt_id = str(uuid.uuid4())
        try:
            valid = execution.validate_prompt(workflow)
            if not valid[0]:
                return web.json_response({
                    "error": "Invalid workflow",
                    "details": valid[1] if len(valid) > 1 else "Validation failed"
                }, status=400)
        except Exception as e:
            return web.json_response({"error": f"Validation error: {e}"}, status=400)

        outputs_to_execute = valid[2] if len(valid) > 2 else []
        comfy_server.PromptServer.instance.prompt_queue.put(
            (0, prompt_id, workflow, {}, outputs_to_execute)
        )

        # Poll for completion
        start = time.time()
        while time.time() - start < timeout:
            history = comfy_server.PromptServer.instance.prompt_queue.get_history(prompt_id=prompt_id)
            if prompt_id in history:
                entry = history[prompt_id]
                if "outputs" in entry:
                    return web.json_response({
                        "prompt_id": prompt_id,
                        "status": "completed",
                        "outputs": _clean_outputs(entry["outputs"])
                    })
            await asyncio.sleep(2)

        return web.json_response({
            "prompt_id": prompt_id,
            "status": "timeout",
            "error": f"Not completed within {timeout}s"
        }, status=408)

    @routes.post('/api/bridge/submit')
    async def bridge_submit(request):
        """Submit workflow and return immediately (async)."""
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        workflow = data.get("workflow") or data.get("prompt")
        text = data.get("text")

        if not workflow:
            return web.json_response({"error": "Missing 'workflow' field"}, status=400)

        if text:
            _inject_text(workflow, text)

        prompt_id = str(uuid.uuid4())
        try:
            valid = execution.validate_prompt(workflow)
            if not valid[0]:
                return web.json_response({
                    "error": "Invalid workflow",
                    "details": valid[1] if len(valid) > 1 else "Validation failed"
                }, status=400)
        except Exception as e:
            return web.json_response({"error": f"Validation error: {e}"}, status=400)

        outputs_to_execute = valid[2] if len(valid) > 2 else []
        comfy_server.PromptServer.instance.prompt_queue.put(
            (0, prompt_id, workflow, {}, outputs_to_execute)
        )

        return web.json_response({
            "prompt_id": prompt_id,
            "status": "queued"
        })

    @routes.get('/api/bridge/status/{prompt_id}')
    async def bridge_status(request):
        """Check execution result for a prompt_id."""
        prompt_id = request.match_info["prompt_id"]
        history = comfy_server.PromptServer.instance.prompt_queue.get_history(prompt_id=prompt_id)

        if prompt_id not in history:
            return web.json_response({
                "prompt_id": prompt_id,
                "status": "running"
            })

        entry = history[prompt_id]
        if "outputs" in entry:
            return web.json_response({
                "prompt_id": prompt_id,
                "status": "completed",
                "outputs": _clean_outputs(entry["outputs"])
            })

        return web.json_response({
            "prompt_id": prompt_id,
            "status": "running"
        })

    @routes.get('/api/bridge/health')
    async def bridge_health(request):
        """Health check with queue info."""
        queue = comfy_server.PromptServer.instance.prompt_queue
        current = queue.get_current_queue()
        return web.json_response({
            "status": "ok",
            "running": len(current[0]) if current[0] else 0,
            "pending": len(current[1]) if current[1] else 0,
        })

    def _inject_text(workflow, text):
        """Find first text input node and set its value."""
        text_classes = ["CLIPTextEncode", "String", "Text", "ShowText", "CR Text"]
        for node_id, node in workflow.items():
            class_type = node.get("class_type", "")
            inputs = node.get("inputs", {})
            for cls_hint in text_classes:
                if cls_hint.lower() in class_type.lower():
                    for key in ["text", "string", "value"]:
                        if key in inputs and isinstance(inputs[key], str):
                            inputs[key] = text
                            return
        for node_id, node in workflow.items():
            inputs = node.get("inputs", {})
            for key, val in inputs.items():
                if isinstance(val, str) and key in ["text", "string", "prompt", "positive"]:
                    inputs[key] = text
                    return

    def _clean_outputs(outputs):
        """Convert outputs to a clean serializable dict."""
        result = {}
        for node_id, node_out in outputs.items():
            clean = {}
            if "images" in node_out:
                clean["images"] = [
                    {"filename": img.get("filename", ""), "subfolder": img.get("subfolder", ""),
                     "type": img.get("type", "output")}
                    for img in node_out["images"]
                ]
            if "gifs" in node_out:
                clean["videos"] = [
                    {"filename": vid.get("filename", ""), "subfolder": vid.get("subfolder", ""),
                     "type": vid.get("type", "output")}
                    for vid in node_out["gifs"]
                ]
            if "text" in node_out:
                clean["text"] = node_out["text"]
            if clean:
                result[node_id] = clean
        return result

    print("[API Bridge] Routes registered:")
    print("[API Bridge]   POST /api/bridge/run")
    print("[API Bridge]   POST /api/bridge/submit")
    print("[API Bridge]   GET  /api/bridge/status/{prompt_id}")
    print("[API Bridge]   GET  /api/bridge/health")

except Exception as e:
    print(f"[API Bridge] Failed to register routes: {e}")
    print("[API Bridge] WebhookCallback node still works, but API routes are unavailable.")
