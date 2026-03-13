"""
ComfyUI API Bridge Node
Install: Copy this folder to ComfyUI/custom_nodes/comfyui-webhook-node/

Features:
  1. WebhookCallback output node (workflow result push)
  2. Auto-registers API routes on ComfyUI server:
     - POST /api/bridge/run      Submit workflow + wait for result
     - POST /api/bridge/submit   Submit workflow (async)
     - GET  /api/bridge/status/{prompt_id}  Check result
     - GET  /api/bridge/health   Health check
"""
from .webhook_node import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from . import api_routes  # Auto-register API routes on import

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
