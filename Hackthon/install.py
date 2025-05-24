import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path

def create_mac_app():
    """Create a macOS .app bundle"""
    # Get the user's Applications folder
    apps_dir = os.path.expanduser('~/Applications')
    app_name = "Desktop Pet.app"
    app_path = os.path.join(apps_dir, app_name)
    
    # Create the basic .app structure
    os.makedirs(os.path.join(app_path, 'Contents', 'MacOS'), exist_ok=True)
    os.makedirs(os.path.join(app_path, 'Contents', 'Resources'), exist_ok=True)
    
    # Create Info.plist
    info_plist = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>DesktopPet</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.desktoppet.app</string>
    <key>CFBundleName</key>
    <string>Desktop Pet</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.10</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>'''
    
    with open(os.path.join(app_path, 'Contents', 'Info.plist'), 'w') as f:
        f.write(info_plist)
    
    # Create Python virtual environment in the app bundle
    resources_dir = os.path.join(app_path, 'Contents', 'Resources')
    venv_dir = os.path.join(resources_dir, 'venv')
    subprocess.check_call([sys.executable, '-m', 'venv', venv_dir])
    
    # Get the Python interpreter path in the virtual environment
    if sys.platform == 'darwin':
        venv_python = os.path.join(venv_dir, 'bin', 'python3')
        pip_path = os.path.join(venv_dir, 'bin', 'pip3')
    else:
        venv_python = os.path.join(venv_dir, 'Scripts', 'python.exe')
        pip_path = os.path.join(venv_dir, 'Scripts', 'pip.exe')
    
    # Install required packages in the virtual environment
    subprocess.check_call([pip_path, 'install', 'PySide6'])
    
    # Create data directory
    data_dir = os.path.join(resources_dir, '.desktop_pet')
    os.makedirs(data_dir, exist_ok=True)
    
    # Create the launcher script
    launcher_script = f'''#!/bin/bash
cd "{resources_dir}"
export PYTHONPATH="{resources_dir}"
export DESKTOP_PET_DATA="{data_dir}"
"{venv_python}" desktop_pet.py
'''
    
    launcher_path = os.path.join(app_path, 'Contents', 'MacOS', 'DesktopPet')
    with open(launcher_path, 'w') as f:
        f.write(launcher_script)
    os.chmod(launcher_path, 0o755)
    
    # Copy the application files
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Copy all Python files
    python_files = ['desktop_pet.py', 'ui_style.py']
    for file in python_files:
        if os.path.exists(os.path.join(current_dir, file)):
            shutil.copy2(os.path.join(current_dir, file), resources_dir)
    
    # Copy GIF files
    for gif in ['idle.gif', 'happy.gif', 'moving.gif']:
        if os.path.exists(os.path.join(current_dir, gif)):
            shutil.copy2(os.path.join(current_dir, gif), resources_dir)
    
    print(f"Created application bundle at {app_path}")
    return app_path

def create_windows_shortcut():
    """Create Windows shortcuts"""
    import winshell
    from win32com.client import Dispatch
    
    # Get paths
    desktop = winshell.desktop()
    start_menu = winshell.start_menu()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create Python virtual environment
    venv_dir = os.path.join(current_dir, 'venv')
    subprocess.check_call([sys.executable, '-m', 'venv', venv_dir])
    
    # Get the Python interpreter path in the virtual environment
    venv_python = os.path.join(venv_dir, 'Scripts', 'python.exe')
    pip_path = os.path.join(venv_dir, 'Scripts', 'pip.exe')
    
    # Install required packages in the virtual environment
    subprocess.check_call([pip_path, 'install', 'PySide6'])
    
    # Create data directory
    data_dir = os.path.join(current_dir, '.desktop_pet')
    os.makedirs(data_dir, exist_ok=True)
    
    # Create a launcher script
    launcher_script = f'''@echo off
cd /d "{current_dir}"
set PYTHONPATH={current_dir}
set DESKTOP_PET_DATA={data_dir}
start /min "" "{venv_python}" desktop_pet.py
'''
    launcher_path = os.path.join(current_dir, 'launch_pet.bat')
    with open(launcher_path, 'w') as f:
        f.write(launcher_script)
    
    # Create shortcut
    shell = Dispatch('WScript.Shell')
    
    # Use .ico file if available, otherwise fallback to .gif
    icon_path = os.path.join(current_dir, 'icon.ico')
    if not os.path.exists(icon_path):
        icon_path = os.path.join(current_dir, 'idle.gif')
    
    # Desktop shortcut
    shortcut_path = os.path.join(desktop, "Desktop Pet.lnk")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = 'cmd.exe'
    shortcut.Arguments = f'/c "{launcher_path}"'
    shortcut.WorkingDirectory = current_dir
    shortcut.IconLocation = icon_path
    shortcut.WindowStyle = 7  # Minimized
    shortcut.save()
    
    # Start Menu shortcut
    start_menu_path = os.path.join(start_menu, "Programs", "Desktop Pet.lnk")
    os.makedirs(os.path.dirname(start_menu_path), exist_ok=True)
    shortcut = shell.CreateShortCut(start_menu_path)
    shortcut.Targetpath = 'cmd.exe'
    shortcut.Arguments = f'/c "{launcher_path}"'
    shortcut.WorkingDirectory = current_dir
    shortcut.IconLocation = icon_path
    shortcut.WindowStyle = 7  # Minimized
    shortcut.save()
    
    print(f"Created shortcuts at:\n{shortcut_path}\n{start_menu_path}")

def create_linux_desktop_entry():
    """Create Linux .desktop file"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create Python virtual environment
    venv_dir = os.path.join(current_dir, 'venv')
    subprocess.check_call([sys.executable, '-m', 'venv', venv_dir])
    
    # Get the Python interpreter path in the virtual environment
    venv_python = os.path.join(venv_dir, 'bin', 'python3')
    pip_path = os.path.join(venv_dir, 'bin', 'pip3')
    
    # Install required packages in the virtual environment
    subprocess.check_call([pip_path, 'install', 'PySide6'])
    
    # Create data directory
    data_dir = os.path.join(current_dir, '.desktop_pet')
    os.makedirs(data_dir, exist_ok=True)
    
    # Create a launcher script
    launcher_script = f'''#!/bin/bash
cd "{current_dir}"
export PYTHONPATH="{current_dir}"
export DESKTOP_PET_DATA="{data_dir}"
"{venv_python}" desktop_pet.py
'''
    launcher_path = os.path.join(current_dir, 'launch_pet.sh')
    with open(launcher_path, 'w') as f:
        f.write(launcher_script)
    os.chmod(launcher_path, 0o755)
    
    # Use .ico file if available, otherwise fallback to .gif
    icon_path = os.path.join(current_dir, 'icon.ico')
    if not os.path.exists(icon_path):
        icon_path = os.path.join(current_dir, 'idle.gif')
    
    # Create .desktop file content
    desktop_entry = f'''[Desktop Entry]
Version=1.0
Type=Application
Name=Desktop Pet
Comment=A cute desktop pet
Exec=bash -c 'cd "{current_dir}" && PYTHONPATH="{current_dir}" DESKTOP_PET_DATA="{data_dir}" "{venv_python}" desktop_pet.py'
Icon={icon_path}
Terminal=false
Categories=Utility;
StartupNotify=true
'''
    
    # Save to user's applications directory
    apps_dir = os.path.expanduser('~/.local/share/applications')
    os.makedirs(apps_dir, exist_ok=True)
    desktop_file = os.path.join(apps_dir, 'desktop-pet.desktop')
    
    with open(desktop_file, 'w') as f:
        f.write(desktop_entry)
    
    # Make it executable
    os.chmod(desktop_file, 0o755)
    
    # Create symbolic link on desktop
    desktop_dir = os.path.expanduser('~/Desktop')
    desktop_link = os.path.join(desktop_dir, 'Desktop Pet')
    
    if os.path.exists(desktop_link):
        os.remove(desktop_link)
    os.symlink(desktop_file, desktop_link)
    
    print(f"Created application shortcut at {desktop_file} and desktop link at {desktop_link}")

def main():
    """Main installation function"""
    system = platform.system().lower()
    
    print("Installing Desktop Pet...")
    
    try:
        if system == 'darwin':
            app_path = create_mac_app()
            print(f"\nInstallation complete! You can find Desktop Pet in your Applications folder and Launchpad.")
            print(f"To uninstall, simply delete {app_path}")
            
        elif system == 'windows':
            create_windows_shortcut()
            print("\nInstallation complete! You can find Desktop Pet shortcuts on your Desktop and Start Menu.")
            print("To uninstall, simply delete the shortcuts and the program folder.")
            
        elif system == 'linux':
            create_linux_desktop_entry()
            print("\nInstallation complete! You can find Desktop Pet in your applications menu and on your desktop.")
            print("To uninstall, delete the .desktop file and the program folder.")
            
        else:
            print(f"Sorry, your operating system ({system}) is not supported.")
            return
        
    except Exception as e:
        print(f"An error occurred during installation: {str(e)}")
        return

if __name__ == '__main__':
    main() 