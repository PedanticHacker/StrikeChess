import platform

system = platform.system()
engine_directory = f"assets/engines/stockfish-18/{system}"

dependency_analysis = Analysis(
    ["main.py"],
    datas=[
        ("strikechess/assets/Linux", "assets/Linux"),
        ("strikechess/assets/audio", "assets/audio"),
        ("strikechess/assets/icons", "assets/icons"),
        ("strikechess/assets/themes", "assets/themes"),
        ("strikechess/assets/translations", "assets/translations"),
        (f"strikechess/{engine_directory}", engine_directory),
        ("strikechess/settings.json", "."),
    ],
)

bytecode_archive = PYZ(dependency_analysis.pure, dependency_analysis.zipped_data)

extension = {"Darwin": "icns", "Windows": "ico"}.get(system)
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
