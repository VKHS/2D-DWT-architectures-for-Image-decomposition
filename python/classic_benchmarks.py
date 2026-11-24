"""Batch classic benchmark workflow: local files only, exact Q6 oracle and plots."""
import argparse
import csv
import hashlib
from pathlib import Path
import sys
import numpy as np
from PIL import Image
from gallery import draw
from dwt import METHODS, forward, decompose, reconstruct

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hardware"))
from golden import q6

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--directory", type=Path, required=True)
    p.add_argument("--size", type=int, default=256)
    p.add_argument("--out", type=Path, default=Path("outputs/classic"))
    a = p.parse_args()
    if a.size < 8 or a.size % 8:
        p.error("size must be a positive multiple of 8")
    if not a.directory.is_dir():
        p.error("supply a directory of local benchmark images")
    paths = sorted(f for f in a.directory.iterdir()
                   if f.is_file() and f.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".pgm"})
    if not paths:
        p.error("no supported image files found")
    a.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, path in enumerate(paths):
        label = f"{i:02d}_{path.stem}"
        out = a.out / label
        out.mkdir(exist_ok=True)
        with Image.open(path) as im:
            x = np.asarray(im.convert("L").resize((a.size, a.size), Image.Resampling.BOX), dtype=np.int64)
        ref = q6(x)
        for method in METHODS:
            np.testing.assert_array_equal(64 * forward(x, method), ref)
        c = decompose(x, 3, "fir")
        z = reconstruct(c, 3)
        draw(label, x / 255.0, out)
        (out / "pixels.hex").write_text("".join(f"{v:02x}\n" for v in x.ravel()))
        (out / "golden_q6.hex").write_text("".join(f"{int(v)&0xffffffff:08x}\n" for v in ref.ravel()))
        rows.append([path.name, hashlib.sha256(path.read_bytes()).hexdigest(), a.size,
                     "PIL L + BOX square resize", len(METHODS), float(np.max(abs(z-x))),
                     float(np.sqrt(np.mean((z-x)**2))), 64, "software only"])
    with (a.out / "manifest.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["source", "sha256", "size", "preprocessing", "methods_exact_q6",
                    "max_reconstruction_error", "rmse", "q6_scale", "validation_scope"])
        w.writerows(rows)
if __name__ == "__main__":
    main()
