from tkinter import messagebox
import customtkinter as ctk
from app.core.config import load_config, save_config


class InspectorManagerWindow(ctk.CTkToplevel):
    """Окно управления базой специалистов."""

    def __init__(self, parent, update_callback):
        super().__init__(parent)
        self.parent = parent
        self.update_callback = update_callback

        self.title("Управление специалистами")
        self.geometry("420x480")
        self.resizable(False, False)
        self.grab_set()

        self.config_data = load_config()

        ctk.CTkLabel(
            self,
            text="База специалистов",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(pady=(15, 5))

        self.list_frame = ctk.CTkScrollableFrame(self, height=160)
        self.list_frame.pack(fill="x", padx=20, pady=5)
        self.refresh_inspector_list()

        self.add_frame = ctk.CTkFrame(self)
        self.add_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            self.add_frame,
            text="Добавить нового специалиста:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(5, 2))

        self.entry_new_name = ctk.CTkEntry(
            self.add_frame, placeholder_text="ФИО (например, Петров А.П.)", height=28
        )
        self.entry_new_name.pack(fill="x", padx=10, pady=2)

        self.entry_new_cert = ctk.CTkEntry(
            self.add_frame,
            placeholder_text="Удостоверение (например, II, № 12345)",
            height=28,
        )
        self.entry_new_cert.pack(fill="x", padx=10, pady=2)

        ctk.CTkButton(
            self.add_frame,
            text="Добавить в базу",
            fg_color="#28a745",
            hover_color="#218838",
            height=30,
            command=self.add_inspector,
        ).pack(fill="x", padx=10, pady=(5, 10))

        self.def_frame = ctk.CTkFrame(self)
        self.def_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(
            self.def_frame,
            text="Специалисты по умолчанию:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(5, 2))

        names = [i["name"] for i in self.config_data["inspectors"]]

        row_v = ctk.CTkFrame(self.def_frame, fg_color="transparent")
        row_v.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(row_v, text="ВИК:", width=50, anchor="w").pack(side="left")
        self.def_vik = ctk.CTkComboBox(row_v, values=names, height=26)
        self.def_vik.pack(side="right", expand=True, fill="x")
        self.def_vik.set(self.config_data["defaults"].get("ВИК", ""))

        row_r = ctk.CTkFrame(self.def_frame, fg_color="transparent")
        row_r.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(row_r, text="РК:", width=50, anchor="w").pack(side="left")
        self.def_rk = ctk.CTkComboBox(row_r, values=names, height=26)
        self.def_rk.pack(side="right", expand=True, fill="x")
        self.def_rk.set(self.config_data["defaults"].get("РК", ""))

        row_u = ctk.CTkFrame(self.def_frame, fg_color="transparent")
        row_u.pack(fill="x", padx=10, pady=(2, 8))
        ctk.CTkLabel(row_u, text="УЗК:", width=50, anchor="w").pack(side="left")
        self.def_uzk = ctk.CTkComboBox(row_u, values=names, height=26)
        self.def_uzk.pack(side="right", expand=True, fill="x")
        self.def_uzk.set(self.config_data["defaults"].get("УЗК", ""))

        ctk.CTkButton(
            self,
            text="Сохранить и закрыть",
            height=35,
            command=self.save_and_close,
        ).pack(pady=10, padx=20, fill="x")

    def refresh_inspector_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        for idx, insp in enumerate(self.config_data["inspectors"]):
            row = ctk.CTkFrame(self.list_frame)
            row.pack(fill="x", pady=2)
            lbl_text = f"{insp['name']} ({insp['cert']})"
            ctk.CTkLabel(row, text=lbl_text, font=ctk.CTkFont(size=11)).pack(
                side="left", padx=5
            )
            ctk.CTkButton(
                row,
                text="X",
                width=28,
                height=24,
                fg_color="#dc3545",
                hover_color="#c82333",
                command=lambda i=idx: self.delete_inspector(i),
            ).pack(side="right", padx=2)

    def add_inspector(self):
        name = self.entry_new_name.get().strip()
        cert = self.entry_new_cert.get().strip()
        if not name or not cert:
            messagebox.showerror("Ошибка", "Заполните ФИО и удостоверение!")
            return

        self.config_data["inspectors"].append({"name": name, "cert": cert})
        save_config(self.config_data)
        self.entry_new_name.delete(0, ctk.END)
        self.entry_new_cert.delete(0, ctk.END)
        self.refresh_inspector_list()

        names = [i["name"] for i in self.config_data["inspectors"]]
        self.def_vik.configure(values=names)
        self.def_rk.configure(values=names)
        self.def_uzk.configure(values=names)

    def delete_inspector(self, index):
        if len(self.config_data["inspectors"]) <= 1:
            messagebox.showerror("Ошибка", "Должен остаться хотя бы один специалист!")
            return
        del self.config_data["inspectors"][index]
        save_config(self.config_data)
        self.refresh_inspector_list()

        names = [i["name"] for i in self.config_data["inspectors"]]
        self.def_vik.configure(values=names)
        self.def_rk.configure(values=names)
        self.def_uzk.configure(values=names)

    def save_and_close(self):
        self.config_data["defaults"]["ВИК"] = self.def_vik.get()
        self.config_data["defaults"]["РК"] = self.def_rk.get()
        self.config_data["defaults"]["УЗК"] = self.def_uzk.get()
        save_config(self.config_data)

        self.update_callback()
        self.destroy()