import os
import cv2
import numpy as np
from pathlib import Path


class AIUpscaler:
    """Wrapper AI Super-Resolution (FSRCNN .pb) untuk skala 1x, 2x, dan 3x."""    

    def __init__(self, models_dir=None):
        base_dir = Path(__file__).resolve().parent
        if models_dir is None:
            self.models_dir = base_dir / "models"
        else:
            self.models_dir = Path(models_dir).resolve()
        self._model_cache = {}

    def _resolve_model_path(self, scale: int) -> str:
        for filename in (f"FSRCNN_x{scale}.pb", f"fsrcnn_x{scale}.pb"):
            full_path = os.path.join(self.models_dir, filename)
            if os.path.exists(full_path):
                return full_path
        raise FileNotFoundError(
            f"File model FSRCNN skala {scale}x tidak ditemukan di: {self.models_dir}"
        )

    def _get_sr(self, scale: int):
        if scale not in (2, 3):
            raise ValueError(f"Skala AI tidak didukung: {scale}x (pilih 2 atau 3)")

        if scale in self._model_cache:
            return self._model_cache[scale]

        if not hasattr(cv2, "dnn_superres"):
            raise RuntimeError(
                "Modul cv2.dnn_superres tidak ditemukan. "
                "Pastikan 'opencv-contrib-python' terpasang."
            )

        model_path = self._resolve_model_path(scale)
        sr = cv2.dnn_superres.DnnSuperResImpl_create()

        print("MODEL PATH:", model_path)
        print("MODEL EXISTS:", os.path.isfile(model_path))
        print(
            "MODEL SIZE:",
            os.path.getsize(model_path) if os.path.isfile(model_path) else 0
        )

        sr.readModel(model_path)
        sr.setModel("fsrcnn", scale)
        self._model_cache[scale] = sr
        return sr

    def upscale_image(self, image_bgr: np.ndarray, scale: int) -> np.ndarray:
        """Naikkan resolusi satu frame BGR (scale: 1, 2, atau 3)."""
        if scale == 1:
            return image_bgr.copy()

        if image_bgr.ndim == 3 and image_bgr.shape[2] == 4:
            image_bgr = cv2.cvtColor(image_bgr, cv2.COLOR_BGRA2BGR)

        sr = self._get_sr(scale)
        return sr.upsample(image_bgr)

    def upscale_batch(self, images_bgr: list, scale: int, progress_callback=None) -> list:
        """Proses seluruh foto dalam sesi sekaligus."""
        results = []
        total = len(images_bgr)
        for idx, img in enumerate(images_bgr):
            upscaled = self.upscale_image(img, scale)
            results.append(upscaled)
            if progress_callback:
                progress_callback(idx + 1, total)
        return results