from app.core.database import Base
import pkgutil
import importlib
from pathlib import Path

# Получаем список всех модулей в пакете models
package_dir = Path(__file__).parent
for module_info in pkgutil.iter_modules([str(package_dir)]):
    # Пропускаем __init__.py
    if module_info.name not in ["__init__"]:
        importlib.import_module(f"{__name__}.{module_info.name}")