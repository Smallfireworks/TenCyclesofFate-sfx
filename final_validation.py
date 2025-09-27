#!/usr/bin/env python3
"""
Final validation script to check project consistency and identify any remaining bugs.
This script performs comprehensive checks on the entire project.
"""

import os
import sys
import ast
import re
from pathlib import Path

def check_file_exists(file_path, description=""):
    """Check if a file exists."""
    if Path(file_path).exists():
        print(f"✅ {description or file_path} exists")
        return True
    else:
        print(f"❌ {description or file_path} is missing")
        return False

def check_imports_in_file(file_path, expected_imports=None, forbidden_imports=None):
    """Check imports in a Python file."""
    if not Path(file_path).exists():
        print(f"⚠️  File {file_path} not found, skipping import check")
        return True
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        
        # Check forbidden imports
        if forbidden_imports:
            for forbidden in forbidden_imports:
                for imp in imports:
                    if forbidden in imp:
                        print(f"❌ {file_path} contains forbidden import: {imp}")
                        return False
        
        # Check expected imports
        if expected_imports:
            for expected in expected_imports:
                found = any(expected in imp for imp in imports)
                if not found:
                    print(f"⚠️  {file_path} missing expected import: {expected}")
        
        print(f"✅ {file_path} imports are valid")
        return True
        
    except Exception as e:
        print(f"❌ Error checking imports in {file_path}: {e}")
        return False

def check_html_elements():
    """Check that HTML elements match JavaScript references."""
    html_file = "frontend/index.html"
    js_file = "frontend/index.js"
    
    if not (Path(html_file).exists() and Path(js_file).exists()):
        print("⚠️  HTML or JS files not found, skipping element check")
        return True
    
    try:
        # Read HTML file
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Read JS file
        with open(js_file, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # Find getElementById calls in JS
        id_pattern = r'getElementById\(["\']([^"\']+)["\']\)'
        js_ids = set(re.findall(id_pattern, js_content))
        
        # Find id attributes in HTML
        html_id_pattern = r'id=["\']([^"\']+)["\']'
        html_ids = set(re.findall(html_id_pattern, html_content))
        
        # Check if all JS IDs exist in HTML
        missing_ids = js_ids - html_ids
        if missing_ids:
            print(f"❌ Missing HTML elements for JS IDs: {missing_ids}")
            return False
        
        print("✅ All JavaScript element references have corresponding HTML elements")
        return True
        
    except Exception as e:
        print(f"❌ Error checking HTML/JS elements: {e}")
        return False

def check_docker_config():
    """Check Docker configuration consistency."""
    docker_compose = "docker-compose.yml"
    dockerfile = "Dockerfile"
    env_example = ".env.docker.example"
    
    all_exist = all([
        check_file_exists(docker_compose, "Docker Compose file"),
        check_file_exists(dockerfile, "Dockerfile"),
        check_file_exists(env_example, "Docker environment example")
    ])
    
    if not all_exist:
        return False
    
    try:
        # Check docker-compose.yml for obsolete version
        with open(docker_compose, 'r', encoding='utf-8') as f:
            compose_content = f.read()
        
        if 'version:' in compose_content:
            print("⚠️  docker-compose.yml still contains obsolete 'version' attribute")
            return False
        
        if 'name:' not in compose_content:
            print("❌ docker-compose.yml missing project name")
            return False
        
        print("✅ Docker configuration is valid")
        return True
        
    except Exception as e:
        print(f"❌ Error checking Docker config: {e}")
        return False

def check_auth_consistency():
    """Check authentication system consistency."""
    auth_file = "backend/app/auth_simple.py"
    config_file = "backend/app/config.py"
    main_file = "backend/app/main.py"
    
    # Check that old auth.py is removed
    old_auth = "backend/app/auth.py"
    if Path(old_auth).exists():
        print(f"❌ Old auth file still exists: {old_auth}")
        return False
    
    # Check imports
    checks = [
        check_imports_in_file(main_file, 
                            expected_imports=["auth_simple"], 
                            forbidden_imports=["app.auth", "backend.app.auth"]),
        check_imports_in_file(auth_file, 
                            forbidden_imports=["authlib", "LINUXDO"]),
        check_imports_in_file(config_file, 
                            forbidden_imports=["LINUXDO"])
    ]
    
    return all(checks)

def main():
    """Main validation function."""
    print("🔍 Final Project Validation")
    print("=" * 50)
    
    # Change to project directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    checks = []
    
    print("\n📁 File Existence Checks")
    print("-" * 30)
    file_checks = [
        check_file_exists("README.md", "README file"),
        check_file_exists("docker-compose.yml", "Docker Compose file"),
        check_file_exists("Dockerfile", "Dockerfile"),
        check_file_exists("deploy.sh", "Linux deployment script"),
        check_file_exists("deploy.bat", "Windows deployment script"),
        check_file_exists("backend/app/auth_simple.py", "New auth system"),
        check_file_exists("frontend/index.html", "Frontend HTML"),
        check_file_exists("frontend/index.js", "Frontend JavaScript"),
        check_file_exists("frontend/index.css", "Frontend CSS"),
    ]
    checks.extend(file_checks)
    
    print("\n🔗 Import and Reference Checks")
    print("-" * 30)
    import_checks = [
        check_auth_consistency(),
        check_html_elements(),
    ]
    checks.extend(import_checks)
    
    print("\n🐳 Docker Configuration Checks")
    print("-" * 30)
    docker_checks = [
        check_docker_config(),
    ]
    checks.extend(docker_checks)
    
    print("\n📊 Validation Summary")
    print("=" * 30)
    passed = sum(checks)
    total = len(checks)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All validation checks passed!")
        print("✅ Project is consistent and ready for deployment")
        return 0
    else:
        print("⚠️  Some validation checks failed")
        print("❗ Please review and fix the issues above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
