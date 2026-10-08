import platform

system = platform.system()
is_macos = system == "Darwin"
engine_directory = f"assets/engines/stockfish-18/{system}"

dependency_analysis = Analysis(
    ["main.py"],
    datas=[
        ("strikechess/settings.json", "."),
        ("strikechess/assets/audio", "assets/audio"),
        ("strikechess/assets/openings.json", "assets"),
        ("strikechess/assets/themes", "assets/themes"),
        (f"strikechess/{engine_directory}", engine_directory),
        ("strikechess/assets/translations", "assets/translations"),
    ],
)

bytecode_archive = PYZ(dependency_analysis.pure, dependency_analysis.zipped_data)

extension = {"Darwin": "icns", "Windows": "ico"}.get(system)
icon_path = f"strikechess/assets/icons/logo.{extension}" if extension else None

if is_macos:
    executable = EXE(
        bytecode_archive,
        dependency_analysis.scripts,
        console=False,
        icon=icon_path,
        name="StrikeChess",
        exclude_binaries=True,
    )

    app = BUNDLE(
        executable,
        dependency_analysis.binaries,
        dependency_analysis.zipfiles,
        dependency_analysis.datas,
        version="1.0",
        icon=icon_path,
        name="StrikeChess.app",
        bundle_identifier="com.pedantichacker.strikechess",
        info_plist={
            "LSMinimumSystemVersion": "14.4",
            "NSHumanReadableCopyright": "© 2026 Boštjan Mejak",
        },
    )
else:
    executable = EXE(
        bytecode_archive,
        dependency_analysis.scripts,
        dependency_analysis.binaries,
        dependency_analysis.zipfiles,
        dependency_analysis.datas,
        console=False,
        icon=icon_path,
        name="StrikeChess",
    )
