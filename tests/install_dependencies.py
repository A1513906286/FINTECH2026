"""
Face Recognition Dependencies Installer
自动安装所有Face ID功能所需的依赖
"""

import subprocess
import sys

def run_command(command, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print(f"[OK] {description} - Success!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} - Failed!")
        print(e.stderr)
        return False

def main():
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║     Face Recognition Dependencies Installer            ║
    ║     Face ID 依赖自动安装程序                           ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    # 检查Python版本
    print(f"\n[1/5] Checking Python version...")
    print(f"Python version: {sys.version}")
    
    if sys.version_info < (3, 7):
        print("[ERROR] Python 3.7+ is required!")
        input("Press Enter to exit...")
        sys.exit(1)
    
    print("[OK] Python version is compatible")
    
    # 安装基础依赖
    packages = [
        ("numpy", "NumPy - Numerical computing library"),
        ("Pillow", "Pillow - Image processing library"),
        ("opencv-python", "OpenCV - Computer vision library"),
    ]
    
    step = 2
    for package, description in packages:
        success = run_command(
            f"pip install {package}",
            f"[{step}/5] Installing {description}"
        )
        if not success:
            print(f"\n[WARNING] Failed to install {package}, but continuing...")
        step += 1
    
    # 安装dlib（可能失败）
    print(f"\n{'='*60}")
    print(f"  [{step}/5] Installing dlib (may take several minutes)")
    print(f"{'='*60}")
    print("\nNote: If dlib installation fails, you have two options:")
    print("  Option 1: conda install -c conda-forge dlib")
    print("  Option 2: Download precompiled wheel from:")
    print("            https://github.com/z-mahmud22/Dlib_Windows_Python3.x")
    print("\nAttempting to install dlib...")
    
    dlib_success = run_command("pip install dlib", "Installing dlib")
    
    if not dlib_success:
        print("\n" + "="*60)
        print("  [WARNING] dlib installation failed!")
        print("="*60)
        print("\nPlease install dlib manually using one of these methods:")
        print("\n1. Using conda (recommended):")
        print("   conda install -c conda-forge dlib")
        print("\n2. Using precompiled wheel:")
        print("   a. Download from: https://github.com/z-mahmud22/Dlib_Windows_Python3.x")
        print("   b. Install: pip install dlib-19.xx.x-cpXX-cpXX-win_amd64.whl")
        print("\nAfter installing dlib, run this script again.")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    step += 1
    
    # 安装face_recognition
    success = run_command(
        "pip install face_recognition",
        f"[{step}/5] Installing face_recognition"
    )
    
    if not success:
        print("\n[ERROR] face_recognition installation failed!")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # 完成
    print(f"\n{'='*60}")
    print("  Installation Complete!")
    print("  所有依赖安装完成！")
    print(f"{'='*60}")
    
    print("\nNext steps:")
    print("  1. Run: python test_face_recognition.py")
    print("  2. Run: python init_db.py")
    print("  3. Run: python app.py")
    print("  4. Visit: http://127.0.0.1:5000/test_face_id")
    
    print("\n下一步:")
    print("  1. 运行: python test_face_recognition.py")
    print("  2. 运行: python init_db.py")
    print("  3. 运行: python app.py")
    print("  4. 访问: http://127.0.0.1:5000/test_face_id")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()

