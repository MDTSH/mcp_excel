#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyXLL Registration Script
专门用于注册PyXLL add-in的脚本

Author: Mathema Team
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def detect_architecture():
    """检测系统架构"""
    machine = platform.machine().lower()
    if machine in ['amd64', 'x86_64', 'x64']:
        return 'X64'
    elif machine in ['i386', 'i686', 'x86']:
        return 'Win32'
    else:
        return 'Win32'  # 默认使用Win32

def register_pyxll():
    """注册PyXLL add-in"""
    print("PyXLL Registration Script")
    print("=" * 50)
    
    # 获取MCP根目录
    mcp_root = Path(__file__).parent
    arch = detect_architecture()
    lib_dir = arch
    
    print(f"MCP Root: {mcp_root}")
    print(f"Architecture: {arch}")
    print(f"Lib Directory: {lib_dir}")
    print()
    
    # 检查pyxll.xll文件
    pyxll_xll = mcp_root / "lib" / lib_dir / "pyxll.xll"
    if not pyxll_xll.exists():
        print(f"[ERROR] pyxll.xll not found at {pyxll_xll}")
        return False
    
    print(f"[INFO] Found pyxll.xll at: {pyxll_xll}")
    
    # 检查pyxll模块
    pyxll_module = mcp_root / "pyxll"
    if not pyxll_module.exists():
        print(f"[ERROR] pyxll module not found at {pyxll_module}")
        return False
    
    print(f"[INFO] Found pyxll module at: {pyxll_module}")
    
    # 添加pyxll模块到sys.path
    pyxll_path = str(pyxll_module)
    if pyxll_path not in sys.path:
        sys.path.insert(0, pyxll_path)
    
    # 检查PyXLL模块是否可用
    try:
        import pyxll
        print("[SUCCESS] PyXLL module is available")
    except ImportError as e:
        print(f"[ERROR] Cannot import PyXLL module: {e}")
        return False
    
    # 检查Excel是否运行
    print("\n[INFO] Checking if Excel is running...")
    try:
        import psutil
        excel_running = any('EXCEL.EXE' in proc.name().upper() for proc in psutil.process_iter())
        if excel_running:
            print("[WARNING] Excel is currently running. Please close Excel before registration.")
            print("[INFO] PyXLL registration requires Excel to be closed.")
            response = input("Do you want to continue anyway? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("[INFO] Registration cancelled. Please close Excel and try again.")
                return False
    except ImportError:
        print("[INFO] psutil not available, skipping Excel check")
    
    # 注册PyXLL add-in
    print(f"\n[INFO] Registering PyXLL add-in...")
    print(f"[INFO] PyXLL directory: {pyxll_xll.parent}")
    
    try:
        # Step 1: Install PyXLL
        print("[INFO] Step 1: Installing PyXLL...")
        install_result = subprocess.run([
            sys.executable, "-m", "pyxll", "install", 
            "--install-first", "--non-interactive", 
            str(pyxll_xll.parent)
        ], capture_output=True, text=True, cwd=str(mcp_root), timeout=60)
        
        if install_result.returncode != 0:
            print(f"[WARNING] PyXLL installation failed, trying direct activation...")
            print(f"[INFO] Installation error: {install_result.stderr}")
        
        # Step 2: Activate PyXLL
        print("[INFO] Step 2: Activating PyXLL...")
        activate_result = subprocess.run([
            sys.executable, "-m", "pyxll", "activate", 
            "--non-interactive", str(pyxll_xll.parent)
        ], capture_output=True, text=True, cwd=str(mcp_root), timeout=30)
        
        if activate_result.returncode == 0:
            print("[SUCCESS] PyXLL add-in activated successfully!")
            if activate_result.stdout.strip():
                print("[INFO] Output information:")
                print(activate_result.stdout)
            print("[INFO] Restart Excel to load the add-in")
            print("[INFO] Check Excel Add-ins to ensure PyXLL is loaded")
            return True
        else:
            print(f"[ERROR] PyXLL activation failed:")
            print(f"Return code: {activate_result.returncode}")
            print(f"Error output: {activate_result.stderr}")
            print(f"Standard output: {activate_result.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        print("[ERROR] PyXLL registration timed out after 5 minutes")
        print("[INFO] This might be due to:")
        print("[INFO] 1. PyXLL license activation required")
        print("[INFO] 2. Network connectivity issues")
        print("[INFO] 3. PyXLL server not responding")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to register PyXLL add-in: {str(e)}")
        return False

def main():
    """主函数"""
    print("PyXLL Registration Tool")
    print("=" * 50)
    print()
    
    # 检查是否以管理员身份运行
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            print("[WARNING] Not running as administrator.")
            print("[INFO] Some operations may require administrator privileges.")
            print()
    except:
        pass
    
    # 注册PyXLL
    success = register_pyxll()
    
    if success:
        print("\n" + "=" * 50)
        print("REGISTRATION COMPLETED SUCCESSFULLY")
        print("=" * 50)
        print()
        print("[NEXT STEPS]")
        print("1. Restart Excel")
        print("2. Check Excel Add-ins to ensure PyXLL is loaded")
        print("3. Test MCP functions in Excel")
    else:
        print("\n" + "=" * 50)
        print("REGISTRATION FAILED")
        print("=" * 50)
        print()
        print("[TROUBLESHOOTING]")
        print("1. Make sure Excel is closed")
        print("2. Check PyXLL license activation")
        print("3. Run as administrator if needed")
        print("4. Check network connectivity")
        print("5. Try manual registration:")
        print("   python -m pyxll install lib/X64/pyxll.xll")
    
    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
