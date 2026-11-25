import platform

system = platform.system()
engine_directory = f"strikechess/assets/engines/stockfish-19/{system}"
engine_files = Tree(engine_directory, prefix=engine_directory)

dependency_analysis = Analysis(
    ["main.py"],
    datas=[
        ("NOTICE.txt", "."),
        ("GPL-3.0.txt", "."),
        ("strikechess/settings.json", "strikechess"),
        ("strikechess/assets/audio", "strikechess/assets/audio"),
        ("strikechess/assets/openings.json", "strikechess/assets"),
        ("strikechess/assets/themes", "strikechess/assets/themes"),
        ("strikechess/assets/translations/*.qm", "strikechess/assets/translations"),
    ],
)

bytecode_archive = PYZ(dependency_analysis.pure)

extension = {"Darwin": "icns", "Windows": "ico"}.get(system)
icon_path = f"strikechess/assets/icons/logo.{extension}" if extension else None

executable = EXE(
    bytecode_archive,
    dependency_analysis.scripts,
    console=False,
    icon=icon_path,
    name="StrikeChess",
    exclude_binaries=True,
    target_arch="universal2",
)

if system == "Darwin":
    app = BUNDLE(
        executable,
        dependency_analysis.binaries,
        dependency_analysis.datas,
        engine_files,
        version="1.0",
        icon=icon_path,
        name="StrikeChess.app",
        bundle_identifier="com.pedantichacker.strikechess",
        info_plist={
            "LSMinimumSystemVersion": "14.4",
            "NSHumanReadableCopyright": "Copyright (C) 2026 Boštjan Mejak",
        },
    )
else:
    app = COLLECT(
        executable,
        dependency_analysis.binaries,
        dependency_analysis.datas,
        engine_files,
        name="StrikeChess",
    )
