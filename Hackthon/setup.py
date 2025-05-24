import os
import sys
import subprocess
from PIL import Image

def create_icon():
    """Create icon files from the idle.gif"""
    try:
        # Read the first frame of the GIF
        with Image.open('idle.gif') as img:
            img.seek(0)  # Get first frame
            
            # For Windows: create .ico file
            icon_sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
            icon_path = 'icon.ico'
            img.save(icon_path, sizes=icon_sizes)
            print(f"Created Windows icon: {icon_path}")
            
            # For macOS: create .icns file
            if sys.platform == 'darwin':
                # Create temporary iconset directory
                iconset_path = 'icon.iconset'
                os.makedirs(iconset_path, exist_ok=True)
                
                # Generate different sizes
                for size in [16, 32, 64, 128, 256, 512]:
                    # Normal resolution
                    resized = img.resize((size, size), Image.Resampling.LANCZOS)
                    resized.save(f'{iconset_path}/icon_{size}x{size}.png')
                    
                    # High resolution (2x)
                    if size <= 256:  # macOS doesn't use 1024x1024
                        resized = img.resize((size*2, size*2), Image.Resampling.LANCZOS)
                        resized.save(f'{iconset_path}/icon_{size}x{size}@2x.png')
                
                # Convert to icns using iconutil
                os.system(f'iconutil -c icns {iconset_path}')
                print("Created macOS icon: icon.icns")
                
                # Clean up iconset directory
                for file in os.listdir(iconset_path):
                    os.remove(os.path.join(iconset_path, file))
                os.rmdir(iconset_path)
            
            return True
    except Exception as e:
        print(f"Error creating icons: {str(e)}")
        return False

def install_requirements():
    """Install required packages"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {str(e)}")
        return False

def main():
    # Ensure we're in the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("Setting up Desktop Pet...")
    
    # Install requirements
    print("\nInstalling required packages...")
    if not install_requirements():
        print("Failed to install requirements. Please try installing them manually.")
        return
    
    # Create icons
    print("\nCreating application icons...")
    if not create_icon():
        print("Failed to create icons. The application will use default system icons.")
    
    # Run the installer
    print("\nRunning installer...")
    import install
    install.main()

if __name__ == '__main__':
    main() 