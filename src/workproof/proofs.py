from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pyautogui  # type: ignore
from PIL import Image, ImageDraw, ImageFilter  # type: ignore

from .config import Config
from .database import LogRecord, insert_log
from .utils.platform_adapters import get_active_window_title

LOGGER = logging.getLogger(__name__)


@dataclass
class ProofOptions:
    blur_radius: int
    watermark: bool


def capture_proof(cfg: Config, opts: ProofOptions | None = None) -> Path | None:
    try:
        ts = datetime.now(timezone.utc)
        day_dir = (cfg.proofs_dir or cfg.reports_dir).joinpath(ts.strftime("%Y-%m-%d"))
        day_dir.mkdir(parents=True, exist_ok=True)
        active_app = get_active_window_title() or "Unknown"
        base = f"{ts.strftime('%H-%M-%S')}__{active_app.replace(' ','_')}"
        img_path = day_dir / f"{base}.png"
        meta_path = day_dir / f"{base}.json"
        img = pyautogui.screenshot()
        if opts is None:
            opts = ProofOptions(cfg.proof_blur_radius, cfg.proof_watermark)
        if opts.blur_radius > 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=opts.blur_radius))
        if opts.watermark:
            d = ImageDraw.Draw(img)
            d.text((10, 10), "WorkProof — Local Only", fill=(255, 255, 255))
        img.save(str(img_path))
        meta = {
            "timestamp": ts.isoformat(),
            "active_app": active_app,
            "screen_size": img.size,
            "blur_radius": opts.blur_radius,
            "watermark": opts.watermark,
            "path": str(img_path),
        }
        meta_path.write_text(json.dumps(meta), encoding="utf-8")
        insert_log(cfg.db_path, LogRecord(
            timestamp=ts, active_app=active_app, running_apps="[]", idle_seconds=0,
            project_path=None, event_type="proof_capture", meta=json.dumps({"path": str(img_path)})
        ))
        LOGGER.info("Proof captured: %s", img_path)
        return img_path
    except Exception as e:
        LOGGER.warning("Proof capture failed: %s", e)
        return None


