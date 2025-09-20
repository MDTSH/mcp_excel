#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MCP Installation Test Script
Quick test to verify installation components

Author: Mathema Team
"""

import os
import sys
import platform
from pathlib import Path

def test_python_version():
    """Test Python version compatibility"""
    print("Testing Python version...")
    version_info = sys.version_info
    print(f"  Python version: {version_info.major}.{version_info.minor}.{version_info.micro}")
    
    if version_info.major == 3 and version_info.minor == 9:
        print("  ✓ Python 3.9.x is compatible")
        return True
    else:
        print("  ✗ Python 3.9.x is required")
        return False

def test_system_architecture():
    """Test system architecture"""
    print("\nTesting system architecture...")
    arch = platform.machine().lower()
    print(f"  Architecture: {arch}")
    
    if arch in ['amd64', 'x86_64']:
        print("  ✓ 64-bit system detected")
        return "X64"
    else:
        print("  ✓ 32-bit system detected")
        return "Win32"

def test_mcp_files():
    """Test MCP file structure"""
    print("\nTesting MCP file structure...")
    mcp_root = Path(__file__).parent
    
    required_files = [
        "requirements.txt",
        "quick_install.bat",
        "install_helper.py"
    ]
    
    all_found = True
    for file_path in required_files:
        full_path = mcp_root / file_path
        if full_path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} - MISSING")
            all_found = False
    
    return all_found

def test_lib_directories():
    """Test library directories"""
    print("\nTesting library directories...")
    mcp_root = Path(__file__).parent
    lib_dir = mcp_root / "lib"
    
    if not lib_dir.exists():
        print("  ✗ lib/ directory not found")
        return False
    
    arch_dirs = ["X64", "Win32"]
    for arch_dir in arch_dirs:
        arch_path = lib_dir / arch_dir
        if arch_path.exists():
            print(f"  ✓ lib/{arch_dir}/ directory found")
            
            # Check for required files
            required_files = ["_mcp.pyd", "pyxll.xll", "pyxll.cfg"]
            for file_name in required_files:
                file_path = arch_path / file_name
                if file_path.exists():
                    print(f"    ✓ {file_name}")
                else:
                    print(f"    ✗ {file_name} - MISSING")
        else:
            print(f"  ✗ lib/{arch_dir}/ directory not found")
    
    return True

def test_pythonpath():
    """Test PYTHONPATH configuration"""
    print("\nTesting PYTHONPATH...")
    mcp_root = str(Path(__file__).parent)
    
    # Determine architecture
    arch = platform.machine().lower()
    if arch in ['amd64', 'x86_64']:
        lib_dir = "X64"
    else:
        lib_dir = "Win32"
    
    lib_path = str(Path(__file__).parent / "lib" / lib_dir)
    
    pythonpath = os.environ.get('PYTHONPATH', '')
    # Split PYTHONPATH by separator and normalize paths for comparison
    pythonpath_list = [os.path.normpath(p.strip()).lower() for p in pythonpath.split(os.pathsep) if p.strip()]
    mcp_root_norm = os.path.normpath(mcp_root).lower()
    lib_path_norm = os.path.normpath(lib_path).lower()
    
    mcp_in_path = mcp_root_norm in pythonpath_list
    lib_in_path = lib_path_norm in pythonpath_list
    
    if mcp_in_path:
        print("  ✓ MCP root in PYTHONPATH")
    else:
        print("  ✗ MCP root not in PYTHONPATH")
        print(f"    Should include: {mcp_root}")
    
    if lib_in_path:
        print(f"  ✓ MCP lib/{lib_dir} in PYTHONPATH")
    else:
        print(f"  ✗ MCP lib/{lib_dir} not in PYTHONPATH")
        print(f"    Should include: {lib_path}")
    
    print(f"    Current PYTHONPATH: {pythonpath}")
    
    return mcp_in_path and lib_in_path

def test_pyxll_module():
    """Test PyXLL module availability"""
    print("\nTesting PyXLL module...")
    
    # Add MCP root to sys.path if needed
    mcp_root = str(Path(__file__).parent)
    if mcp_root not in sys.path:
        sys.path.insert(0, mcp_root)
    
    try:
        import pyxll
        print("  ✓ PyXLL module imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ PyXLL module import failed: {e}")
        print(f"    Make sure MCP root is in PYTHONPATH")
        return False

def test_mcp_import():
    """Test MCP library import"""
    print("\nTesting MCP library import...")
    
    # Add MCP paths to sys.path
    mcp_root = Path(__file__).parent
    
    # Determine architecture
    arch = platform.machine().lower()
    if arch in ['amd64', 'x86_64']:
        lib_dir = "X64"
    else:
        lib_dir = "Win32"
    
    mcp_paths = [
        str(mcp_root),
        str(mcp_root / "lib" / lib_dir)
    ]
    
    for path in mcp_paths:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    try:
        import mcp
        print("  ✓ MCP library imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ MCP library import failed: {e}")
        return False

def main():
    """Main test function"""
    print("MCP Installation Test")
    print("=" * 50)
    
    tests = [
        ("Python Version", test_python_version),
        ("System Architecture", lambda: test_system_architecture()),
        ("MCP Files", test_mcp_files),
        ("Library Directories", test_lib_directories),
        ("PYTHONPATH", test_pythonpath),
        ("PyXLL Module", test_pyxll_module),
        ("MCP Import", test_mcp_import)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ✗ {test_name} test failed with error: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! MCP is ready to use.")
    else:
        print("✗ Some tests failed. Please check the installation.")
        print("\nTo fix issues, run: quick_install.bat")

if __name__ == "__main__":
    main()
