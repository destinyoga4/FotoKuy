import customtkinter as ctk


class HomePage(ctk.CTkFrame):

    def __init__(self, parent, on_solo=None):

        super().__init__(parent)

        self.on_solo = on_solo

        self.build_ui()

    def build_ui(self):


        title = ctk.CTkLabel(
            self,
            text="WELCOME TO FOTOSKUY",
            font=("Arial", 36, "bold")
        )

        title.pack(pady=(50, 20))

        desc = ctk.CTkLabel(
            self,
            text="Raka Cimahi blablabla wekwek.",
            font=("Arial", 16)
        )

        desc.pack()

        question = ctk.CTkLabel(
            self,
            text="Apakah anda ingin foto sendiri atau dengan teman?",
            font=("Arial", 18)
        )

        question.pack(pady=(50, 30))

        button_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        button_frame.pack()

        solo_btn = ctk.CTkButton(
            button_frame,
            text="SOLO",
            width=250,
            height=180,
            font=("Arial", 28, "bold"),
            command=self.handle_solo
        )

        solo_btn.pack(
            side="left",
            padx=20
        )

        mabar_btn = ctk.CTkButton(
            button_frame,
            text="MABAR\n\nCOMING SOON",
            width=250,
            height=180,
            font=("Arial", 24)
        )

        mabar_btn.pack(
            side="left",
            padx=20
        )

    def handle_solo(self):

        if self.on_solo:
            self.on_solo()