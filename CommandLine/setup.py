from distutils.core import setup
import py2exe

# This single command below will create a .exe with DLL dependencies
#setup(console=['agsAdmin.py'])

# The commands below create a self contained .exe
import py_compile
excludes = ["Secur32.dll", "SHFOLDER.dll"]
setup(
    name='agsAdmin',
    version='10.1',
    description="""agsAdmin""",
    author="Esri",
    options = {
        "py2exe": {
            "compressed": 1,
            "optimize": 2,
            "ascii": 1,
            "bundle_files": 1,
            "dll_excludes": excludes,
            "packages": ["encodings"],
            "dist_dir": "dist"
            }
        },
    zipfile = None,
    console=["agsAdmin.py"]
    )

