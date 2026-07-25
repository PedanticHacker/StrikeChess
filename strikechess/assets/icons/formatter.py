import re
from pathlib import Path


def format_icon_resources() -> None:
    """Restructure icon_resources.py file."""
    icons_directory: Path = Path(__file__).parent
    file_path: Path = icons_directory / "icon_resources.py"

    with open(file_path, encoding="utf-8") as file:
        text: str = file.read()

    formatted_text: str = text.replace("\\\r\n", "").replace("\\\n", "")

    structure_match = re.search(r"qt_resource_struct\s*=\s*(b\".*?\")", formatted_text, re.DOTALL)
    names_match = re.search(r"qt_resource_name\s*=\s*(b\".*?\")", formatted_text, re.DOTALL)
    data_match = re.search(r"qt_resource_data\s*=\s*(b\".*?\")", formatted_text, re.DOTALL)

    if not all([structure_match, names_match, data_match]):
        print("Error: Could not find all required data in icon_resources.py file")
        return

    icon_structure: str = structure_match.group(1)
    icon_names: str = names_match.group(1)
    icon_data: str = data_match.group(1)

    code: str = f"""from PySide6.QtCore import qRegisterResourceData


__version__: Final[str] = "1.0"

icon_compiler_version: int = 3
icon_structure: bytes = {icon_structure}
icon_names: bytes = {icon_names}
icon_data: bytes = {icon_data}
qRegisterResourceData(icon_compiler_version, icon_structure, icon_names, icon_data)
"""

    with open(file_path, mode="w", encoding="utf-8", newline="\n") as file:
        file.write(code)

    print("Formatting complete!")


if __name__ == "__main__":
    format_icon_resources()
