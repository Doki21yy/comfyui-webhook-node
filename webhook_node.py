"""
WebhookCallback node - POSTs workflow results to a callback URL.
Supports images, text, audio output.
"""
import json
import os
import base64
import urllib.request
import urllib.error
import folder_paths


class WebhookCallback:
    CATEGORY = "api-bridge"
    FUNCTION = "execute"
    OUTPUT_NODE = True
    RETURN_TYPES = ()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "webhook_url": ("STRING", {"default": "", "multiline": False}),
                "task_id": ("STRING", {"default": "", "multiline": False}),
            },
            "optional": {
                "images": ("IMAGE",),
                "text": ("STRING", {"forceInput": True}),
                "audio": ("AUDIO",),
            },
        }

    def execute(self, webhook_url, task_id, images=None, text=None, audio=None):
        if not webhook_url:
            print("[WebhookCallback] No webhook_url, skipping")
            return {}

        payload = {"task_id": task_id, "status": "completed", "outputs": {}}

        if images is not None:
            import numpy as np
            from PIL import Image
            import io
            results = []
            output_dir = folder_paths.get_output_directory()
            for i, image in enumerate(images):
                arr = (image.cpu().numpy() * 255).astype(np.uint8)
                pil_img = Image.fromarray(arr)
                fname = f"webhook_{task_id}_{i:04d}.png"
                pil_img.save(os.path.join(output_dir, fname))
                buf = io.BytesIO()
                pil_img.save(buf, format="PNG")
                results.append({"filename": fname, "type": "image/png",
                                "base64": base64.b64encode(buf.getvalue()).decode()})
            payload["outputs"]["images"] = results

        if text is not None:
            payload["outputs"]["text"] = text

        if audio is not None:
            try:
                import torchaudio
                output_dir = folder_paths.get_output_directory()
                fname = f"webhook_{task_id}_audio.wav"
                waveform = audio["waveform"].squeeze(0)
                torchaudio.save(os.path.join(output_dir, fname), waveform, audio["sample_rate"])
                with open(os.path.join(output_dir, fname), "rb") as f:
                    payload["outputs"]["audio"] = [{"filename": fname, "type": "audio/wav",
                                                     "base64": base64.b64encode(f.read()).decode()}]
            except Exception as e:
                print(f"[WebhookCallback] Audio error: {e}")

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(webhook_url, data=data,
                                         headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                print(f"[WebhookCallback] Sent -> {resp.status}")
        except Exception as e:
            print(f"[WebhookCallback] Failed: {e}")

        return {}


NODE_CLASS_MAPPINGS = {"WebhookCallback": WebhookCallback}
NODE_DISPLAY_NAME_MAPPINGS = {"WebhookCallback": "Webhook Callback (API Bridge)"}
