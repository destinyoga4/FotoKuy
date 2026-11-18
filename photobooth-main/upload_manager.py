import os
import uuid
import mimetypes
import requests
import qrcode
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from dotenv import load_dotenv
import threading
import time
import zipfile
import math

# Membaca konfigurasi dari file .env
load_dotenv()


class UploadManager:
    MAX_RETRIES = 1

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.supabase_key = os.getenv("SUPABASE_KEY", "")
        self.supabase_bucket = os.getenv("SUPABASE_BUCKET", "")

        self._validate_config()

    def _validate_config(self):
        """Periksa apakah konfigurasi Supabase berhasil dibaca."""
        missing = []

        if not self.supabase_url:
            missing.append("SUPABASE_URL")

        if not self.supabase_key:
            missing.append("SUPABASE_KEY")

        if not self.supabase_bucket:
            missing.append("SUPABASE_BUCKET")

        if missing:
            raise RuntimeError(
                "Konfigurasi Supabase belum lengkap: "
                + ", ".join(missing)
                + ". Periksa file .env."
            )

        if not self.supabase_url.startswith("https://"):
            raise RuntimeError(
                "SUPABASE_URL tidak valid. "
                "Formatnya harus https://PROJECT_ID.supabase.co"
            )

        print("[Supabase] Konfigurasi berhasil dibaca.")
        print(f"[Supabase] URL: {self.supabase_url}")
        print(f"[Supabase] Bucket: {self.supabase_bucket}")
        print("[Supabase] Key: berhasil dibaca")

    # ─────────────────────────────────────────────────────────────
    # UPLOAD
    # ─────────────────────────────────────────────────────────────

    def upload_file(self, filepath):
        """
        Upload file ke Supabase Storage.

        Mendukung gambar, GIF, dan ZIP.
        Return URL publik jika berhasil atau None jika gagal.
        """
        if not os.path.isfile(filepath):
            print(f"Upload gagal: file tidak ditemukan: {filepath}")
            return None

        original_filename = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)

        # Ambil ekstensi file, misalnya .jpg, .gif, atau .zip
        extension = os.path.splitext(original_filename)[1].lower()

        # Nama acak agar file tidak menimpa file sebelumnya
        remote_filename = f"{uuid.uuid4().hex}{extension}"

        # Deteksi Content-Type secara otomatis
        content_type, _ = mimetypes.guess_type(filepath)

        if content_type is None:
            content_type = "application/octet-stream"

        # Endpoint upload Supabase Storage
        upload_url = (
            f"{self.supabase_url}/storage/v1/object/"
            f"{self.supabase_bucket}/{remote_filename}"
        )

        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": content_type,
            "x-upsert": "false",
        }

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                print(
                    f"[Upload Attempt {attempt}] "
                    f"{original_filename} ({file_size // 1024} KB)"
                )

                print(f"[Supabase] Endpoint: {upload_url}")
                print(f"[Supabase] Content-Type: {content_type}")
                print("[Supabase] Mulai mengirim file...")

                with open(filepath, "rb") as file:
                    response = requests.post(
                        upload_url,
                        headers=headers,
                        data=file,
                        timeout=(5, 20),
                    )

                print(f"[Supabase] Respons diterima: HTTP {response.status_code}")

                if response.status_code in (200, 201):
                    public_url = (
                        f"{self.supabase_url}/storage/v1/object/public/"
                        f"{self.supabase_bucket}/{remote_filename}"
                    )

                    print("Upload ke Supabase berhasil!")
                    print(f"Link publik: {public_url}")

                    return public_url

                print(
                    f"Upload gagal (HTTP {response.status_code}): "
                    f"{response.text[:500]}"
                )

                # Error konfigurasi tidak perlu dicoba berulang
                if response.status_code == 400:
                    print(
                        "Periksa format file dan pengaturan bucket."
                    )
                    return None

                if response.status_code == 401:
                    print(
                        "Key Supabase tidak valid. "
                        "Periksa SUPABASE_KEY di .env."
                    )
                    return None

                if response.status_code == 403:
                    print(
                        "Akses ditolak. Periksa key dan izin Storage."
                    )
                    return None

                if response.status_code == 404:
                    print(
                        "Project atau bucket tidak ditemukan. "
                        "Periksa SUPABASE_URL dan SUPABASE_BUCKET."
                    )
                    return None

                if response.status_code == 413:
                    print(
                        "Ukuran file melebihi batas bucket."
                    )
                    return None

            except requests.Timeout:
                print(
                    f"Upload timeout pada percobaan {attempt}."
                )

            except requests.ConnectionError as error:
                print(
                    f"Tidak dapat terhubung ke Supabase: {error}"
                )

            except requests.RequestException as error:
                print(
                    f"Request upload gagal: {error}"
                )

            except OSError as error:
                print(f"File tidak dapat dibaca: {error}")
                return None

            if attempt < self.MAX_RETRIES:
                print("Mencoba ulang dalam 2 detik...")
                time.sleep(2)

        print("Upload gagal setelah semua percobaan.")
        return None

    # ─────────────────────────────────────────────────────────────
    # QR CODE
    # ─────────────────────────────────────────────────────────────

    def generate_qr(self, url, output_path="qr_share_internet.png"):
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(output_path)
        return output_path

    # ─────────────────────────────────────────────────────────────
    # QR WINDOW (Tkinter — lebih cantik dari OpenCV)
    # ─────────────────────────────────────────────────────────────

    def show_qr_window(
        self, qr_path, url, timeout=40, reupload_callback=None, close_callback=None,
        download_label="Foto",
        timeout_callback=None, wait=True,
    ):
        """Tampilkan QR dengan countdown visual, tombol Tutup & Upload Ulang."""
        with Image.open(qr_path) as source:
            qr_img_raw = source.resize((280, 280), Image.LANCZOS)
        root = tk.Toplevel()
        root.title(f"Scan untuk Download {download_label}")
        root.configure(bg="#0f3460")
        root.resizable(False, False)
        root.grab_set()

        # ── Title ──────────────────────────────────────────────
        tk.Label(
            root,
            text="📸 SCAN UNTUK DOWNLOAD",
            font=("Segoe UI", 18, "bold"),
            bg="#0f3460",
            fg="#e94560",
        ).pack(pady=(18, 2))

        tk.Label(
            root, text=download_label, font=("Segoe UI", 12, "bold"),
            bg="#0f3460", fg="#00d4aa",
        ).pack(pady=4)

        tk.Label(
            root, text="Scan QR, lalu tekan Download di halaman yang terbuka.",
            font=("Segoe UI", 10), bg="#0f3460", fg="#a8a8b3",
        ).pack(padx=16)

        tk.Label(
            root,
            text="Foto tersimpan di Supabase Storage",
            font=("Segoe UI", 10),
            bg="#0f3460",
            fg="#a8a8b3",
        ).pack()

        # ── QR Image ───────────────────────────────────────────
        qr_tk = ImageTk.PhotoImage(qr_img_raw, master=root)

        qr_frame = tk.Label(
            root, image=qr_tk, bg="white", relief="flat", bd=8
        )
        qr_frame.image = qr_tk  # prevent GC
        qr_frame.pack(padx=28, pady=14)

        # ── URL Label ──────────────────────────────────────────
        url_display = url if len(url) < 52 else url[:49] + "…"
        tk.Label(
            root,
            text=url_display,
            font=("Consolas", 9),
            bg="#0f3460",
            fg="#00d4aa",
            wraplength=320,
        ).pack(pady=(0, 6))

        # ── Countdown ─────────────────────────────────────────
        count_var = tk.StringVar(value=f"⏱ {timeout} detik")
        count_label = tk.Label(
            root,
            textvariable=count_var,
            font=("Segoe UI", 14),
            bg="#0f3460",
            fg="#f5a623",
        )
        count_label.pack(pady=4)

        # ── Buttons ────────────────────────────────────────────
        btn_frame = tk.Frame(root, bg="#0f3460")
        btn_frame.pack(pady=14)

        timer_id = None
        closed = False

        def cancel_timer():
            nonlocal timer_id
            if timer_id is not None:
                root.after_cancel(timer_id)
                timer_id = None

        def on_destroy(event):
            nonlocal closed
            if event.widget is root:
                closed = True
                cancel_timer()

        root.bind("<Destroy>", on_destroy, add="+")

        def destroy_window():
            nonlocal closed
            if closed:
                return False
            closed = True
            cancel_timer()
            root.destroy()
            return True

        def close_window():
            if not destroy_window():
                return
            if close_callback:
                close_callback()

        def on_close():
            close_window()

        def on_reupload():
            if not destroy_window():
                return
            if reupload_callback:
                reupload_callback()

        btn_close = tk.Button(
            btn_frame,
            text="✖  Tutup",
            font=("Segoe UI", 11, "bold"),
            bg="#e94560",
            fg="white",
            activebackground="#c73652",
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=8,
            command=on_close,
        )
        btn_close.grid(row=0, column=0, padx=10)

        if reupload_callback:
            btn_reup = tk.Button(
                btn_frame,
                text="🔄  Upload Ulang",
                font=("Segoe UI", 11, "bold"),
                bg="#16213e",
                fg="#00d4aa",
                activebackground="#00d4aa",
                activeforeground="#16213e",
                relief="flat",
                cursor="hand2",
                padx=18,
                pady=8,
                command=on_reupload,
            )
            btn_reup.grid(row=0, column=1, padx=10)

        # ── Countdown timer loop ───────────────────────────────
        deadline = time.monotonic() + timeout

        def _tick():
            nonlocal timer_id
            timer_id = None
            if closed:
                return
            remaining = max(0, math.ceil(deadline - time.monotonic()))
            if remaining <= 0:
                if destroy_window():
                    callback = timeout_callback or close_callback
                    if callback:
                        callback()
                return
            count_var.set(f"⏱ {remaining} detik")
            timer_id = root.after(1000, _tick)

        timer_id = root.after(1000, _tick)
        root.protocol("WM_DELETE_WINDOW", close_window)
        if wait:
            root.wait_window()
        return root
    def create_bundle(self, photo_path, gif_path):
        """Paket satu sesi saja agar satu link dapat mengunduh foto dan GIF."""
        if not os.path.isfile(photo_path) or not os.path.isfile(gif_path):
            raise FileNotFoundError("Foto atau GIF untuk paket download tidak ditemukan.")
        bundle_path = os.path.splitext(photo_path)[0] + ".zip"
        with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_STORED) as bundle:
            bundle.write(photo_path, arcname="foto.jpg")
            bundle.write(gif_path, arcname="animasi.gif")
        return bundle_path

