import os
from docx import Document
from app.core.config import RK_INTERVALS


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
    template_path, output_path, joint_num, doc_date, inspector_data, lab_cert, rk_data=None
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

    for paragraph in doc.paragraphs:
        replace_text_in_paragraph(paragraph, "{{JOINT}}", joint_num)
        replace_text_in_paragraph(paragraph, "{{DATE}}", doc_date)
        replace_text_in_paragraph(paragraph, "{{LAB_CERT}}", lab_cert)
        replace_text_in_paragraph(paragraph, insp_tag, inspector_name)
        replace_text_in_paragraph(paragraph, cert_tag, inspector_cert)

    for table in doc.tables:
        replace_text_in_table(table, "{{JOINT}}", joint_num)
        replace_text_in_table(table, "{{DATE}}", doc_date)
        replace_text_in_paragraph(paragraph, "{{LAB_CERT}}", lab_cert)
        replace_text_in_table(table, insp_tag, inspector_name)
        replace_text_in_table(table, cert_tag, inspector_cert)

    if rk_data and "rk" in template_path.lower():
        for interval in RK_INTERVALS:
            data = rk_data["intervals"].get(
                interval, {"cord": "-", "defect": "ДНО", "concl": "Годен"}
            )
            cord_tag = f"{{{{{interval}_cord}}}}"
            defect_tag = f"{{{{{interval}_defect}}}}"
            concl_tag = f"{{{{{interval}_concl}}}}"

            for paragraph in doc.paragraphs:
                replace_text_in_paragraph(paragraph, cord_tag, data["cord"])
                replace_text_in_paragraph(paragraph, defect_tag, data["defect"])
                replace_text_in_paragraph(paragraph, concl_tag, data["concl"])
            for table in doc.tables:
                replace_text_in_table(table, cord_tag, data["cord"])
                replace_text_in_table(table, defect_tag, data["defect"])
                replace_text_in_table(table, concl_tag, data["concl"])

        summary = rk_data.get("summary", "Годен")
        for paragraph in doc.paragraphs:
            replace_text_in_paragraph(paragraph, "{{summary_concl}}", summary)
        for table in doc.tables:
            replace_text_in_table(table, "{{summary_concl}}", summary)

    doc.save(output_path)