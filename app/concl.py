from datetime import datetime
import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from docx import Document

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "inspectors_config.json"

# Стандартные интервалы мерного пояса для РК
RK_INTERVALS = [
    "0-300",
    "300-600",
    "600-900",
    "900-1200",
    "1200-1500",
    "1500-1800",
    "1800-2100",
    "2100-0",
]


def load_config():
    """Загружает базу специалистов и настройки по умолчанию из файла."""
    default_data = {
        "inspectors": [
            {"name": "Владимиров А.С.", "cert": "II, № 0057-18-22812 от 29.03.2024г."},
            {"name": "Ильницкий Н.А.", "cert": "II, № 0072-2986-2025 от 28.11.2025г."},
            {"name": "Ильницкий И.А.", "cert": "II, № 0072-4490-2026 от 03.04.2026г."},
        ],
        "defaults": {"ВИК": "Владимиров А.С.", "РК": "Ильницкий И.А.", "УЗК": "Ильницкий Н.А."},
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_data
    return default_data


def save_config(data):
    """Сохраняет базу специалистов в файл."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {e}")


def replace_text_in_paragraph(paragraph, search_text, replace_text):
    """Точечно заменяет текст в параграфе, сохраняя картинки и форматирование."""
    if search_text in paragraph.text:
        for run in paragraph.runs:
            if search_text in run.text:
                run.text = run.text.replace(search_text, replace_text)
                return

        full_text = "".join(run.text for run in paragraph.runs)
        if search_text in full_text:
            new_full_text = full_text.replace(search_text, replace_text)
            if paragraph.runs:
                paragraph.runs[0].text = new_full_text
                for run in paragraph.runs[1:]:
                    run.text = ""


def replace_text_in_table(table, search_text, replace_text):
    """Безопасная замена в таблицах с сохранением верстки."""
    for row in table.rows:
        trPr = row._tr.get_or_add_trPr()
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                replace_text_in_paragraph(paragraph, search_text, replace_text)
            for nested_table in cell.tables:
                replace_text_in_table(nested_table, search_text, replace_text)


def process_document(
    template_path, output_path, joint_num, doc_date, inspector_data, rk_data=None
):
    """Открывает шаблон, заменяет общие теги и специфичные теги дефектов РК."""
    doc = Document(template_path)

    if "vik" in template_path.lower():
        prefix = "VIK"
    elif "rk" in template_path.lower():
        prefix = "RK"
    elif "uzk" in template_path.lower():
        prefix = "UZK"
    else:
        prefix = "GENERAL"

    insp_tag = f"{{{{INSPECTOR_{prefix}}}}}"
    cert_tag = f"{{{{CERT_{prefix}}}}}"

    inspector_name = inspector_data.get("name", "")
    inspector_cert = inspector_data.get("cert", "")

    # Базовая замена по всему документу
    for paragraph in doc.paragraphs:
        replace_text_in_paragraph(paragraph, "{{JOINT}}", joint_num)
        replace_text_in_paragraph(paragraph, "{{DATE}}", doc_date)
        replace_text_in_paragraph(paragraph, insp_tag, inspector_name)
        replace_text_in_paragraph(paragraph, cert_tag, inspector_cert)

    for table in doc.tables:
        replace_text_in_table(table, "{{JOINT}}", joint_num)
        replace_text_in_table(table, "{{DATE}}", doc_date)
        replace_text_in_table(table, insp_tag, inspector_name)
        replace_text_in_table(table, cert_tag, inspector_cert)

    # Если это шаблон РК и переданы данные дефектов — подставляем их
    if rk_data and "rk" in template_path.lower():
        for interval in RK_INTERVALS:
            data = rk_data["intervals"].get(
                interval, {"cord": "-", "defect": "ДНО", "concl": "Годен"}
            )
            # Оборачиваем теги интервалов в двойные скобки {{...}}
            cord_tag = f"{{{{{interval}_cord}}}}"
            defect_tag = f"{{{{{interval}_defect}}}}"
            concl_tag = f"{{{{{interval}_concl}}}}"

            for paragraph in doc.paragraphs:
                replace_text_in_paragraph(
                    paragraph, cord_tag, data["cord"]
                )
                replace_text_in_paragraph(
                    paragraph, defect_tag, data["defect"]
                )
                replace_text_in_paragraph(
                    paragraph, concl_tag, data["concl"]
                )
            for table in doc.tables:
                replace_text_in_table(table, cord_tag, data["cord"])
                replace_text_in_table(table, defect_tag, data["defect"])
                replace_text_in_table(table, concl_tag, data["concl"])

        # Подставляем итоговое заключение РК
        summary = rk_data.get("summary", "Годен")
        for paragraph in doc.paragraphs:
            replace_text_in_paragraph(paragraph, "{{summary_concl}}", summary)
        for table in doc.tables:
            replace_text_in_table(table, "{{summary_concl}}", summary)

    doc.save(output_path)


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

        # Скролл-контейнер для интервалов
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

            # Координата
            entry_cord = ctk.CTkEntry(row_frame, width=80, height=28)
            entry_cord.pack(side="left", padx=2)
            entry_cord.insert(0, saved["cord"])

            # Описание
            entry_defect = ctk.CTkEntry(row_frame, width=170, height=28)
            entry_defect.pack(side="left", padx=2)
            entry_defect.insert(0, saved["defect"])

            # Заключение (Годен / Ремонт)
            combo_concl = ctk.CTkComboBox(
                row_frame, values=["Годен", "Ремонт", "Вырезать"], width=100, height=28
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

        self.callback(
            {"intervals": new_intervals, "summary": summary}
        )
        self.destroy()


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


class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Генератор заключений НК")
        self.geometry("520x660")
        self.resizable(False, False)

        if getattr(sys, "frozen", False):
            default_dir = os.path.dirname(sys.executable)
        else:
            default_dir = os.path.dirname(os.path.abspath(__file__))

        self.templates_dir = ctk.StringVar(value=default_dir)
        self.rk_defects_data = None  # Данные дефектов РК

        # Заголовок
        self.title_label = ctk.CTkLabel(
            self,
            text="Автоматизация заключений НК",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.title_label.pack(pady=(15, 10))

        # Фрейм выбора папки
        self.frame_dir = ctk.CTkFrame(self)
        self.frame_dir.pack(pady=5, padx=20, fill="x")

        self.label_dir = ctk.CTkLabel(
            self.frame_dir,
            text="Папка с шаблонами:",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.label_dir.pack(anchor="w", padx=10, pady=(5, 0))

        self.dir_inner_frame = ctk.CTkFrame(self.frame_dir, fg_color="transparent")
        self.dir_inner_frame.pack(fill="x", padx=10, pady=5)

        self.entry_dir = ctk.CTkEntry(
            self.dir_inner_frame, textvariable=self.templates_dir, height=32
        )
        self.entry_dir.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.btn_browse = ctk.CTkButton(
            self.dir_inner_frame,
            text="Обзор",
            width=80,
            height=32,
            command=self.browse_directory,
        )
        self.btn_browse.pack(side="right")

        # Основные данные (Стык и Дата)
        self.frame_inputs = ctk.CTkFrame(self)
        self.frame_inputs.pack(pady=5, padx=20, fill="x")

        self.label_joint = ctk.CTkLabel(
            self.frame_inputs,
            text="Номер стыка:",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.label_joint.pack(anchor="w", padx=10, pady=(8, 0))

        self.entry_joint = ctk.CTkEntry(
            self.frame_inputs, height=32, font=ctk.CTkFont(size=13)
        )
        self.entry_joint.pack(fill="x", padx=10, pady=(3, 8))

        self.label_date = ctk.CTkLabel(
            self.frame_inputs,
            text="Дата заключения (ДД.ММ.ГГГГ):",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.label_date.pack(anchor="w", padx=10, pady=(3, 0))

        self.date_inner_frame = ctk.CTkFrame(
            self.frame_inputs, fg_color="transparent"
        )
        self.date_inner_frame.pack(fill="x", padx=10, pady=(3, 10))

        self.entry_date = ctk.CTkEntry(
            self.date_inner_frame, height=32, font=ctk.CTkFont(size=13)
        )
        self.entry_date.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.entry_date.insert(0, datetime.now().strftime("%d.%m.%Y"))

        self.btn_today = ctk.CTkButton(
            self.date_inner_frame,
            text="Сегодня",
            width=80,
            height=32,
            command=self.set_today_date,
        )
        self.btn_today.pack(side="right")

        # Исполнители
        self.frame_inspectors = ctk.CTkFrame(self)
        self.frame_inspectors.pack(pady=5, padx=20, fill="x")

        top_insp_frame = ctk.CTkFrame(self.frame_inspectors, fg_color="transparent")
        top_insp_frame.pack(fill="x", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            top_insp_frame,
            text="Исполнители контроля:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            top_insp_frame,
            text="⚙ Управление базой",
            width=130,
            height=26,
            command=self.open_manager,
        ).pack(side="right")

        self.row_vik = ctk.CTkFrame(
            self.frame_inspectors, fg_color="transparent"
        )
        self.row_vik.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(self.row_vik, text="ВИК:", width=50, anchor="w").pack(
            side="left"
        )
        self.combo_vik = ctk.CTkComboBox(self.row_vik, height=28)
        self.combo_vik.pack(side="right", expand=True, fill="x")

        self.row_rk = ctk.CTkFrame(self.frame_inspectors, fg_color="transparent")
        self.row_rk.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(self.row_rk, text="РК:", width=50, anchor="w").pack(
            side="left"
        )
        self.combo_rk = ctk.CTkComboBox(self.row_rk, height=28)
        self.combo_rk.pack(side="right", expand=True, fill="x")

        self.row_uzk = ctk.CTkFrame(
            self.frame_inspectors, fg_color="transparent"
        )
        self.row_uzk.pack(fill="x", padx=10, pady=(2, 8))
        ctk.CTkLabel(self.row_uzk, text="УЗК:", width=50, anchor="w").pack(
            side="left"
        )
        self.combo_uzk = ctk.CTkComboBox(self.row_uzk, height=28)
        self.combo_uzk.pack(side="right", expand=True, fill="x")

        self.update_comboboxes()

        # Фрейм опций РК (Дефекты)
        self.frame_rk_opt = ctk.CTkFrame(self)
        self.frame_rk_opt.pack(pady=5, padx=20, fill="x")

        self.check_defects = ctk.CTkCheckBox(
            self.frame_rk_opt,
            text="Указать дефекты / настроить РК",
            command=self.toggle_defects_btn,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.check_defects.pack(anchor="w", padx=10, pady=8)

        self.btn_defects_config = ctk.CTkButton(
            self.frame_rk_opt,
            text="Заполнить карту дефектов РК...",
            state="disabled",
            height=30,
            command=self.open_defects_window,
        )
        self.btn_defects_config.pack(fill="x", padx=10, pady=(0, 8))

        # Кнопка генерации
        self.btn_generate = ctk.CTkButton(
            self,
            text="Создать пакет документов (ВИК, РК, УЗК)",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#28a745",
            hover_color="#218838",
            height=40,
            command=self.generate_files,
        )
        self.btn_generate.pack(pady=(10, 15), padx=20, fill="x")

    def toggle_defects_btn(self):
        if self.check_defects.get() == 1:
            self.btn_defects_config.configure(state="normal")
            # Если еще не открывали, инициализируем дефолтные «ДНО» / «Годен»
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
        self.rk_summary_status = result_dict["summary"]

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

    def browse_directory(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.templates_dir.set(dir_path)

    def set_today_date(self):
        self.entry_date.delete(0, ctk.END)
        self.entry_date.insert(0, datetime.now().strftime("%d.%m.%Y"))

    def generate_files(self):
        folder = self.templates_dir.get()
        joint = self.entry_joint.get().strip()
        doc_date = self.entry_date.get().strip()

        vik_name = self.combo_vik.get().strip()
        rk_name = self.combo_rk.get().strip()
        uzk_name = self.combo_uzk.get().strip()

        if not folder:
            messagebox.showerror("Ошибка", "Укажите папку с шаблонами!")
            return
        if not joint:
            messagebox.showerror("Ошибка", "Введите номер стыка!")
            return

        config = load_config()
        inspectors_map = {i["name"]: i for i in config["inspectors"]}

        vik_data = inspectors_map.get(vik_name, {"name": vik_name, "cert": ""})
        rk_data = inspectors_map.get(rk_name, {"name": rk_name, "cert": ""})
        uzk_data = inspectors_map.get(uzk_name, {"name": uzk_name, "cert": ""})

        vik_template = os.path.join(folder, "template_vik.docx")
        rk_template = os.path.join(folder, "template_rk.docx")
        uzk_template = os.path.join(folder, "template_uzk.docx")

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
                "В указанной папке отсутствуют шаблоны:\n• "
                + "\n• ".join(missing_files),
            )
            return

        # Подготовка данных дефектов РК, если чекбокс активен
        rk_payload = None
        if self.check_defects.get() == 1:
            if not self.rk_defects_data:
                self.rk_defects_data = {
                    interval: {"cord": "-", "defect": "ДНО", "concl": "Годен"}
                    for interval in RK_INTERVALS
                }
            # Проверяем итоговый статус
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
            # Если галочка не стоит, по умолчанию все зоны чистые (ДНО, Годен)
            default_intervals = {
                interval: {"cord": "-", "defect": "ДНО", "concl": "Годен"}
                for interval in RK_INTERVALS
            }
            rk_payload = {"intervals": default_intervals, "summary": "Годен"}

        try:
            out_folder = os.path.join(folder, f"Стык_{joint}")
            os.makedirs(out_folder, exist_ok=True)

            process_document(
                vik_template,
                os.path.join(out_folder, f"{joint} ВИК.docx"),
                joint,
                doc_date,
                vik_data,
            )
            process_document(
                rk_template,
                os.path.join(out_folder, f"{joint} РК.docx"),
                joint,
                doc_date,
                rk_data,
                rk_payload,
            )
            process_document(
                uzk_template,
                os.path.join(out_folder, f"{joint} УЗК.docx"),
                joint,
                doc_date,
                uzk_data,
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


if __name__ == "__main__":
    import sys

    app = App()
    app.mainloop()