
import os
import re
import base64
import requests

from pathlib import Path
from dotenv import load_dotenv


load_dotenv()

MODEL_ID = "@cf/black-forest-labs/flux-1-schnell"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "generated_mudras"


class CloudflareImageGenerator:

    def __init__(self):

        self.account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.api_token = os.getenv("CLOUDFLARE_API_TOKEN")

        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not self.account_id or not self.api_token:
            raise ValueError(
                "Cloudflare credentials are missing. "
                "Check CLOUDFLARE_ACCOUNT_ID and "
                "CLOUDFLARE_API_TOKEN in your .env file."
            )

        self.api_url = (
            f"https://api.cloudflare.com/client/v4/accounts/"
            f"{self.account_id}/ai/run/{MODEL_ID}"
        )

    @staticmethod
    def _slugify(mudra_name):

        slug = re.sub(
            r"[^a-z0-9]+",
            "_",
            mudra_name.lower()
        ).strip("_")

        if not slug:
            raise ValueError("Invalid mudra name.")

        return slug



    def generate_image(self, mudra_name):

        # First, use a neutral educational illustration prompt.
        prompt = (
            f"Create an educational line-art diagram of the "
            f"{mudra_name} hand gesture used in Indian classical dance. "
            "Show a single stylized hand shape, from wrist to fingertips. "
            "Make every finger position clearly distinguishable. "
            "Use a front-facing view, a plain white background, "
            "clean outlines and a simple instructional illustration style."
        )

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        def send_request(prompt_text):

            payload = {
                "prompt": prompt_text,
                "steps": 4
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=180
            )

            try:
                data = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError(
                    "Cloudflare returned an invalid response."
                )

            if not response.ok:
                errors = data.get("errors", [])

                raise RuntimeError(
                    f"Cloudflare API error "
                    f"({response.status_code}): {errors}"
                )

            image_data = data.get("result", {}).get("image")

            if not image_data:
                raise RuntimeError(
                    "Cloudflare did not return an image."
                )

            return image_data

        try:

            # First generation attempt.
            image_base64 = send_request(prompt)

        except RuntimeError as exc:

            error_text = str(exc)

            # Retry only when Cloudflare specifically reports
            # the NSFW moderation error.
            if "8007" not in error_text:
                raise

            print(
                "Cloudflare rejected the first prompt. "
                "Trying a simpler educational prompt."
            )

            fallback_prompt = (
                f"An educational diagram illustrating the "
                f"{mudra_name} gesture. "
                "One simple hand illustration, clear finger arrangement, "
                "plain white background, clean instructional line art."
            )

            # One retry only. Do not retry indefinitely.
            image_base64 = send_request(fallback_prompt)

        # Decode the generated image.
        image_bytes = base64.b64decode(
            image_base64,
            validate=True
        )

        filename = self._slugify(mudra_name) + ".jpg"

        image_path = self.output_dir / filename

        temporary_path = image_path.with_suffix(".tmp")

        try:

            with open(temporary_path, "wb") as image_file:
                image_file.write(image_bytes)

            os.replace(temporary_path, image_path)

        finally:

            if temporary_path.exists():
                temporary_path.unlink()

        print(f"Generated image saved: {image_path}")

        return str(image_path)
