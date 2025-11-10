from __future__ import annotations

import os
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet  # type: ignore

from .config import Config


def _key_from_password(password: str) -> bytes:
    # Simplified: in production derive with PBKDF2; for demo, pad/truncate to 32 bytes base64
    import base64, hashlib
    h = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(h)


def backup_all(cfg: Config, password: str, out_dir: Optional[Path] = None) -> Path:
    ts = datetime.now().strftime("%Y%m%d")
    out_base = (out_dir or cfg.logs_dir.parent) / f"backup-{ts}"
    tmp_tar = out_base.with_suffix(".tar")
    with tarfile.open(tmp_tar, "w") as tar:
        tar.add(cfg.logs_dir, arcname="logs")
        if cfg.proofs_dir:
            tar.add(cfg.proofs_dir, arcname="Proofs")
        tar.add(cfg.reports_dir, arcname="reports")
    key = _key_from_password(password)
    f = Fernet(key)
    data = tmp_tar.read_bytes()
    enc_path = out_base.with_suffix(".bin")
    enc_path.write_bytes(f.encrypt(data))
    tmp_tar.unlink(missing_ok=True)
    return enc_path


def restore_backup(cfg: Config, enc_file: Path, password: str, dest: Optional[Path] = None) -> Path:
    key = _key_from_password(password)
    f = Fernet(key)
    dec = f.decrypt(enc_file.read_bytes())
    tmp_tar = enc_file.with_suffix(".restored.tar")
    tmp_tar.write_bytes(dec)
    with tarfile.open(tmp_tar, "r") as tar:
        tar.extractall(path=(dest or cfg.logs_dir.parent))
    tmp_tar.unlink(missing_ok=True)
    return dest or cfg.logs_dir.parent


