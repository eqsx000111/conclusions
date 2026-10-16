import json
import os

CONFIG_FILE = "inspectors_config.json"

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
    """Загружает конфигурацию из файла."""
    default_data = {
        "inspectors": [
            {"name": "Владимиров А.С.", "cert": "II, № 0057-18-22812"},
            {"name": "Ильницкий Н.А.", "cert": "II, № 0072-2986-2025"},
            {"name": "Ильницкий И.А.", "cert": "II, № 0072-2987-2025"},
        ],
        "defaults": {"ВИК": "Владимиров А.С.", "РК": "Ильницкий И.А.", "УЗК": "Ильницкий Н.А."},
        "lab_certs": ["№ЛНК-042А0045", "№ЛНК-011А114"],
        "templates_folder": "",
        "remember_templates": False,
        "save_folder": "",
        "remember_folder": False,
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_data
    return default_data


def save_config(data):
    """Сохраняет конфигурацию в файл."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка сохранения конфига: {e}")