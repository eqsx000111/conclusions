from datetime import datetime
import os
import tkinter as tk  # Оставляем стандартный tkinter для диалогов
from tkinter import filedialog, messagebox
import customtkinter as ctk
from docx import Document

# Устанавливаем тему оформления
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


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


def process_document(template_path, output_path, joint_num, doc_date):
    """Открывает шаблон, заменяет теги и сохраняет новый файл."""
    doc = Document(template_path)

    for paragraph in doc.paragraphs:
        replace_text_in_paragraph(paragraph, "{{JOINT}}", joint_num)
        replace_text_in_paragraph(paragraph, "{{DATE}}", doc_date)

    for table in doc.tables:
        replace_text_in_table(table, "{{JOINT}}", joint_num)
        replace_text_in_table(table, "{{DATE}}", doc_date)

    doc.save(output_path)


class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Генератор заключений НК")
        self.geometry("500x420")
        self.resizable(False, False)

        # Определяем папку, откуда запущен скрипт (или .exe)
        if getattr(sys, "frozen", False):
            default_dir = os.path.dirname(sys.executable)
        else:
            default_dir = os.path.dirname(os.path.abspath(__file__))

        self.templates_dir = ctk.StringVar(value=default_dir)

        # Заголовок
        self.title_label = ctk.CTkLabel(
            self,
            text="Автоматизация заключений НК",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.title_label.pack(pady=(20, 15))

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
            self.dir_inner_frame,
            textvariable=self.templates_dir,
            width=320,
            height=32,
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

        # Фрейм ввода данных (Стык и Дата)
        self.frame_inputs = ctk.CTkFrame(self)
        self.frame_inputs.pack(pady=10, padx=20, fill="x")

        # Номер стыка
        self.label_joint = ctk.CTkLabel(
            self.frame_inputs,
            text="Номер стыка:",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.label_joint.pack(anchor="w", padx=10, pady=(10, 0))

        self.entry_joint = ctk.CTkEntry(
            self.frame_inputs, height=35, font=ctk.CTkFont(size=13)
        )
        self.entry_joint.pack(fill="x", padx=10, pady=(5, 10))

        # Дата
        self.label_date = ctk.CTkLabel(
            self.frame_inputs,
            text="Дата заключения (ДД.ММ.ГГГГ):",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.label_date.pack(anchor="w", padx=10, pady=(5, 0))

        self.date_inner_frame = ctk.CTkFrame(
            self.frame_inputs, fg_color="transparent"
        )
        self.date_inner_frame.pack(fill="x", padx=10, pady=(5, 10))

        self.entry_date = ctk.CTkEntry(
            self.date_inner_frame, height=35, font=ctk.CTkFont(size=13)
        )
        self.entry_date.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.entry_date.insert(0, datetime.now().strftime("%d.%m.%Y"))

        self.btn_today = ctk.CTkButton(
            self.date_inner_frame,
            text="Сегодня",
            width=80,
            height=35,
            command=self.set_today_date,
        )
        self.btn_today.pack(side="right")

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
        self.btn_generate.pack(pady=(15, 20), padx=20, fill="x")

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

        if not folder:
            messagebox.showerror("Ошибка", "Укажите папку с шаблонами!")
            return
        if not joint:
            messagebox.showerror("Ошибка", "Введите номер стыка!")
            return

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

        try:
            out_folder = os.path.join(folder, f"Стык_{joint}")
            os.makedirs(out_folder, exist_ok=True)

            process_document(
                vik_template,
                os.path.join(out_folder, f"{joint} ВИК.docx"),
                joint,
                doc_date,
            )
            process_document(
                rk_template,
                os.path.join(out_folder, f"{joint} РК.docx"),
                joint,
                doc_date,
            )
            process_document(
                uzk_template,
                os.path.join(out_folder, f"{joint} УЗК.docx"),
                joint,
                doc_date,
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