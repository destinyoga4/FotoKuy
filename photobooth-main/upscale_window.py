import threading
import customtkinter as ctk
from tkinter import messagebox
import cv2
from PIL import Image

from upscale_engine import AIUpscaler

# Palet warna diselaraskan dengan app.py
ACCENT = "#f0627b"
ACCENT_HOVER = "#ff7f96"
BG_DARK = "#0b1220"
BG_MID = "#111c31"
BG_CARD = "#17243b"
BG_SURFACE = "#1d2d48"
BORDER = "#2b4163"
FG_TEXT = "#f4f7fb"
FG_MUTED = "#91a2bb"
GREEN = "#34d3ad"
ORANGE = "#f6b756"


class UpscaleWindow(ctk.CTkToplevel):
    """Window review foto mentah + pilihan AI Super-Resolution (1x / 2x / 3x)."""

    def __init__(self, master, raw_photos_bgr, on_confirm, on_cancel=None):
        super().__init__(master)
        self.raw_photos_bgr = raw_photos_bgr
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.upscaler = AIUpscaler()

        self._processing = False
        self._completed = False
        self._photo_refs = []
        self.scale_var = ctk.IntVar(value=2)

        self.title("Review Foto & AI Upscale")
        self.geometry("1040x680")
        self.minsize(820, 560)
        self.configure(fg_color=BG_DARK)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._handle_close)

        self._build_ui()
        self._update_resolution_info()

    def _build_ui(self):
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color=BG_MID, corner_radius=0, height=74)
        header.pack(fill="x")
        header.pack_propagate(False)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", padx=24, pady=12)

        ctk.CTkLabel(
            title_box,
            text="TAHAP 2  •  PENINGKATAN KUALITAS FOTO",
            font=("Segoe UI", 10, "bold"),
            text_color=GREEN,
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="✨  Preview Jepretan Mentah & AI Upscale",
            font=("Segoe UI", 19, "bold"),
            text_color=FG_TEXT,
        ).pack(anchor="w")

        # ── Area Preview Foto Mentah ──
        preview_wrapper = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
        )
        preview_wrapper.pack(fill="both", expand=True, padx=24, pady=(16, 12))

        ctk.CTkLabel(
            preview_wrapper,
            text=f"Hasil jepretan mentah ({len(self.raw_photos_bgr)} foto) — skala pilihan akan diterapkan ke semua foto:",
            font=("Segoe UI", 12),
            text_color=FG_MUTED,
        ).pack(anchor="w", padx=18, pady=(14, 6))

        self.photos_scroll = ctk.CTkScrollableFrame(
            preview_wrapper,
            fg_color="transparent",
            orientation="horizontal",
        )
        self.photos_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._render_raw_photos()

        # ── Panel Kontrol Skala (1x / 2x / 3x) ──
        control_card = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
        )
        control_card.pack(fill="x", padx=24, pady=(0, 20))

        left_ctrl = ctk.CTkFrame(control_card, fg_color="transparent")
        left_ctrl.pack(side="left", padx=20, pady=16)

        ctk.CTkLabel(
            left_ctrl,
            text="Pilih Skala AI Super-Resolution (FSRCNN):",
            font=("Segoe UI", 13, "bold"),
            text_color=FG_TEXT,
        ).pack(anchor="w", pady=(0, 8))

        radio_row = ctk.CTkFrame(left_ctrl, fg_color="transparent")
        radio_row.pack(anchor="w")

        options = [
            (1, "1x (Asli / Tanpa Upscale)"),
            (2, "2x (AI HD — Cepat & Tajam)"),
            (3, "3x (AI Ultra — Detail Maksimal)"),
        ]
        for val, label in options:
            rb = ctk.CTkRadioButton(
                radio_row,
                text=label,
                variable=self.scale_var,
                value=val,
                command=self._update_resolution_info,
                font=("Segoe UI", 12, "bold"),
                text_color=FG_TEXT,
                fg_color=ACCENT,
                hover_color=ACCENT_HOVER,
                border_color=BORDER,
            )
            rb.pack(side="left", padx=(0, 22))

        self.res_info_label = ctk.CTkLabel(
            left_ctrl,
            text="",
            font=("Segoe UI", 11),
            text_color=GREEN,
        )
        self.res_info_label.pack(anchor="w", pady=(8, 0))

        # ── Tombol Aksi Kanan ──
        right_ctrl = ctk.CTkFrame(control_card, fg_color="transparent")
        right_ctrl.pack(side="right", padx=20, pady=16)

        self.status_label = ctk.CTkLabel(
            right_ctrl,
            text="Siap diproses",
            font=("Segoe UI", 11),
            text_color=FG_MUTED,
        )
        self.status_label.pack(anchor="e", pady=(0, 6))

        self.proceed_btn = ctk.CTkButton(
            right_ctrl,
            text="🚀  Proses & Masuk ke Template",
            command=self._start_upscale,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            font=("Segoe UI", 13, "bold"),
            height=42,
            width=240,
            corner_radius=10,
        )
        self.proceed_btn.pack(anchor="e")

    def _render_raw_photos(self):
        for idx, bgr in enumerate(self.raw_photos_bgr):
            card = ctk.CTkFrame(
                self.photos_scroll,
                fg_color=BG_SURFACE,
                corner_radius=12,
                border_width=1,
                border_color=BORDER,
            )
            card.pack(side="left", padx=8, pady=6, fill="y")

            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            orig_w, orig_h = pil_img.size

            thumb = pil_img.copy()
            thumb.thumbnail((250, 280), Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=thumb.size)
            self._photo_refs.append(ctk_img)

            ctk.CTkLabel(card, text="", image=ctk_img).pack(padx=10, pady=(10, 6))
            ctk.CTkLabel(
                card,
                text=f"Foto #{idx + 1}  •  {orig_w}×{orig_h} px",
                font=("Segoe UI", 11, "bold"),
                text_color=FG_TEXT,
            ).pack(pady=(0, 10))

    def _update_resolution_info(self):
        if not self.raw_photos_bgr:
            return
        h, w = self.raw_photos_bgr[0].shape[:2]
        scale = self.scale_var.get()
        if scale == 1:
            self.res_info_label.configure(
                text=f"Resolusi tetap: {w}×{h} px (langsung masuk ke template tanpa AI upscale)",
                text_color=FG_MUTED,
            )
        else:
            self.res_info_label.configure(
                text=f"Estimasi resolusi baru: {w}×{h} px  →  {w * scale}×{h * scale} px per foto",
                text_color=GREEN,
            )

    def _start_upscale(self):
        if self._processing:
            return
        self._processing = True
        scale = self.scale_var.get()

        self.proceed_btn.configure(state="disabled", text="⏳  Memproses AI...")
        self.status_label.configure(
            text=f"Menjalankan AI FSRCNN {scale}x pada {len(self.raw_photos_bgr)} foto...",
            text_color=ORANGE,
        )

        def _worker():
            try:
                def _on_progress(done, total):
                    self.after(
                        0,
                        lambda d=done, t=total: self.status_label.configure(
                            text=f"Memproses foto {d}/{t} (skala {scale}x)..."
                        ),
                    )

                upscaled = self.upscaler.upscale_batch(
                    self.raw_photos_bgr, scale, progress_callback=_on_progress
                )
                self.after(0, lambda: self._finish_success(upscaled, scale))
            except Exception as exc:
                self.after(0, lambda e=exc: self._finish_error(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _finish_success(self, upscaled_photos, scale):
        self._processing = False
        self._completed = True
        self.grab_release()
        self.destroy()
        if self.on_confirm:
            self.on_confirm(upscaled_photos, scale)

    def _finish_error(self, error):
        self._processing = False
        self.proceed_btn.configure(state="normal", text="🚀  Proses & Masuk ke Template")
        self.status_label.configure(text="❌ Gagal melakukan upscale", text_color=ACCENT)
        messagebox.showerror("AI Upscale Gagal", f"Terjadi kesalahan saat upscale:\n{error}")

    def _handle_close(self):
        if self._processing:
            return
        self.grab_release()
        self.destroy()
        if not self._completed and self.on_cancel:
            self.on_cancel()