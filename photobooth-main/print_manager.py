import ctypes
import ctypes.wintypes as wt
import logging
import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from PIL import Image, ImageTk

if sys.platform == "win32":
    from PIL import ImageWin
else:
    ImageWin = None


BG = "#0b1220"
SURFACE = "#111c31"
CARD = "#17243b"
SURFACE_HOVER = "#2b4163"
BORDER = "#2b4163"
TEXT = "#f4f7fb"
MUTED = "#91a2bb"
ACCENT = "#f0627b"
ACCENT_HOVER = "#ff7f96"
GREEN = "#34d3ad"
ORANGE = "#f6b756"
BLUE = "#60a5fa"

# Konstanta Win32 GDI & Print Spooler
PRINTER_ENUM_LOCAL = 0x00000002
PRINTER_ENUM_CONNECTIONS = 0x00000004
HORZRES = 8
VERTRES = 10
LOGPIXELSX = 88
LOGPIXELSY = 90

MIN_COPIES = 1
MAX_COPIES = 10


class PrintError(RuntimeError):
    """Error yang ramah pengguna saat proses cetak gagal."""


class _PRINTER_INFO_4W(ctypes.Structure):
    _fields_ = [
        ("pPrinterName", wt.LPWSTR),
        ("pServerName", wt.LPWSTR),
        ("Attributes", wt.DWORD),
    ]


class _DOCINFOW(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_int),
        ("lpszDocName", wt.LPCWSTR),
        ("lpszOutput", wt.LPCWSTR),
        ("lpszDatatype", wt.LPCWSTR),
        ("fwType", wt.DWORD),
    ]


def _load_win32_apis():
    """Muat API winspool.drv dan gdi32.dll dengan tipe argumen/hasil 64-bit aman."""
    if sys.platform != "win32":
        raise PrintError("Fitur cetak langsung hanya didukung di sistem operasi Windows.")

    winspool = ctypes.WinDLL("winspool.drv", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32.dll", use_last_error=True)

    winspool.EnumPrintersW.argtypes = [
        wt.DWORD,
        wt.LPWSTR,
        wt.DWORD,
        ctypes.c_void_p,
        wt.DWORD,
        ctypes.POINTER(wt.DWORD),
        ctypes.POINTER(wt.DWORD),
    ]
    winspool.EnumPrintersW.restype = wt.BOOL

    winspool.GetDefaultPrinterW.argtypes = [
        wt.LPWSTR,
        ctypes.POINTER(wt.DWORD),
    ]
    winspool.GetDefaultPrinterW.restype = wt.BOOL

    gdi32.CreateDCW.argtypes = [
        wt.LPCWSTR,
        wt.LPCWSTR,
        wt.LPCWSTR,
        ctypes.c_void_p,
    ]
    gdi32.CreateDCW.restype = wt.HDC

    gdi32.DeleteDC.argtypes = [wt.HDC]
    gdi32.DeleteDC.restype = wt.BOOL

    gdi32.GetDeviceCaps.argtypes = [wt.HDC, ctypes.c_int]
    gdi32.GetDeviceCaps.restype = ctypes.c_int

    gdi32.StartDocW.argtypes = [wt.HDC, ctypes.POINTER(_DOCINFOW)]
    gdi32.StartDocW.restype = ctypes.c_int

    gdi32.EndDoc.argtypes = [wt.HDC]
    gdi32.EndDoc.restype = ctypes.c_int

    gdi32.AbortDoc.argtypes = [wt.HDC]
    gdi32.AbortDoc.restype = ctypes.c_int

    gdi32.StartPage.argtypes = [wt.HDC]
    gdi32.StartPage.restype = ctypes.c_int

    gdi32.EndPage.argtypes = [wt.HDC]
    gdi32.EndPage.restype = ctypes.c_int

    return winspool, gdi32


def get_default_printer() -> str | None:
    """Ambil nama printer default Windows, atau None jika belum diatur."""
    if sys.platform != "win32":
        return None
    try:
        winspool, _ = _load_win32_apis()
        needed = wt.DWORD(0)
        winspool.GetDefaultPrinterW(None, ctypes.byref(needed))
        if needed.value <= 1:
            return None
        buf = ctypes.create_unicode_buffer(needed.value)
        if winspool.GetDefaultPrinterW(buf, ctypes.byref(needed)):
            name = buf.value.strip()
            return name or None
    except Exception:
        logging.exception("Gagal membaca printer default Windows")
    return None


def list_printers() -> list[str]:
    """Kembalikan daftar printer yang dikenali Windows (default printer di urutan pertama)."""
    if sys.platform != "win32":
        return []

    winspool, _ = _load_win32_apis()
    flags = PRINTER_ENUM_LOCAL | PRINTER_ENUM_CONNECTIONS
    needed = wt.DWORD(0)
    returned = wt.DWORD(0)

    winspool.EnumPrintersW(flags, None, 4, None, 0, ctypes.byref(needed), ctypes.byref(returned))
    printers: list[str] = []
    if needed.value > 0:
        buf = ctypes.create_string_buffer(needed.value)
        ok = winspool.EnumPrintersW(
            flags, None, 4, buf, needed.value, ctypes.byref(needed), ctypes.byref(returned)
        )
        if ok and returned.value > 0:
            entries = ctypes.cast(buf, ctypes.POINTER(_PRINTER_INFO_4W))
            seen = set()
            for idx in range(returned.value):
                name = (entries[idx].pPrinterName or "").strip()
                if name and name not in seen:
                    seen.add(name)
                    printers.append(name)

    default_name = get_default_printer()
    if default_name:
        if default_name in printers:
            printers.remove(default_name)
        printers.insert(0, default_name)

    return printers


def calculate_print_layout(
    img_size: tuple[int, int],
    printable_size: tuple[int, int],
    dpi: tuple[int, int] = (300, 300),
    auto_rotate: bool = True,
) -> tuple[bool, tuple[int, int, int, int]]:
    """
    Hitung apakah gambar perlu diputar 90° dan koordinat kotak cetak (x0, y0, x1, y1)
    agar gambar proporsional, terpusat, dan maksimal di area cetak kertas.
    """
    img_w, img_h = img_size
    page_w, page_h = printable_size
    dpi_x = max(1, int(dpi[0] or 300))
    dpi_y = max(1, int(dpi[1] or 300))

    if img_w <= 0 or img_h <= 0:
        raise ValueError("Dimensi gambar tidak valid.")
    if page_w <= 0 or page_h <= 0:
        raise ValueError("Dimensi area cetak printer tidak valid.")

    # Dimensi fisik kertas dalam inci untuk cek orientasi sebenarnya
    phys_w = page_w / dpi_x
    phys_h = page_h / dpi_y

    rotate = bool(auto_rotate and ((img_w > img_h) != (phys_w > phys_h)))
    eff_w, eff_h = (img_h, img_w) if rotate else (img_w, img_h)

    # Skala dalam satuan fisik (inci) agar tetap proporsional meski DPI X != DPI Y
    scale = min(phys_w / eff_w, phys_h / eff_h)
    draw_w = max(1, int(round(eff_w * scale * dpi_x)))
    draw_h = max(1, int(round(eff_h * scale * dpi_y)))

    draw_w = min(draw_w, page_w)
    draw_h = min(draw_h, page_h)

    x0 = (page_w - draw_w) // 2
    y0 = (page_h - draw_h) // 2
    return rotate, (x0, y0, x0 + draw_w, y0 + draw_h)


def _prepare_rgb_image(image_path: str) -> Image.Image:
    """Buka gambar dan pastikan berformat RGB dengan latar putih jika transparan."""
    with Image.open(image_path) as raw:
        if raw.mode in ("RGBA", "LA") or (raw.mode == "P" and "transparency" in raw.info):
            rgba = raw.convert("RGBA")
            background = Image.new("RGB", rgba.size, (255, 255, 255))
            background.paste(rgba, mask=rgba.split()[-1])
            return background
        return raw.convert("RGB")


def print_image(
    image_path: str,
    printer_name: str | None = None,
    copies: int = 1,
    doc_name: str = "Fotoskuy Photobooth",
    auto_rotate: bool = True,
    output_path: str | None = None,
) -> dict:
    """
    Cetak file gambar langsung ke printer Windows menggunakan Win32 GDI + PIL.ImageWin.

    Mengembalikan dict ringkasan hasil cetak (printer, copies, rotated, dst_rect).
    """
    if not image_path or not os.path.exists(image_path):
        raise PrintError("File foto yang akan dicetak tidak ditemukan.")

    try:
        copies_int = int(copies)
    except (TypeError, ValueError) as exc:
        raise PrintError("Jumlah cetak harus berupa angka.") from exc
    if copies_int < MIN_COPIES or copies_int > MAX_COPIES:
        raise PrintError(f"Jumlah cetak harus antara {MIN_COPIES} sampai {MAX_COPIES} lembar.")

    if ImageWin is None:
        raise PrintError("Modul PIL.ImageWin hanya tersedia di Windows.")

    target_printer = (printer_name or "").strip() or get_default_printer()
    if not target_printer:
        raise PrintError(
            "Tidak ada printer yang tersedia.\n"
            "Pastikan printer sudah tersambung dan dikenali Windows."
        )

    _, gdi32 = _load_win32_apis()
    img = _prepare_rgb_image(image_path)

    hdc = gdi32.CreateDCW("WINSPOOL", target_printer, None, None)
    if not hdc:
        err_code = ctypes.get_last_error()
        raise PrintError(
            f"Gagal terhubung ke printer '{target_printer}' (kode {err_code}).\n"
            "Periksa koneksi dan status printer di Windows."
        )

    doc_started = False
    try:
        page_w = gdi32.GetDeviceCaps(hdc, HORZRES)
        page_h = gdi32.GetDeviceCaps(hdc, VERTRES)
        dpi_x = gdi32.GetDeviceCaps(hdc, LOGPIXELSX) or 300
        dpi_y = gdi32.GetDeviceCaps(hdc, LOGPIXELSY) or 300

        rotate, dst_rect = calculate_print_layout(
            img.size,
            (page_w, page_h),
            dpi=(dpi_x, dpi_y),
            auto_rotate=auto_rotate,
        )
        if rotate:
            img = img.transpose(Image.Transpose.ROTATE_90)

        dib = ImageWin.Dib(img)

        doc_info = _DOCINFOW()
        doc_info.cbSize = ctypes.sizeof(_DOCINFOW)
        doc_info.lpszDocName = doc_name
        doc_info.lpszOutput = output_path
        doc_info.lpszDatatype = None
        doc_info.fwType = 0

        if gdi32.StartDocW(hdc, ctypes.byref(doc_info)) <= 0:
            err_code = ctypes.get_last_error()
            raise PrintError(
                f"Printer '{target_printer}' menolak memulai dokumen cetak (kode {err_code})."
            )
        doc_started = True

        for page_idx in range(copies_int):
            if gdi32.StartPage(hdc) <= 0:
                err_code = ctypes.get_last_error()
                raise PrintError(
                    f"Gagal memulai halaman cetak ke-{page_idx + 1} (kode {err_code})."
                )
            dib.draw(hdc, dst_rect)
            if gdi32.EndPage(hdc) <= 0:
                err_code = ctypes.get_last_error()
                raise PrintError(
                    f"Gagal menyelesaikan halaman cetak ke-{page_idx + 1} (kode {err_code})."
                )

        if gdi32.EndDoc(hdc) <= 0:
            err_code = ctypes.get_last_error()
            raise PrintError(f"Gagal menutup antrean cetak (kode {err_code}).")
        doc_started = False

        logging.info(
            "Berhasil mengirim cetak ke '%s' (%dx, rotated=%s, rect=%s)",
            target_printer,
            copies_int,
            rotate,
            dst_rect,
        )
        return {
            "printer": target_printer,
            "copies": copies_int,
            "rotated": rotate,
            "dst_rect": dst_rect,
        }
    except Exception:
        if doc_started:
            try:
                gdi32.AbortDoc(hdc)
            except Exception:
                pass
        raise
    finally:
        gdi32.DeleteDC(hdc)


class PrintDialog:
    """Popup pemilihan printer dan jumlah cetak yang menyatu dengan tema Fotoskuy."""

    def __init__(
        self,
        parent: tk.Misc,
        image_path: str,
        on_status=None,
        on_close=None,
    ):
        self.parent = parent
        self.image_path = image_path
        self.on_status = on_status
        self.on_close = on_close

        self._printing = False
        self._closed = False
        self._thumb_tk = None
        self._printers: list[str] = []
        self._default_printer: str | None = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Print Foto")
        self.dialog.configure(bg=BG)
        self.dialog.transient(parent)
        self.dialog.resizable(False, False)
        self.dialog.protocol("WM_DELETE_WINDOW", self._handle_close)
        self.dialog.bind("<Escape>", lambda _event: self._handle_close())

        width, height = 500, 440
        parent.update_idletasks()
        try:
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            x = max(0, px + (pw - width) // 2)
            y = max(0, py + (ph - height) // 2)
        except Exception:
            sw = self.dialog.winfo_screenwidth()
            sh = self.dialog.winfo_screenheight()
            x = max(0, (sw - width) // 2)
            y = max(0, (sh - height) // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

        self.printer_var = tk.StringVar(value="")
        self.copies_var = tk.IntVar(value=1)

        self._build_ui()
        self._refresh_printers()

        self.dialog.grab_set()
        self.dialog.focus_force()

    def _build_ui(self):
        # ── Header ──
        header = tk.Frame(self.dialog, bg=SURFACE, height=68)
        header.pack(fill="x")
        header.pack_propagate(False)

        header_inner = tk.Frame(header, bg=SURFACE)
        header_inner.pack(fill="both", expand=True, padx=20, pady=10)
        tk.Label(
            header_inner,
            text="DIRECT PRINT",
            font=("Segoe UI", 9, "bold"),
            bg=SURFACE,
            fg=BLUE,
        ).pack(anchor="w")
        tk.Label(
            header_inner,
            text="🖨  Cetak Foto ke Printer",
            font=("Segoe UI", 16, "bold"),
            bg=SURFACE,
            fg=TEXT,
        ).pack(anchor="w")

        # ── Body ──
        body = tk.Frame(self.dialog, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=(14, 10))

        # Ringkasan foto mini
        info_card = tk.Frame(body, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        info_card.pack(fill="x", pady=(0, 12))

        try:
            with Image.open(self.image_path) as img:
                orig_w, orig_h = img.size
                thumb = img.copy()
                thumb.thumbnail((72, 72), Image.LANCZOS)
                self._thumb_tk = ImageTk.PhotoImage(thumb)
        except Exception:
            orig_w, orig_h = 0, 0
            self._thumb_tk = None

        if self._thumb_tk is not None:
            tk.Label(info_card, image=self._thumb_tk, bg=CARD).pack(side="left", padx=(10, 10), pady=8)

        meta_box = tk.Frame(info_card, bg=CARD)
        meta_box.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)
        tk.Label(
            meta_box,
            text=os.path.basename(self.image_path),
            font=("Segoe UI", 10, "bold"),
            bg=CARD,
            fg=TEXT,
            anchor="w",
        ).pack(fill="x")
        dim_text = f"Resolusi: {orig_w} × {orig_h} px  •  Auto-fit ke kertas" if orig_w else "Siap dicetak"
        tk.Label(
            meta_box,
            text=dim_text,
            font=("Segoe UI", 9),
            bg=CARD,
            fg=MUTED,
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        # Pilih Printer
        printer_card = tk.Frame(body, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        printer_card.pack(fill="x", pady=(0, 12))

        top_row = tk.Frame(printer_card, bg=CARD)
        top_row.pack(fill="x", padx=14, pady=(10, 4))
        tk.Label(
            top_row,
            text="Pilih Printer",
            font=("Segoe UI", 10, "bold"),
            bg=CARD,
            fg=TEXT,
        ).pack(side="left")
        self.refresh_btn = tk.Button(
            top_row,
            text="🔄 Refresh",
            command=self._refresh_printers,
            font=("Segoe UI", 9, "bold"),
            bg=SURFACE,
            fg=MUTED,
            activebackground=SURFACE_HOVER,
            activeforeground=TEXT,
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=2,
            bd=0,
        )
        self.refresh_btn.pack(side="right")

        style = ttk.Style(self.dialog)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Fotoskuy.TCombobox",
            fieldbackground=SURFACE,
            background=SURFACE_HOVER,
            foreground=TEXT,
            arrowcolor=TEXT,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            selectbackground=SURFACE_HOVER,
            selectforeground=TEXT,
        )

        self.printer_combo = ttk.Combobox(
            printer_card,
            textvariable=self.printer_var,
            state="readonly",
            font=("Segoe UI", 10),
            style="Fotoskuy.TCombobox",
        )
        self.printer_combo.pack(fill="x", padx=14, pady=(2, 4))
        self.printer_combo.bind("<<ComboboxSelected>>", lambda _e: self._update_printer_hint())

        self.printer_hint_label = tk.Label(
            printer_card,
            text="",
            font=("Segoe UI", 9),
            bg=CARD,
            fg=GREEN,
            anchor="w",
        )
        self.printer_hint_label.pack(fill="x", padx=14, pady=(0, 10))

        # Jumlah Cetak (Copies)
        copies_card = tk.Frame(body, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        copies_card.pack(fill="x", pady=(0, 8))

        copies_row = tk.Frame(copies_card, bg=CARD)
        copies_row.pack(fill="x", padx=14, pady=10)

        label_box = tk.Frame(copies_row, bg=CARD)
        label_box.pack(side="left", fill="x", expand=True)
        tk.Label(
            label_box,
            text="Jumlah Cetak (Copies)",
            font=("Segoe UI", 10, "bold"),
            bg=CARD,
            fg=TEXT,
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            label_box,
            text=f"Pilih {MIN_COPIES} sampai {MAX_COPIES} lembar",
            font=("Segoe UI", 9),
            bg=CARD,
            fg=MUTED,
            anchor="w",
        ).pack(fill="x")

        stepper = tk.Frame(copies_row, bg=CARD)
        stepper.pack(side="right")

        step_btn_style = {
            "font": ("Segoe UI", 13, "bold"),
            "bg": SURFACE,
            "fg": TEXT,
            "activebackground": SURFACE_HOVER,
            "activeforeground": TEXT,
            "relief": "flat",
            "cursor": "hand2",
            "width": 3,
            "bd": 0,
        }
        self.minus_btn = tk.Button(stepper, text="−", command=self._dec_copies, **step_btn_style)
        self.minus_btn.pack(side="left")

        self.copies_label = tk.Label(
            stepper,
            textvariable=self.copies_var,
            font=("Segoe UI", 14, "bold"),
            bg=BG,
            fg=GREEN,
            width=4,
            pady=3,
        )
        self.copies_label.pack(side="left", padx=6)

        self.plus_btn = tk.Button(stepper, text="+", command=self._inc_copies, **step_btn_style)
        self.plus_btn.pack(side="left")

        # Status
        self.status_label = tk.Label(
            body,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg=BG,
            fg=MUTED,
            anchor="w",
        )
        self.status_label.pack(fill="x", pady=(2, 0))

        # ── Footer Buttons ──
        footer = tk.Frame(self.dialog, bg=BG)
        footer.pack(fill="x", side="bottom", padx=20, pady=(4, 16))

        btn_common = {
            "font": ("Segoe UI", 10, "bold"),
            "relief": "flat",
            "cursor": "hand2",
            "padx": 14,
            "pady": 9,
            "bd": 0,
        }
        self.cancel_btn = tk.Button(
            footer,
            text="Tutup",
            command=self._handle_close,
            bg=SURFACE,
            fg=MUTED,
            activebackground=SURFACE_HOVER,
            activeforeground=TEXT,
            **btn_common,
        )
        self.cancel_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.print_btn = tk.Button(
            footer,
            text="🖨  Cetak Sekarang",
            command=self._start_print,
            bg=GREEN,
            fg=BG,
            activebackground="#57e0bd",
            activeforeground=BG,
            **btn_common,
        )
        self.print_btn.pack(side="left", fill="x", expand=True, padx=(6, 0))

    def _dec_copies(self):
        if self._printing:
            return
        self.copies_var.set(max(MIN_COPIES, self.copies_var.get() - 1))

    def _inc_copies(self):
        if self._printing:
            return
        self.copies_var.set(min(MAX_COPIES, self.copies_var.get() + 1))

    def _refresh_printers(self):
        if self._printing:
            return
        current = self.printer_var.get()
        try:
            self._printers = list_printers()
            self._default_printer = get_default_printer()
        except Exception as exc:
            logging.exception("Gagal membaca daftar printer")
            self._printers = []
            self._default_printer = None
            self.status_label.configure(text=f"⚠ Gagal membaca printer: {exc}", fg=ACCENT)

        self.printer_combo.configure(values=self._printers)
        if self._printers:
            if current in self._printers:
                self.printer_var.set(current)
            else:
                self.printer_var.set(self._printers[0])
            self.print_btn.configure(state="normal", bg=GREEN)
            self._update_printer_hint()
            self.status_label.configure(
                text=f"✓ {len(self._printers)} printer terdeteksi di Windows",
                fg=MUTED,
            )
        else:
            self.printer_var.set("")
            self.print_btn.configure(state="disabled", bg=SURFACE_HOVER)
            self.printer_hint_label.configure(
                text="⚠ Tidak ada printer terdeteksi. Sambungkan printer lalu klik Refresh.",
                fg=ORANGE,
            )
            self.status_label.configure(text="", fg=MUTED)

    def _update_printer_hint(self):
        selected = self.printer_var.get()
        if not selected:
            self.printer_hint_label.configure(text="", fg=MUTED)
            return
        if selected == self._default_printer:
            self.printer_hint_label.configure(text="★ Printer default Windows", fg=GREEN)
        else:
            self.printer_hint_label.configure(text="✓ Siap mencetak ke printer terpilih", fg=MUTED)

    def _set_controls_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.printer_combo.configure(state="readonly" if enabled else "disabled")
        self.refresh_btn.configure(state=state)
        self.minus_btn.configure(state=state)
        self.plus_btn.configure(state=state)
        self.cancel_btn.configure(state=state)
        if enabled and self._printers:
            self.print_btn.configure(state="normal", text="🖨  Cetak Sekarang", bg=GREEN)
        else:
            self.print_btn.configure(
                state="disabled",
                text="⏳  Mengirim ke Printer..." if not enabled else "🖨  Cetak Sekarang",
                bg=SURFACE_HOVER,
            )

    def _start_print(self):
        if self._printing or self._closed:
            return
        printer_name = self.printer_var.get().strip()
        if not printer_name:
            messagebox.showwarning("Printer Belum Dipilih", "Pilih printer terlebih dahulu.", parent=self.dialog)
            return
        copies = self.copies_var.get()

        self._printing = True
        self._set_controls_enabled(False)
        self.status_label.configure(
            text=f"⏳ Mengirim {copies} lembar ke {printer_name}...",
            fg=ORANGE,
        )
        if self.on_status:
            self.on_status(f"🖨 Mencetak {copies} lembar ke {printer_name}...", ORANGE)

        def _worker():
            try:
                result = print_image(
                    self.image_path,
                    printer_name=printer_name,
                    copies=copies,
                )
                self._schedule_ui(self._on_print_success, result)
            except Exception as exc:
                logging.exception("Gagal mencetak foto")
                self._schedule_ui(self._on_print_error, exc)

        threading.Thread(target=_worker, daemon=True).start()

    def _schedule_ui(self, callback, *args):
        if self._closed:
            return
        try:
            if self.dialog.winfo_exists():
                self.dialog.after(0, callback, *args)
        except tk.TclError:
            pass

    def _on_print_success(self, result: dict):
        self._printing = False
        if self._closed:
            return
        printer_name = result["printer"]
        copies = result["copies"]
        msg = f"✅ {copies} lembar dikirim ke {printer_name}"
        if self.on_status:
            self.on_status(msg, GREEN)
        self.status_label.configure(text=msg, fg=GREEN)
        self._set_controls_enabled(True)
        messagebox.showinfo(
            "Berhasil Dicetak",
            f"Foto berhasil dikirim ke printer:\n{printer_name}\n\nJumlah cetak: {copies} lembar",
            parent=self.dialog,
        )
        self._handle_close()

    def _on_print_error(self, error: Exception):
        self._printing = False
        if self._closed:
            return
        self._set_controls_enabled(True)
        self.status_label.configure(text="❌ Gagal mengirim ke printer", fg=ACCENT)
        if self.on_status:
            self.on_status("❌ Cetak foto gagal", ACCENT)
        messagebox.showerror("Gagal Mencetak", str(error), parent=self.dialog)

    def _handle_close(self):
        if self._printing or self._closed:
            return
        self._closed = True
        try:
            self.dialog.grab_release()
        except tk.TclError:
            pass
        try:
            self.dialog.destroy()
        except tk.TclError:
            pass
        # Kembalikan fokus & grab ke PreviewWindow agar tetap interaktif
        try:
            if self.parent.winfo_exists():
                self.parent.grab_set()
                self.parent.focus_force()
        except tk.TclError:
            pass
        if self.on_close:
            self.on_close()
