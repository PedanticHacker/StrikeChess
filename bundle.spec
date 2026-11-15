import platform

system = platform.system()
engine_directory = f"assets/engines/stockfish-19/{system}"
engine_files = Tree(f"strikechess/{engine_directory}", prefix=engine_directory)

dependency_analysis = Analysis(
    ["main.py"],
    datas=[
        ("NOTICE.txt", "."),
        ("GPL-3.0.txt", "."),
        ("strikechess/settings.json", "."),
        ("strikechess/assets/audio", "assets/audio"),
        ("strikechess/assets/openings.json", "assets"),
        ("strikechess/assets/themes", "assets/themes"),
        ("strikechess/assets/translations/*.qm", "assets/translations"),
    ],
)

bytecode_archive = PYZ(dependency_analysis.pure, dependency_analysis.zipped_data)

extension = {"Darwin": "icns", "Windows": "ico"}.get(system)
icon_path = f"strikechess/assets/icons/logo.{extension}" if extension else None

if system == "Darwin":
    executable = EXE(
        bytecode_archive,
        dependency_analysis.scripts,
        console=False,
        icon=icon_path,
        name="StrikeChess",
        exclude_binaries=True,
        target_arch="universal2",
    )

    app = BUNDLE(
        executable,
        dependency_analysis.binaries,
        dependency_analysis.zipfiles,
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
    executable = EXE(
        bytecode_archive,
        dependency_analysis.scripts,
        dependency_analysis.binaries,
        dependency_analysis.zipfiles,
        dependency_analysis.datas,
        engine_files,
        console=False,
        icon=icon_path,
        name="StrikeChess",
    )
