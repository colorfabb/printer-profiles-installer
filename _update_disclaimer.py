import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_pattern = r'DISCLAIMER_TEXT = """.*?"""'
new_text = r'''DISCLAIMER_TEXT = """colorFabb Profile Installer – Disclaimer / Important Information (Free Tool)

This free installer downloads and installs 3D printing profiles ("Profiles") maintained by colorFabb from a public GitHub repository and copies them into configuration folders used by the following third-party slicing applications:

• PrusaSlicer
• OrcaSlicer
• Bambu Studio

By continuing, you acknowledge and agree that:

Third-party software
PrusaSlicer, OrcaSlicer, and Bambu Studio are owned and controlled by third parties. colorFabb does not guarantee compatibility with any specific slicer version, operating system version, or system configuration.

Overwriting existing files
The installer may create, modify, or overwrite profile files in the target slicer's configuration directories. If a profile file with the same filename already exists, it may be replaced. You are responsible for backing up your existing profiles and settings before proceeding.

System changes
The installer writes files into user-level application data folders (such as Windows AppData or macOS Application Support) used by your slicers. These changes may affect slicer behavior, available presets, and print results.

Use at your own risk
Profiles are provided "AS IS" and may not be suitable for your printer, firmware, hardware setup, material batch, environment, or intended use. Incorrect settings may cause failed prints, reduced quality, excessive wear, or equipment damage. Always review profile settings and perform a test print before production use.

No warranties
To the maximum extent permitted by law, colorFabb disclaims all warranties, express or implied, including merchantability, fitness for a particular purpose, and non-infringement.

Limitation of liability
To the maximum extent permitted by law, colorFabb is not liable for any direct, indirect, incidental, special, consequential, or exemplary damages, including loss of data, loss of profits, business interruption, hardware damage, or any other loss arising out of or related to the use of this installer or the Profiles, even if advised of the possibility of such damages.

Network and source availability
Installation requires internet access to download content from GitHub. colorFabb does not guarantee availability, integrity, or continued access to remote resources, and installation may fail or be incomplete due to network conditions or repository changes.

If you do not agree, cancel the installation.

[ ] I have read and understand the above, including the overwrite warning, and I want to continue.
"""'''

content_new = re.sub(old_pattern, new_text, content, count=1, flags=re.DOTALL)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content_new)

print('✓ Updated DISCLAIMER_TEXT successfully')
