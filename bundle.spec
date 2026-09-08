import platform

system = platform.system()
engine_directory = f"assets/engines/stockfish-18/{system}"
is_macos = system == "Darwin"

dependency_analysis = Analysis(
    ["main.py"],
    datas=[
        ("strikechess/assets/audio", "assets/audio"),
        ("strikechess/assets/openings.json", "assets"),
        ("strikechess/assets/themes", "assets/themes"),
        ("strikechess/assets/translations", "assets/translations"),
        (f"strikechess/{engine_directory}", engine_directory),
        ("strikechess/settings.json", "."),
    ],
)

bytecode_archive = PYZ(dependency_analysis.pure, dependency_analysis.zipped_data)

extension = {"Darwin": "icns", "Windows": "ico"}.get(system)
icon_path = f"strikechess/assets/icons/logo.{extension}" if extension else None

if is_macos:
    executable = EXE(
        bytecode_archive,
        dependency_analysis.scripts,
        exclude_binaries=True,
        name="StrikeChess",
        console=False,
        icon=icon_path,
    )

    app = BUNDLE(
        executable,
        dependency_analysis.binaries,
        dependency_analysis.zipfiles,
        dependency_analysis.datas,
        name="StrikeChess.app",
        icon=icon_path,
        bundle_identifier="com.pedantichacker.strikechess",
        version="1.0",
        info_plist={"NSHumanReadableCopyright": "© 2026 Boštjan Mejak"},
    )
else:
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
