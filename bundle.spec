import platform

dependency_analysis = Analysis(
    ["main.py"],
    datas=[
        ("strikechess/assets", "assets"),
        ("strikechess/settings.json", "."),
    ],
)

bytecode_archive = PYZ(dependency_analysis.pure, dependency_analysis.zipped_data)

extension = {"Darwin": "icns", "Windows": "ico"}.get(platform.system())
icon_path = f"strikechess/assets/icons/logo.{extension}" if extension else None

executable = EXE(
    bytecode_archive,
    dependency_analysis.scripts,
    dependency_analysis.binaries,
    dependency_analysis.zipfiles,
    dependency_analysis.datas,
    name="StrikeChess",
    console=False,
    icon=icon_path,
)
