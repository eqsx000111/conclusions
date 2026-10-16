from datetime import datetime
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

from app.core.config import RK_INTERVALS, load_config, save_config
from app.core.doc_processor import process_document
from app.ui.defects_window import RKDefectsWindow
from app.ui.inspectors_window import InspectorManagerWindow


class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Генератор заключений НК")
        self.geometry("520x860")
        self.resizable(False, False)

        if getattr(sys, "frozen", False):
            default_dir = os.path.dirname(sys.executable)
        else:
            default_dir = os.path.dirname(os.path.abspath(__file__))

        config = load_config()

        saved_templates_dir = config.get("templates_folder", "")
        remember_templates = config.get("remember_templates", False)
        initial_templates_dir = (
            saved_templates_dir
            if (remember_templates and saved_templates_dir)
            else default_dir
        )
        self.templates_dir = ctk.StringVar(value=initial_templates_dir)
        self.remember_templates_var = ctk.BooleanVar(
            value=remember_templates
        )

        saved_save_dir = config.get("save_folder", "")
        remember_save = config.get("remember_folder", False)
        initial_save_dir = (
            saved_save_dir if (remember_save and saved_save_dir) else default_dir
        )
        self.save_dir = ctk.StringVar(value=initial_save_dir)
        self.remember_save_var = ctk.BooleanVar(value=remember_save)

        self.rk_defects_data = None

        self.title_label = ctk.CTkLabel(
            self,
            text="Автоматизация заключений НК",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.title_label.pack(pady=(10, 5))

        # Папка с шаблонами
        self.frame_dir = ctk.CTkFrame(self)
        self.frame_dir.pack(pady=2, padx=20, fill="x")
        ctk.CTkLabel(
            self.frame_dir,
            text="Папка с шаблонами:",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(3, 0))

        dir_inner = ctk.CTkFrame(self.frame_dir, fg_color="transparent")
        dir_inner.pack(fill="x", padx=10, pady=3)
        self.entry_dir = ctk.CTkEntry(
            dir_inner, textvariable=self.templates_dir, height=28
        )
        self.entry_dir.pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(
            dir_inner,
            text="Обзор",
            width=80,
            height=28,
            command=self.browse_templates_dir,
        ).pack(side="right")

        self.check_remember_templates = ctk.CTkCheckBox(
            self.frame_dir,
            text="Запомнить папку с шаблонами",
            variable=self.remember_templates_var,
            command=self.toggle_remember_templates,
            font=ctk.CTkFont(size=11),
        )
        self.check_remember_templates.pack(anchor="w", padx=10, pady=(0, 4))

        # Папка сохранения результатов
        self.frame_save = ctk.CTkFrame(self)
        self.frame_save.pack(pady=2, padx=20, fill="x")
        ctk.CTkLabel(
            self.frame_save,
            text="Папка для сохранения результатов:",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(3, 0))

        save_inner = ctk.CTkFrame(self.frame_save, fg_color="transparent")
        save_inner.pack(fill="x", padx=10, pady=3)
        self.entry_save = ctk.CTkEntry(
            save_inner, textvariable=self.save_dir, height=28
        )
        self.entry_save.pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(
            save_inner,
            text="Обзор",
            width=80,
            height=28,
            command=self.browse_save_directory,
        ).pack(side="right")

        self.check_remember_save = ctk.CTkCheckBox(
            self.frame_save,
            text="Запомнить папку сохранения",
            variable=self.remember_save_var,
            command=self.toggle_remember_save,
            font=ctk.CTkFont(size=11),
        )
        self.check_remember_save.pack(anchor="w", padx=10, pady=(0, 4))

        # Стык и Дата
        self.frame_inputs = ctk.CTkFrame(self)
        self.frame_inputs.pack(pady=2, padx=20, fill="x")
        ctk.CTkLabel(
            self.frame_inputs,
            text="Номер стыка:",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(4, 0))
        self.entry_joint = ctk.CTkEntry(
            self.frame_inputs, height=28, font=ctk.CTkFont(size=12)
        )
        self.entry_joint.pack(fill="x", padx=10, pady=(2, 4))

        ctk.CTkLabel(
            self.frame_inputs,
            text="Дата заключения (ДД.ММ.ГГГГ):",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(2, 0))

        date_inner = ctk.CTkFrame(self.frame_inputs, fg_color="transparent")
        date_inner.pack(fill="x", padx=10, pady=(2, 6))
        self.entry_date = ctk.CTkEntry(
            date_inner, height=28, font=ctk.CTkFont(size=12)
        )
        self.entry_date.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.entry_date.insert(0, datetime.now().strftime("%d.%m.%Y"))
        ctk.CTkButton(
            date_inner,
            text="Сегодня",
            width=80,
            height=28,
            command=self.set_today_date,
        ).pack(side="right")

        # lab
        self.frame_lab = ctk.CTkFrame(self)
        self.frame_lab.pack(pady=2, padx=20, fill="x")
        ctk.CTkLabel(
            self.frame_lab,
            text="Свидетельство ЛНК:",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(3, 0))
        lab_certs = config.get("lab_certs", [])
        default_cert = config.get("default_lab_cert", lab_certs[0] if lab_certs else "")
        self.combo_lab = ctk.CTkComboBox(self.frame_lab, values=lab_certs, height=26)
        self.combo_lab.pack(fill="x", padx=10, pady=(2, 6))
        self.combo_lab.set(default_cert)

        # Исполнители
        self.frame_inspectors = ctk.CTkFrame(self)
        self.frame_inspectors.pack(pady=2, padx=20, fill="x")
        top_insp = ctk.CTkFrame(self.frame_inspectors, fg_color="transparent")
        top_insp.pack(fill="x", padx=10, pady=(4, 2))
        ctk.CTkLabel(
            top_insp,
            text="Исполнители контроля:",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(side="left")
        ctk.CTkButton(
            top_insp,
            text="⚙ Управление базой",
            width=120,
            height=24,
            command=self.open_manager,
        ).pack(side="right")

        self.row_vik = ctk.CTkFrame(
            self.frame_inspectors, fg_color="transparent"
        )
        self.row_vik.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(self.row_vik, text="ВИК:", width=45, anchor="w").pack(
            side="left"
        )
        self.combo_vik = ctk.CTkComboBox(self.row_vik, height=26)
        self.combo_vik.pack(side="right", expand=True, fill="x")

        self.row_rk = ctk.CTkFrame(self.frame_inspectors, fg_color="transparent")
        self.row_rk.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(self.row_rk, text="РК:", width=45, anchor="w").pack(
            side="left"
        )
        self.combo_rk = ctk.CTkComboBox(self.row_rk, height=26)
        self.combo_rk.pack(side="right", expand=True, fill="x")

        self.row_uzk = ctk.CTkFrame(
            self.frame_inspectors, fg_color="transparent"
        )
        self.row_uzk.pack(fill="x", padx=10, pady=(2, 4))
        ctk.CTkLabel(self.row_uzk, text="УЗК:", width=45, anchor="w").pack(
            side="left"
        )
        self.combo_uzk = ctk.CTkComboBox(self.row_uzk, height=26)
        self.combo_uzk.pack(side="right", expand=True, fill="x")

        self.update_comboboxes()

        # Дефекты РК
        self.frame_rk_opt = ctk.CTkFrame(self)
        self.frame_rk_opt.pack(pady=2, padx=20, fill="x")
        self.check_defects = ctk.CTkCheckBox(
            self.frame_rk_opt,
            text="Указать дефекты / настроить РК",
            command=self.toggle_defects_btn,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.check_defects.pack(anchor="w", padx=10, pady=4)
        self.btn_defects_config = ctk.CTkButton(
            self.frame_rk_opt,
            text="Заполнить карту дефектов РК...",
            state="disabled",
            height=26,
            command=self.open_defects_window,
        )
        self.btn_defects_config.pack(fill="x", padx=10, pady=(0, 4))

        # Кнопка генерации
        self.btn_generate = ctk.CTkButton(
            self,
            text="Создать пакет документов (ВИК, РК, УЗК)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#28a745",
            hover_color="#218838",
            height=36,
            command=self.generate_files,
        )
        self.btn_generate.pack(pady=(8, 10), padx=20, fill="x")

    def toggle_defects_btn(self):
        if self.check_defects.get() == 1:
            self.btn_defects_config.configure(state="normal")
            if not self.rk_defects_data:
                self.rk_defects_data = {
                    interval: {"cord": "-", "defect": "ДНО", "concl": "Годен"}
                    for interval in RK_INTERVALS
                }
        else:
            self.btn_defects_config.configure(state="disabled")

    def open_defects_window(self):
        RKDefectsWindow(self, self.rk_defects_data, self.save_rk_defects)

    def save_rk_defects(self, result_dict):
        self.rk_defects_data = result_dict["intervals"]

    def update_comboboxes(self):
        config = load_config()
        names = [i["name"] for i in config["inspectors"]]
        self.combo_vik.configure(values=names)
        self.combo_rk.configure(values=names)
        self.combo_uzk.configure(values=names)
        defaults = config["defaults"]
        self.combo_vik.set(defaults.get("ВИК", names[0] if names else ""))
        self.combo_rk.set(defaults.get("РК", names[0] if names else ""))
        self.combo_uzk.set(defaults.get("УЗК", names[0] if names else ""))

    def open_manager(self):
        InspectorManagerWindow(self, self.update_comboboxes)

    def browse_templates_dir(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.templates_dir.set(dir_path)
            if self.remember_templates_var.get():
                config = load_config()
                config["templates_folder"] = dir_path
                config["remember_templates"] = True
                save_config(config)

    def toggle_remember_templates(self):
        config = load_config()
        is_remember = self.remember_templates_var.get()
        config["remember_templates"] = is_remember
        config["templates_folder"] = self.templates_dir.get() if is_remember else ""
        save_config(config)

    def browse_save_directory(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.save_dir.set(dir_path)
            if self.remember_save_var.get():
                config = load_config()
                config["save_folder"] = dir_path
                config["remember_folder"] = True
                save_config(config)

    def toggle_remember_save(self):
        config = load_config()
        is_remember = self.remember_save_var.get()
        config["remember_folder"] = is_remember
        config["save_folder"] = self.save_dir.get() if is_remember else ""
        save_config(config)

    def set_today_date(self):
        self.entry_date.delete(0, tk.END)
        self.entry_date.insert(0, datetime.now().strftime("%d.%m.%Y"))

    def generate_files(self):
        templates_folder = self.templates_dir.get()
        target_folder = self.save_dir.get()
        joint = self.entry_joint.get().strip()
        doc_date = self.entry_date.get().strip()
        selected_lab_cert = self.combo_lab.get().strip()

        vik_name = self.combo_vik.get().strip()
        rk_name = self.combo_rk.get().strip()
        uzk_name = self.combo_uzk.get().strip()

        if not templates_folder:
            messagebox.showerror("Ошибка", "Укажите папку с шаблонами!")
            return
        if not target_folder:
            messagebox.showerror("Ошибка", "Укажите папку для сохранения!")
            return
        if not joint:
            messagebox.showerror("Ошибка", "Введите номер стыка!")
            return

        config = load_config()
        inspectors_map = {i["name"]: i for i in config["inspectors"]}

        vik_data = inspectors_map.get(vik_name, {"name": vik_name, "cert": ""})
        rk_data = inspectors_map.get(rk_name, {"name": rk_name, "cert": ""})
        uzk_data = inspectors_map.get(uzk_name, {"name": uzk_name, "cert": ""})

        vik_template = os.path.join(templates_folder, "template_vik.docx")
        rk_template = os.path.join(templates_folder, "template_rk.docx")
        uzk_template = os.path.join(templates_folder, "template_uzk.docx")

        missing_files = []
        if not os.path.exists(vik_template):
            missing_files.append("template_vik.docx")
        if not os.path.exists(rk_template):
            missing_files.append("template_rk.docx")
        if not os.path.exists(uzk_template):
            missing_files.append("template_uzk.docx")

        if missing_files:
            messagebox.showerror(
                "Ошибка",
                "В папке шаблонов отсутствуют файлы:\n• "
                + "\n• ".join(missing_files),
            )
            return

        rk_payload = None
        if self.check_defects.get() == 1:
            if not self.rk_defects_data:
                self.rk_defects_data = {
                    interval: {"cord": "-", "defect": "ДНО", "concl": "Годен"}
                    for interval in RK_INTERVALS
                }
            has_repair = any(
                d["concl"] in ["Ремонт", "Вырезать"]
                for d in self.rk_defects_data.values()
            )
            summary = "Ремонт" if has_repair else "Годен"
            rk_payload = {
                "intervals": self.rk_defects_data,
                "summary": summary,
            }
        else:
            default_intervals = {
                interval: {"cord": "-", "defect": "ДНО", "concl": "Годен"}
                for interval in RK_INTERVALS
            }
            rk_payload = {"intervals": default_intervals, "summary": "Годен"}

        try:
            out_folder = os.path.join(target_folder, f"Стык_{joint}")
            os.makedirs(out_folder, exist_ok=True)

            process_document(
                vik_template,
                os.path.join(out_folder, f"{joint} ВИК.docx"),
                joint,
                doc_date,
                vik_data,
                selected_lab_cert
            )
            process_document(
                rk_template,
                os.path.join(out_folder, f"{joint} РК.docx"),
                joint,
                doc_date,
                rk_data,
                selected_lab_cert,
                rk_payload,
            )
            process_document(
                uzk_template,
                os.path.join(out_folder, f"{joint} УЗК.docx"),
                joint,
                doc_date,
                uzk_data,
                selected_lab_cert
            )

            messagebox.showinfo(
                "Успех!",
                f"Пакет заключений для стыка №{joint} успешно создан!\n\nПапка сохранения:\n{out_folder}",
            )
            self.entry_joint.delete(0, ctk.END)

        except Exception as e:
            messagebox.showerror(
                "Ошибка обработки",
                f"Не удалось создать документы.\nУбедитесь, что файлы закрыты в Word.\n\nДетали:\n{str(e)}",
            )