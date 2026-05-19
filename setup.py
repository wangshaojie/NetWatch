from cx_Freeze import setup, Executable

build_options = {
    'packages': ['PyQt5'],
    'excludes': [],
    'include_files': []
}

executables = [
    Executable(
        'netwatch.py',
        base='gui',  # GUI模式，不显示控制台窗口
        target_name='NetWatch.exe'
    )
]

setup(
    name='NetWatch',
    version='1.0',
    description='Windows Port Manager',
    options={'build_exe': build_options},
    executables=executables
)
