"""Commit completed output files without replacing existing user files."""
import os
import re
import tempfile
from pathlib import Path
from typing import Callable


def safe_stem(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip().rstrip(". ")[:100]
    if not name:
        name = "output"
    if re.fullmatch(r"CON|PRN|AUX|NUL|COM[0-9¹²³]|LPT[0-9¹²³]", name.split(".")[0], re.I):
        name = "_" + name
    return name


def write_output(folder: Path, stem: str, extension: str, save: Callable[[Path], None]) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    target = None
    for number in range(1, 10001):
        suffix = "" if number == 1 else f" ({number})"
        candidate = folder / f"{safe_stem(stem)}{suffix}{extension}"
        try:
            fd = os.open(candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            continue
        os.close(fd)
        target = candidate
        break
    if target is None:
        raise ValueError("Too many conflicting filenames in the output folder.")
    temporary = None
    try:
        fd, name = tempfile.mkstemp(prefix=".local-pdf-", suffix=extension, dir=folder)
        os.close(fd)
        temporary = Path(name)
        save(temporary)
        os.replace(temporary, target)
        return target
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
