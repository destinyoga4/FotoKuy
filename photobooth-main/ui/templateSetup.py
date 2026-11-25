import customtkinter as ctk
from tkinter import messagebox


class TemplateSetupPage(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        on_back=None,
        on_continue=None
    ):
        super().__init__(
            parent,
            fg_color="#0b1220"
        )

        self.on_back = on_back
        self.on_continue = on_continue

        self.template_name_var = ctk.StringVar(
            value="Template Baru"
        )

        self.resolution_var = ctk.StringVar(
            value="600x1800"
        )

        self.custom_width_var = ctk.StringVar(
            value="1080"
        )

        self.custom_height_var = ctk.StringVar(
            value="1350"
        )

        self.resolution_cards = {}

        self.build_ui()
        self.select_resolution("600x1800")

    def build_ui(self):
        self.build_header()
        self.build_content()

    def build_header(self):
        header = ctk.CTkFrame(
            self,
            height=82,
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

        title_container = ctk.CTkFrame(
            header,
            fg_color="transparent"
        )
        title_container.pack(
            side="left",
            padx=10,
            pady=12
        )

        ctk.CTkLabel(
            title_container,
            text="TEMPLATE STUDIO",
            font=("Segoe UI", 11, "bold"),
            text_color="#34d3ad"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_container,
            text="Buat Template Baru",
            font=("Segoe UI", 24, "bold"),
            text_color="#f4f7fb"
        ).pack(anchor="w")

    def build_content(self):
        page_content = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        page_content.pack(
            fill="both",
            expand=True,
            padx=55,
            pady=30
        )

        page_content.grid_columnconfigure(
            0,
            weight=1
        )
        page_content.grid_columnconfigure(
            1,
            weight=0
        )

        self.build_setup_panel(page_content)
        self.build_preview_panel(page_content)

    def build_setup_panel(self, parent):
        setup_panel = ctk.CTkFrame(
            parent,
            fg_color="#111c31",
            corner_radius=18,
            border_width=1,
            border_color="#2b4163"
        )
        setup_panel.grid(
            row=0,
            column=0,
            padx=(0, 20),
            sticky="nsew"
        )

        ctk.CTkLabel(
            setup_panel,
            text="1. Informasi Template",
            font=("Segoe UI", 20, "bold"),
            text_color="#f4f7fb"
        ).pack(
            anchor="w",
            padx=28,
            pady=(28, 8)
        )

        ctk.CTkLabel(
            setup_panel,
            text="Masukkan nama dan pilih ukuran template.",
            font=("Segoe UI", 13),
            text_color="#91a2bb"
        ).pack(
            anchor="w",
            padx=28,
            pady=(0, 20)
        )

        ctk.CTkLabel(
            setup_panel,
            text="Nama template",
            font=("Segoe UI", 13, "bold"),
            text_color="#f4f7fb"
        ).pack(
            anchor="w",
            padx=28,
            pady=(0, 7)
        )

        name_entry = ctk.CTkEntry(
            setup_panel,
            textvariable=self.template_name_var,
            height=44,
            corner_radius=10,
            fg_color="#17243b",
            border_color="#2b4163",
            text_color="#f4f7fb",
            placeholder_text="Contoh: My Pink Strip"
        )
        name_entry.pack(
            fill="x",
            padx=28,
            pady=(0, 28)
        )

        ctk.CTkLabel(
            setup_panel,
            text="2. Pilih Resolusi",
            font=("Segoe UI", 20, "bold"),
            text_color="#f4f7fb"
        ).pack(
            anchor="w",
            padx=28,
            pady=(0, 8)
        )

        ctk.CTkLabel(
            setup_panel,
            text=(
                "Resolusi menentukan ukuran hasil akhir. "
                "Ukuran editor akan menyesuaikan secara otomatis."
            ),
            font=("Segoe UI", 13),
            text_color="#91a2bb",
            wraplength=680,
            justify="left"
        ).pack(
            anchor="w",
            padx=28,
            pady=(0, 20)
        )

        resolution_grid = ctk.CTkFrame(
            setup_panel,
            fg_color="transparent"
        )
        resolution_grid.pack(
            fill="x",
            padx=20,
            pady=(0, 20)
        )

        for column in range(2):
            resolution_grid.grid_columnconfigure(
                column,
                weight=1
            )

        presets = [
            {
                "value": "600x1800",
                "title": "Photo Strip",
                "resolution": "600 × 1800 px",
                "description": "Cocok untuk 4 foto vertikal"
            },
            {
                "value": "600x1500",
                "title": "Short Strip",
                "resolution": "600 × 1500 px",
                "description": "Cocok untuk 3 foto vertikal"
            },
            {
                "value": "1200x1800",
                "title": "Grid Portrait",
                "resolution": "1200 × 1800 px",
                "description": "Cocok untuk grid 4 sampai 6 foto"
            },
            {
                "value": "1080x1080",
                "title": "Square",
                "resolution": "1080 × 1080 px",
                "description": "Cocok untuk layout persegi"
            },
            {
                "value": "1920x1080",
                "title": "Landscape",
                "resolution": "1920 × 1080 px",
                "description": "Cocok untuk hasil digital lebar"
            },
            {
                "value": "custom",
                "title": "Custom",
                "resolution": "Ukuran sendiri",
                "description": "Masukkan lebar dan tinggi manual"
            }
        ]

        for index, preset in enumerate(presets):
            row = index // 2
            column = index % 2

            self.create_resolution_card(
                resolution_grid,
                preset=preset,
                row=row,
                column=column
            )

        self.custom_size_frame = ctk.CTkFrame(
            setup_panel,
            fg_color="#17243b",
            corner_radius=12,
            border_width=1,
            border_color="#2b4163"
        )

        self.build_custom_size_inputs()

        continue_button = ctk.CTkButton(
            setup_panel,
            text="LANJUT KE EDITOR →",
            height=50,
            corner_radius=12,
            fg_color="#34d3ad",
            hover_color="#2bbf9d",
            text_color="#07111d",
            font=("Segoe UI", 14, "bold"),
            command=self.continue_to_editor
        )
        continue_button.pack(
            fill="x",
            padx=28,
            pady=(12, 28)
        )

    def create_resolution_card(
        self,
        parent,
        preset,
        row,
        column
    ):
        value = preset["value"]

        card = ctk.CTkButton(
            parent,
            text=(
                f"{preset['title']}\n"
                f"{preset['resolution']}\n"
                f"{preset['description']}"
            ),
            height=115,
            corner_radius=14,
            fg_color="#17243b",
            hover_color="#1d2d48",
            border_width=1,
            border_color="#2b4163",
            text_color="#f4f7fb",
            font=("Segoe UI", 13, "bold"),
            anchor="w",
            command=lambda selected=value: (
                self.select_resolution(selected)
            )
        )

        card.grid(
            row=row,
            column=column,
            padx=8,
            pady=8,
            sticky="nsew"
        )

        self.resolution_cards[value] = card

    def build_custom_size_inputs(self):
        ctk.CTkLabel(
            self.custom_size_frame,
            text="Ukuran Custom",
            font=("Segoe UI", 14, "bold"),
            text_color="#f4f7fb"
        ).pack(
            anchor="w",
            padx=18,
            pady=(15, 10)
        )

        input_row = ctk.CTkFrame(
            self.custom_size_frame,
            fg_color="transparent"
        )
        input_row.pack(
            fill="x",
            padx=18,
            pady=(0, 16)
        )

        input_row.grid_columnconfigure(0, weight=1)
        input_row.grid_columnconfigure(1, weight=0)
        input_row.grid_columnconfigure(2, weight=1)

        width_entry = ctk.CTkEntry(
            input_row,
            textvariable=self.custom_width_var,
            placeholder_text="Lebar",
            height=40,
            justify="center",
            fg_color="#0b1220",
            border_color="#2b4163"
        )
        width_entry.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        ctk.CTkLabel(
            input_row,
            text="×",
            font=("Segoe UI", 20, "bold"),
            text_color="#91a2bb"
        ).grid(
            row=0,
            column=1,
            padx=12
        )

        height_entry = ctk.CTkEntry(
            input_row,
            textvariable=self.custom_height_var,
            placeholder_text="Tinggi",
            height=40,
            justify="center",
            fg_color="#0b1220",
            border_color="#2b4163"
        )
        height_entry.grid(
            row=0,
            column=2,
            sticky="ew"
        )

    def build_preview_panel(self, parent):
        preview_panel = ctk.CTkFrame(
            parent,
            width=340,
            fg_color="#111c31",
            corner_radius=18,
            border_width=1,
            border_color="#2b4163"
        )
        preview_panel.grid(
            row=0,
            column=1,
            sticky="ns"
        )
        preview_panel.grid_propagate(False)

        ctk.CTkLabel(
            preview_panel,
            text="PREVIEW UKURAN",
            font=("Segoe UI", 12, "bold"),
            text_color="#34d3ad"
        ).pack(
            pady=(28, 5)
        )

        self.preview_title = ctk.CTkLabel(
            preview_panel,
            text="Photo Strip",
            font=("Segoe UI", 22, "bold"),
            text_color="#f4f7fb"
        )
        self.preview_title.pack()

        self.preview_resolution = ctk.CTkLabel(
            preview_panel,
            text="600 × 1800 px",
            font=("Segoe UI", 13),
            text_color="#91a2bb"
        )
        self.preview_resolution.pack(
            pady=(4, 22)
        )

        preview_area = ctk.CTkFrame(
            preview_panel,
            fg_color="#0b1220",
            corner_radius=14
        )
        preview_area.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(0, 20)
        )

        self.preview_canvas = ctk.CTkCanvas(
            preview_area,
            width=250,
            height=390,
            bg="#0b1220",
            highlightthickness=0
        )
        self.preview_canvas.pack(
            expand=True,
            padx=15,
            pady=15
        )

        self.preview_information = ctk.CTkLabel(
            preview_panel,
            text=(
                "Ukuran asli digunakan saat template "
                "disimpan dan dirender."
            ),
            font=("Segoe UI", 11),
            text_color="#91a2bb",
            wraplength=280,
            justify="center"
        )
        self.preview_information.pack(
            padx=25,
            pady=(0, 25)
        )

    def select_resolution(self, value):
        self.resolution_var.set(value)

        for card_value, card in self.resolution_cards.items():
            if card_value == value:
                card.configure(
                    border_color="#34d3ad",
                    border_width=2,
                    fg_color="#1d2d48"
                )
            else:
                card.configure(
                    border_color="#2b4163",
                    border_width=1,
                    fg_color="#17243b"
                )

        if value == "custom":
            self.custom_size_frame.pack(
                fill="x",
                padx=28,
                pady=(0, 10)
            )
        else:
            self.custom_size_frame.pack_forget()

        self.update_preview()

    def get_selected_size(self):
        selected = self.resolution_var.get()

        if selected == "custom":
            try:
                width = int(
                    self.custom_width_var.get()
                )
                height = int(
                    self.custom_height_var.get()
                )
                return width, height

            except ValueError:
                return None

        width_text, height_text = selected.split("x")

        return int(width_text), int(height_text)

    def update_preview(self):
        selected_size = self.get_selected_size()

        if selected_size is None:
            return

        width, height = selected_size

        title_mapping = {
            "600x1800": "Photo Strip",
            "600x1500": "Short Strip",
            "1200x1800": "Grid Portrait",
            "1080x1080": "Square",
            "1920x1080": "Landscape",
            "custom": "Custom"
        }

        self.preview_title.configure(
            text=title_mapping.get(
                self.resolution_var.get(),
                "Template"
            )
        )

        self.preview_resolution.configure(
            text=f"{width} × {height} px"
        )

        self.preview_canvas.delete("all")

        canvas_width = 250
        canvas_height = 390

        available_width = 210
        available_height = 340

        scale = min(
            available_width / width,
            available_height / height
        )

        preview_width = width * scale
        preview_height = height * scale

        left = (
            canvas_width - preview_width
        ) / 2

        top = (
            canvas_height - preview_height
        ) / 2

        right = left + preview_width
        bottom = top + preview_height

        self.preview_canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill="#f4f7fb",
            outline="#34d3ad",
            width=3
        )

        self.preview_canvas.create_text(
            canvas_width / 2,
            canvas_height / 2,
            text=f"{width}\n×\n{height}",
            fill="#17243b",
            font=("Segoe UI", 14, "bold"),
            justify="center"
        )

    def continue_to_editor(self):
        template_name = (
            self.template_name_var.get().strip()
        )

        if not template_name:
            messagebox.showwarning(
                "Nama template kosong",
                "Masukkan nama template terlebih dahulu."
            )
            return

        selected_size = self.get_selected_size()

        if selected_size is None:
            messagebox.showwarning(
                "Ukuran tidak valid",
                "Lebar dan tinggi harus berupa angka."
            )
            return

        width, height = selected_size

        if width < 300 or height < 300:
            messagebox.showwarning(
                "Resolusi terlalu kecil",
                "Lebar dan tinggi minimal 300 piksel."
            )
            return

        if width > 5000 or height > 5000:
            messagebox.showwarning(
                "Resolusi terlalu besar",
                "Lebar dan tinggi maksimal 5000 piksel."
            )
            return

        setup_data = {
            "name": template_name,
            "width": width,
            "height": height,
            "resolution": f"{width}x{height}"
        }

        if self.on_continue:
            self.on_continue(setup_data)
        else:
            messagebox.showinfo(
                "Konfigurasi template",
                f"Nama: {template_name}\n"
                f"Ukuran: {width} × {height} px\n\n"
                "Halaman editor akan dibuat berikutnya."
            )

    def go_back(self):
        if self.on_back:
            self.on_back()