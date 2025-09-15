#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MCP Installation Helper Script
Mathema Calculation Plus - Installation Assistant

This script provides additional functionality for the MCP installation process,
including Excel detection, PyXLL configuration, and system validation.

Author: Mathema Team
Version: 1.4.0
"""

import os
import sys
import platform
import subprocess
import winreg
import shutil
from pathlib import Path
from typing import Optional, Tuple, List

class MCPInstaller:
    """MCP Installation Helper Class"""
    
    def __init__(self, mcp_root: str):
        self.mcp_root = Path(mcp_root)
        self.arch = self._detect_architecture()
        self.lib_dir = "X64" if self.arch == "x64" else "Win32"
        
    def _detect_architecture(self) -> str:
        """Detect system architecture"""
        machine = platform.machine().lower()
        # Handle different architecture naming conventions
        if machine in ['amd64', 'x86_64', 'x64']:
            return 'x64'
        elif machine in ['i386', 'i686', 'x86']:
            return 'x86'
        else:
            return machine
    
    def check_python_version(self) -> Tuple[bool, str]:
        """Check if Python 3.9.x is installed"""
        try:
            version_info = sys.version_info
            if version_info.major == 3 and version_info.minor == 9:
                return True, f"{version_info.major}.{version_info.minor}.{version_info.micro}"
            else:
                return False, f"{version_info.major}.{version_info.minor}.{version_info.micro}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def find_excel_installation(self) -> List[dict]:
        """Find Excel installation paths"""
        excel_paths = []
        
        # Common Excel installation paths
        search_paths = [
            r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE",
            r"C:\Program Files\Microsoft Office\Office16\EXCEL.EXE",
            r"C:\Program Files (x86)\Microsoft Office\Office16\EXCEL.EXE",
            r"C:\Program Files\Microsoft Office\Office15\EXCEL.EXE",
            r"C:\Program Files (x86)\Microsoft Office\Office15\EXCEL.EXE",
            r"C:\Program Files\Microsoft Office\Office14\EXCEL.EXE",
            r"C:\Program Files (x86)\Microsoft Office\Office14\EXCEL.EXE",
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                # Determine architecture based on path
                arch = "x64" if "Program Files\\" in path and "Program Files (x86)" not in path else "x86"
                
                # Try to get version info
                version = self._get_excel_version(path)
                
                excel_paths.append({
                    'path': path,
                    'architecture': arch,
                    'version': version,
                    'found': True
                })
        
        return excel_paths
    
    def _get_excel_version(self, excel_path: str) -> str:
        """Get Excel version from executable"""
        try:
            # Use PowerShell to get version info
            cmd = f'Get-ItemProperty "{excel_path}" | Select-Object -ExpandProperty VersionInfo | Select-Object -ExpandProperty ProductVersion'
            result = subprocess.run(['powershell', '-Command', cmd], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return "Unknown"
    
    def find_excel_startup_directories(self) -> List[str]:
        """Find Excel startup directories for add-in installation"""
        startup_dirs = []
        
        # Common Excel startup directories
        potential_dirs = [
            os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Excel', 'XLSTART'),
            os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'AddIns'),
            r"C:\Program Files\Microsoft Office\root\Office16\XLSTART",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\XLSTART",
            r"C:\Program Files\Microsoft Office\Office16\XLSTART",
            r"C:\Program Files (x86)\Microsoft Office\Office16\XLSTART",
        ]
        
        for dir_path in potential_dirs:
            if os.path.exists(dir_path):
                startup_dirs.append(dir_path)
        
        return startup_dirs
    
    def update_pyxll_config(self, python_exe: str) -> bool:
        """Update pyxll.cfg with correct Python executable path"""
        try:
            pyxll_cfg = self.mcp_root / "lib" / self.lib_dir / "pyxll.cfg"
            
            if not pyxll_cfg.exists():
                print(f"[ERROR] pyxll.cfg not found at {pyxll_cfg}")
                return False
            
            # Read current config
            with open(pyxll_cfg, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Update executable line
            updated_lines = []
            for line in lines:
                if line.strip().startswith('executable ='):
                    updated_lines.append(f"executable = {python_exe}\n")
                else:
                    updated_lines.append(line)
            
            # Write updated config
            with open(pyxll_cfg, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
            
            print(f"[SUCCESS] Updated pyxll.cfg with Python path: {python_exe}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to update pyxll.cfg: {str(e)}")
            return False
    
    def install_pyxll_addin(self) -> bool:
        """Install PyXLL add-in using local PyXLL module"""
        try:
            pyxll_xll = self.mcp_root / "lib" / self.lib_dir / "pyxll.xll"
            pyxll_module = self.mcp_root / "pyxll"
            
            if not pyxll_xll.exists():
                print(f"[ERROR] pyxll.xll not found at {pyxll_xll}")
                return False
            
            if not pyxll_module.exists():
                print(f"[ERROR] pyxll module not found at {pyxll_module}")
                return False
            
            # Add pyxll module to sys.path if not already there
            pyxll_path = str(pyxll_module)
            if pyxll_path not in sys.path:
                sys.path.insert(0, pyxll_path)
            
            # Check if PyXLL module can be imported
            try:
                import pyxll
                print("[SUCCESS] PyXLL module is available")
            except ImportError as e:
                print(f"[ERROR] Cannot import PyXLL module: {e}")
                return False
            
            print(f"[INFO] Registering {self.lib_dir} version PyXLL...")
            print(f"[INFO] PyXLL directory: {pyxll_xll.parent}")
            
            # Step 1: Install PyXLL
            print("[INFO] Step 1: Installing PyXLL...")
            install_result = subprocess.run([
                sys.executable, "-m", "pyxll", "install", 
                "--install-first", "--non-interactive", 
                str(pyxll_xll.parent)
            ], capture_output=True, text=True, cwd=str(self.mcp_root), timeout=60)
            
            if install_result.returncode != 0:
                print(f"[WARNING] PyXLL installation failed, trying direct activation...")
                print(f"[INFO] Installation error: {install_result.stderr}")
            
            # Step 2: Activate PyXLL
            print("[INFO] Step 2: Activating PyXLL...")
            activate_result = subprocess.run([
                sys.executable, "-m", "pyxll", "activate", 
                "--non-interactive", str(pyxll_xll.parent)
            ], capture_output=True, text=True, cwd=str(self.mcp_root), timeout=30)
            
            if activate_result.returncode == 0:
                print(f"[SUCCESS] {self.lib_dir} version PyXLL activated successfully!")
                if activate_result.stdout.strip():
                    print("[INFO] Output information:")
                    print(activate_result.stdout)
                print("[INFO] Restart Excel to load the add-in")
                return True
            else:
                print(f"[ERROR] {self.lib_dir} version PyXLL activation failed!")
                if activate_result.stderr.strip():
                    print("[INFO] Error information:")
                    print(activate_result.stderr)
                print("[INFO] This might be due to:")
                print("[INFO] 1. PyXLL license not activated")
                print("[INFO] 2. Excel not closed during registration")
                print("[INFO] 3. Permission issues")
                print("[INFO] You can manually register using:")
                print(f"[INFO] python -m pyxll install {pyxll_xll.parent}")
                return False
            
        except subprocess.TimeoutExpired:
            print("[ERROR] PyXLL registration timed out")
            print("[INFO] This might be due to:")
            print("[INFO] 1. PyXLL license activation required")
            print("[INFO] 2. Excel not closed during registration")
            print("[INFO] 3. Network connectivity issues")
            print("[INFO] You can manually register using:")
            print(f"[INFO] python -m pyxll install {pyxll_xll.parent}")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to register PyXLL add-in: {str(e)}")
            return False
    
    def test_mcp_import(self) -> bool:
        """Test if MCP can be imported successfully"""
        try:
            # Add MCP paths to sys.path
            mcp_paths = [
                str(self.mcp_root),
                str(self.mcp_root / "lib" / self.lib_dir)
            ]
            
            for path in mcp_paths:
                if path not in sys.path:
                    sys.path.insert(0, path)
            
            # Test import
            import mcp
            print("[SUCCESS] MCP library imported successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] MCP import test failed: {str(e)}")
            return False
    
    def install_python_dependencies(self) -> bool:
        """Install Python dependencies from requirements.txt"""
        try:
            requirements_file = self.mcp_root / "requirements.txt"
            
            if not requirements_file.exists():
                print(f"[ERROR] requirements.txt not found at {requirements_file}")
                return False
            
            # Upgrade pip first
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            
            # Install minimal requirements
            result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("[SUCCESS] Essential Python dependencies installed successfully")
                print("[INFO] For additional features, install optional dependencies:")
                print("[INFO] pip install -r requirements-optional.txt")
                return True
            else:
                print(f"[ERROR] Failed to install dependencies: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Failed to install Python dependencies: {str(e)}")
            return False
    
    def setup_pythonpath(self) -> bool:
        """Setup PYTHONPATH environment variable"""
        try:
            mcp_paths = [
                str(self.mcp_root),
                str(self.mcp_root / "lib" / self.lib_dir),
                str(self.mcp_root / "pyxll")  # Add pyxll directory
            ]
            
            # Get current PYTHONPATH
            current_pythonpath = os.environ.get('PYTHONPATH', '')
            
            # Add MCP paths if not already present
            updated_paths = []
            for path in mcp_paths:
                if path not in current_pythonpath:
                    updated_paths.append(path)
            
            if updated_paths:
                new_pythonpath = ';'.join(updated_paths)
                if current_pythonpath:
                    new_pythonpath = current_pythonpath + ';' + new_pythonpath
                
                # Set for current session
                os.environ['PYTHONPATH'] = new_pythonpath
                
                # Set system environment variable
                try:
                    subprocess.run(['setx', 'PYTHONPATH', new_pythonpath], 
                                 check=True, capture_output=True)
                    print("[SUCCESS] PYTHONPATH updated successfully")
                except subprocess.CalledProcessError:
                    print("[WARNING] Failed to set system PYTHONPATH, but current session is updated")
                
                return True
            else:
                print("[INFO] MCP paths already in PYTHONPATH")
                return True
                
        except Exception as e:
            print(f"[ERROR] Failed to setup PYTHONPATH: {str(e)}")
            return False

def main():
    """Main installation function"""
    print("MCP Installation Helper")
    print("=" * 50)
    
    # Get MCP root directory
    mcp_root = os.path.dirname(os.path.abspath(__file__))
    installer = MCPInstaller(mcp_root)
    
    print(f"MCP Root: {mcp_root}")
    print(f"Architecture: {installer.arch}")
    print(f"Lib Directory: {installer.lib_dir}")
    print()
    
    # Check Python version
    print("Checking Python version...")
    is_valid, version = installer.check_python_version()
    if is_valid:
        print(f"[SUCCESS] Python {version} is compatible")
    else:
        print(f"[ERROR] Python {version} is not compatible. Python 3.9.x is required.")
        return False
    
    # Install Python dependencies
    print("\nInstalling Python dependencies...")
    installer.install_python_dependencies()
    
    # Setup PYTHONPATH
    print("\nSetting up PYTHONPATH...")
    installer.setup_pythonpath()
    
    # Test MCP import
    print("\nTesting MCP import...")
    installer.test_mcp_import()
    
    # Find Excel installations (optional)
    print("\nSearching for Excel installations...")
    excel_installations = installer.find_excel_installation()
    
    if excel_installations:
        print(f"[SUCCESS] Found {len(excel_installations)} Excel installation(s):")
        for excel in excel_installations:
            print(f"  - {excel['path']} ({excel['architecture']}, v{excel['version']})")
        
        # Ask user if they want Excel integration
        print("\n[INFO] Excel integration is optional and requires PyXLL commercial license.")
        print("[INFO] PyXLL module and add-in files are included in MCP.")
        print("[INFO] Do you want to configure Excel integration? (y/N): ", end="")
        
        try:
            user_input = input().strip().lower()
            if user_input in ['y', 'yes']:
                # Update PyXLL config
                print("\nUpdating PyXLL configuration...")
                installer.update_pyxll_config(sys.executable)
                
                # Register PyXLL add-in
                print("\nRegistering PyXLL add-in...")
                installer.install_pyxll_addin()
            else:
                print("[INFO] Skipping Excel integration. You can configure it later if needed.")
                print("[INFO] To configure Excel integration later, run:")
                print(f"[INFO] python {installer.mcp_root}/register_pyxll.py")
                print(f"[INFO] or: python -m pyxll install {installer.mcp_root}/lib/{installer.lib_dir}/pyxll.xll")
        except KeyboardInterrupt:
            print("\n[INFO] Skipping Excel integration.")
        
    else:
        print("[INFO] No Excel installations found. Excel integration will be skipped.")
        print("[INFO] You can install Excel integration later if needed.")
    
    print("\nInstallation helper completed!")
    return True

if __name__ == "__main__":
    main()
