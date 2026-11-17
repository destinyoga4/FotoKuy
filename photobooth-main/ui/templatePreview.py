import os
import customtkinter as ctk
from PIL import Image


class TemplatePreviewPage(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        template_data,
        on_back=None,
        on_use=None
    ):
        super().__init__(
            parent,
            fg_color="#0b1220"
        )

        self.template_data = template_data
        self.on_back = on_back
        self.on_use = on_use
        self.preview_image = None

        self.build_ui()

    def build_ui(self):
        self.build_header()
        self.build_content()

    def build_header(self):
        header = ctk.CTkFrame(
            self,
            height=80,
            corner_radius=0,
            fg_color="#111c31"
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        back_button = ctk.CTkButton(
            header,
            text="← Kembali",
            width=120,
            height=40,
            corner_radius=10,
            fg_color="#1d2d48",
            hover_color="#2b4163",
            command=self.go_back
        )
        back_button.pack(
            side="left",
            padx=24,
            pady=20
        )

        title = ctk.CTkLabel(
            header,
            text="PREVIEW TEMPLATE",
            font=("Segoe UI", 25, "bold"),
            text_color="#f4f7fb"
        )
        title.pack(
            side="left",
            padx=20
        )

    def build_content(self):
        content = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        content.pack(
            fill="both",
            expand=True,
            padx=60,
            pady=35
        )

        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)

        self.build_image_panel(content)
        self.build_information_panel(content)

    def build_image_panel(self, parent):
        image_panel = ctk.CTkFrame(
            parent,
            fg_color="#111c31",
            corner_radius=18,
            border_width=1,
            border_color="#2b4163"
        )
        image_panel.grid(
            row=0,
            column=0,
            padx=(0, 18),
            sticky="nsew"
        )

        overlay_path = self.template_data.get(
            "overlay_full_path",
            ""
        )

        if overlay_path and os.path.exists(overlay_path):
            try:
                pil_image = Image.open(overlay_path)
                pil_image.thumbnail(
                    (620, 540),
                    Image.LANCZOS
                )

                self.preview_image = ctk.CTkImage(
                    light_image=pil_image,
                    dark_image=pil_image,
                    size=pil_image.size
                )

                image_label = ctk.CTkLabel(
                    image_panel,
                    text="",
                    image=self.preview_image
                )
                image_label.pack(
                    expand=True,
                    padx=30,
                    pady=30
                )

            except Exception as error:
                self.show_image_error(
                    image_panel,
                    f"Gambar template gagal dibuka.\n{error}"
                )
        else:
            self.show_image_error(
                image_panel,
                "Gambar template tidak ditemukan."
            )

    def show_image_error(self, parent, text):
        error_label = ctk.CTkLabel(
            parent,
            text=text,
            font=("Segoe UI", 16),
            text_color="#f6b756"
        )
        error_label.pack(
            expand=True,
            padx=30,
            pady=30
        )

    def build_information_panel(self, parent):
        information_panel = ctk.CTkFrame(
            parent,
            fg_color="#17243b",
            corner_radius=18,
            border_width=1,
            border_color="#2b4163"
        )
        information_panel.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        template_name = self.template_data.get(
            "name",
            "Template"
        )

        slot_count = self.get_slot_count()

        ctk.CTkLabel(
            information_panel,
            text=template_name,
            font=("Segoe UI", 28, "bold"),
            text_color="#f4f7fb",
            wraplength=340,
            justify="left"
        ).pack(
            anchor="w",
            padx=30,
            pady=(40, 12)
        )

        ctk.CTkLabel(
            information_panel,
            text="Detail sesi foto",
            font=("Segoe UI", 14, "bold"),
            text_color="#34d3ad"
        ).pack(
            anchor="w",
            padx=30,
            pady=(15, 8)
        )

        self.create_information_row(
            information_panel,
            "Jumlah foto",
            f"{slot_count} kali"
        )

        self.create_information_row(
            information_panel,
            "Filter",
            "Bisa diganti saat sesi"
        )

        self.create_information_row(
            information_panel,
            "Hasil",
            "Foto komposit dan GIF"
        )

        warning = ctk.CTkLabel(
            information_panel,
            text=(
                f"Kamera akan mengambil {slot_count} foto "
                "sesuai jumlah slot pada template."
            ),
            font=("Segoe UI", 13),
            text_color="#91a2bb",
            wraplength=340,
            justify="left"
        )
        warning.pack(
            anchor="w",
            padx=30,
            pady=(24, 20)
        )

        use_button = ctk.CTkButton(
            information_panel,
            text="GUNAKAN TEMPLATE",
            height=54,
            corner_radius=12,
            font=("Segoe UI", 17, "bold"),
            fg_color="#f0627b",
            hover_color="#ff7f96",
            command=self.use_template
        )
        use_button.pack(
            side="bottom",
            fill="x",
            padx=30,
            pady=30
        )

    def create_information_row(self, parent, label, value):
        row = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )
        row.pack(
            fill="x",
            padx=30,
            pady=7
        )

        ctk.CTkLabel(
            row,
            text=label,
            font=("Segoe UI", 13),
            text_color="#91a2bb"
        ).pack(side="left")

        ctk.CTkLabel(
            row,
            text=value,
            font=("Segoe UI", 13, "bold"),
            text_color="#f4f7fb"
        ).pack(side="right")

    def get_slot_count(self):
        possible_slot_keys = (
            "slots",
            "photo_slots",
            "positions",
            "frames"
        )

        for key in possible_slot_keys:
            value = self.template_data.get(key)

            if isinstance(value, list):
                return len(value)

            if isinstance(value, int):
                return value

        return self.template_data.get(
            "photo_count",
            4
        )

    def go_back(self):
        if self.on_back:
            self.on_back()

    def use_template(self):
        if self.on_use:
            self.on_use(self.template_data)