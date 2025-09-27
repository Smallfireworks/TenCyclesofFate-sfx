#!/usr/bin/env python3
"""
Simple syntax test to verify the function ordering fix.
This checks that get_password_hash is defined before it's used.
"""

import ast
import sys
from pathlib import Path

def test_function_ordering():
    """Test that get_password_hash is defined before it's used."""
    auth_file = Path(__file__).parent / "backend" / "app" / "auth_simple.py"
    
    if not auth_file.exists():
        print(f"❌ File not found: {auth_file}")
        return False
    
    print(f"📁 Analyzing file: {auth_file}")
    
    try:
        with open(auth_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content)
        
        # Track function definitions and calls
        function_defs = {}
        function_calls = []
        
        class FunctionAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.current_line = 0
            
            def visit_FunctionDef(self, node):
                function_defs[node.name] = node.lineno
                print(f"📍 Function '{node.name}' defined at line {node.lineno}")
                self.generic_visit(node)
            
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name):
                    function_calls.append((node.func.id, node.lineno))
                self.generic_visit(node)
        
        analyzer = FunctionAnalyzer()
        analyzer.visit(tree)
        
        # Check if get_password_hash is defined before it's used
        get_password_hash_def_line = function_defs.get('get_password_hash')
        if not get_password_hash_def_line:
            print("❌ get_password_hash function not found")
            return False
        
        print(f"✅ get_password_hash defined at line {get_password_hash_def_line}")
        
        # Check all calls to get_password_hash
        get_password_hash_calls = [
            (func_name, line) for func_name, line in function_calls 
            if func_name == 'get_password_hash'
        ]
        
        print(f"📞 Found {len(get_password_hash_calls)} calls to get_password_hash:")
        
        all_calls_valid = True
        for func_name, call_line in get_password_hash_calls:
            print(f"   - Called at line {call_line}")
            if call_line < get_password_hash_def_line:
                print(f"   ❌ Call at line {call_line} is BEFORE definition at line {get_password_hash_def_line}")
                all_calls_valid = False
            else:
                print(f"   ✅ Call at line {call_line} is AFTER definition at line {get_password_hash_def_line}")
        
        return all_calls_valid
        
    except Exception as e:
        print(f"❌ Error analyzing file: {e}")
        return False

def test_syntax():
    """Test that the file has valid Python syntax."""
    auth_file = Path(__file__).parent / "backend" / "app" / "auth_simple.py"
    
    try:
        with open(auth_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to compile the code
        compile(content, str(auth_file), 'exec')
        print("✅ File has valid Python syntax")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking syntax: {e}")
        return False

def main():
    """Main test function."""
    print("🔧 Testing Authentication System Function Ordering Fix")
    print("=" * 60)
    
    syntax_ok = test_syntax()
    ordering_ok = test_function_ordering()
    
    print("\n📊 Test Results")
    print("=" * 30)
    print(f"Syntax: {'✅ PASS' if syntax_ok else '❌ FAIL'}")
    print(f"Function Ordering: {'✅ PASS' if ordering_ok else '❌ FAIL'}")
    
    if syntax_ok and ordering_ok:
        print("\n🎉 All tests passed!")
        print("💡 The 'NameError: name get_password_hash is not defined' should be fixed.")
        print("🚀 The Docker container should now start successfully.")
        return 0
    else:
        print("\n⚠️  Some tests failed. The function ordering issue may still exist.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
