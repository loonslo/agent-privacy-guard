# Third-party notices

The Windows executable contains a Python runtime and gitleaks. Their license texts
are included in licenses/python.txt and licenses/gitleaks.txt. Gitleaks is MIT
licensed, Copyright (c) 2019 Zachary Rice.

PyInstaller 6.22.0 builds this executable. Its license is included in
licenses/pyinstaller.txt. Its bootloader distribution exception
permits distribution of the generated application under the application's own
terms. See https://pyinstaller.org/en/stable/license.html for the GPL license and
the bootloader exception. PyInstaller is a build dependency; users do not install it.

This project does not bundle Git, MCP SDKs, transformers, torch or model weights.
The executable performs local rule checks and returns advisory results only.
