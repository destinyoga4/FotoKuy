import os
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image


class TemplatePage(ctk.CTkFrame):
    CARD_WIDTH = 240
    CARD_HEIGHT = 260
    IMAGE_SIZE = (210, 180)

    def __init__(
        self,
        parent,
        templates,
        on_back=None,
        on_select=None,
        on_create=None
    ):
        super().__init__(
            parent,
            fg_color="#0b1220"
        )

        self.templates = templates
        self.on_back = on_back
        self.on_select = on_select
        self.on_create = on_create
        self.template_images = []

        self.build_ui()

    def build_ui(self):
        self.build_header()
        self.build_content()

    def build_header(self):
        header = ctk.CTkFrame(
            self,
            fg_color="#111c31",
            height=80,
            corner_radius=0
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        back_button = ctk.CTkButton(
            header,
            text="← Kembali",
            width=120,
            height=38,
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
            text="PILIH TEMPLATE",
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
            padx=50,
            pady=30
        )

        description = ctk.CTkLabel(
            content,
            text=(
                f"{len(self.templates)} template tersedia. "
                "Pilih template untuk melihat preview."
            ),
            font=("Segoe UI", 15),
            text_color="#91a2bb"
        )
        description.pack(
            anchor="w",
            pady=(0, 16)
        )

        self.search_entry = ctk.CTkEntry(
            content,
            placeholder_text="Cari template...",
            height=42,
            corner_radius=12,
            fg_color="#17243b",
            border_color="#2b4163"
        )
        self.search_entry.pack(
            fill="x",
            pady=(0, 25)
        )
        self.search_entry.bind(
            "<KeyRelease>",
            self.filter_templates
        )

        self.template_grid = ctk.CTkScrollableFrame(
            content,
            fg_color="#111c31",
            corner_radius=16
        )
        self.template_grid.pack(
            fill="both",
            expand=True
        )

        for column in range(3):
            self.template_grid.grid_columnconfigure(
                column,
                weight=1
            )

        self.render_templates(self.templates)

    def render_templates(self, templates):
        for widget in self.template_grid.winfo_children():
            widget.destroy()

        self.template_images.clear()

        create_card = ctk.CTkButton(
            self.template_grid,
            text="+\n\nBUAT TEMPLATE\nCOMING SOON",
            width=self.CARD_WIDTH,
            height=self.CARD_HEIGHT,
            corner_radius=16,
            font=("Segoe UI", 18, "bold"),
            fg_color="#17243b",
            hover_color="#1d2d48",
            border_width=2,
            border_color="#34d3ad",
            command=self.open_template_setup
        )
        create_card.grid(
            row=0,
            column=0,
            padx=16,
            pady=16,
            sticky="nsew"
        )

        if not templates:
            empty_label = ctk.CTkLabel(
                self.template_grid,
                text=(
                    "Tidak ada template ditemukan.\n"
                    "Periksa folder assets/templates dan config.json."
                ),
                font=("Segoe UI", 15),
                text_color="#f6b756"
            )
            empty_label.grid(
                row=0,
                column=1,
                columnspan=2,
                padx=20,
                pady=70
            )
            return

        for index, template_data in enumerate(templates, start=1):
            self.create_template_card(
                template_data,
                index
            )

    def create_template_card(self, template_data, position):
        thumbnail_path = template_data.get("thumbnail_path")

        if (
            not thumbnail_path
            or not os.path.exists(thumbnail_path)
        ):
            thumbnail_path = template_data.get(
                "overlay_full_path"
            )

        card_image = None

        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                pil_image = Image.open(thumbnail_path)
                pil_image.thumbnail(
                    self.IMAGE_SIZE,
                    Image.LANCZOS
                )

                card_image = ctk.CTkImage(
                    light_image=pil_image,
                    dark_image=pil_image,
                    size=self.IMAGE_SIZE
                )

                # Referensi harus disimpan agar gambar tidak hilang.
                self.template_images.append(card_image)

            except Exception as error:
                print(
                    f"Gagal membuka gambar "
                    f"'{thumbnail_path}': {error}"
                )

        template_name = template_data.get(
            "name",
            "Template"
        )

        button = ctk.CTkButton(
            self.template_grid,
            text=(
                template_name
                if card_image
                else f"🖼️\n\n{template_name}"
            ),
            image=card_image,
            compound="top",
            width=self.CARD_WIDTH,
            height=self.CARD_HEIGHT,
            corner_radius=16,
            font=("Segoe UI", 16, "bold"),
            fg_color="#17243b",
            hover_color="#1d2d48",
            border_width=1,
            border_color="#2b4163",
            command=lambda data=template_data: (
                self.select_template(data)
            )
        )

        row = position // 3
        column = position % 3

        button.grid(
            row=row,
            column=column,
            padx=16,
            pady=16,
            sticky="nsew"
        )

    def filter_templates(self, event=None):
        keyword = self.search_entry.get().strip().lower()

        if not keyword:
            filtered_templates = self.templates
        else:
            filtered_templates = [
                template
                for template in self.templates
                if keyword in template.get(
                    "name",
                    ""
                ).lower()
            ]

        self.render_templates(filtered_templates)

    def select_template(self, template_data):
        if self.on_select:
            self.on_select(template_data)

    def go_back(self):
        if self.on_back:
            self.on_back()

    def open_template_setup(self):
        if self.on_create:
            self.on_create()