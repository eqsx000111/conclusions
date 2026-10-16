from tkinter import messagebox
import customtkinter as ctk
from app.core.config import RK_INTERVALS


class RKDefectsWindow(ctk.CTkToplevel):
    """Окно детальной настройки дефектов РК по интервалам."""

    def __init__(self, parent, current_data, callback):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        self.data = current_data or {}

        self.title("Карта дефектов РК")
        self.geometry("600x650")
        self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(
            self,
            text="Настройка дефектов по зонам контроля (РК)",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(pady=(15, 10))

        self.scroll_frame = ctk.CTkScrollableFrame(self, height=450)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=5)

        self.rows_ui = {}

        for interval in RK_INTERVALS:
            saved = self.data.get(
                interval, {"cord": "-", "defect": "ДНО", "concl": "Годен"}
            )

            row_frame = ctk.CTkFrame(self.scroll_frame)
            row_frame.pack(fill="x", pady=5, padx=5)

            ctk.CTkLabel(
                row_frame,
                text=f"Зона {interval}:",
                font=ctk.CTkFont(size=12, weight="bold"),
                width=80,
                anchor="w",
            ).pack(side="left", padx=5)

            entry_cord = ctk.CTkEntry(row_frame, width=80, height=28)
            entry_cord.pack(side="left", padx=2)
            entry_cord.insert(0, saved["cord"])

            entry_defect = ctk.CTkEntry(row_frame, width=170, height=28)
            entry_defect.pack(side="left", padx=2)
            entry_defect.insert(0, saved["defect"])

            combo_concl = ctk.CTkComboBox(
                row_frame,
                values=["Годен", "Ремонт", "Вырезать"],
                width=100,
                height=28,
            )
            combo_concl.pack(side="left", padx=2)
            combo_concl.set(saved["concl"])

            self.rows_ui[interval] = {
                "cord": entry_cord,
                "defect": entry_defect,
                "concl": combo_concl,
            }

        ctk.CTkButton(
            self,
            text="Применить и закрыть",
            fg_color="#28a745",
            hover_color="#218838",
            height=35,
            command=self.save_data,
        ).pack(pady=15, padx=20, fill="x")

    def save_data(self):
        new_intervals = {}
        has_repair = False

        for interval, widgets in self.rows_ui.items():
            cord = widgets["cord"].get().strip() or "-"
            defect = widgets["defect"].get().strip() or "ДНО"
            concl = widgets["concl"].get().strip()

            new_intervals[interval] = {
                "cord": cord,
                "defect": defect,
                "concl": concl,
            }
            if concl in ["Ремонт", "Вырезать"]:
                has_repair = True

        summary = "Ремонт" if has_repair else "Годен"

        self.callback({"intervals": new_intervals, "summary": summary})
        self.destroy()