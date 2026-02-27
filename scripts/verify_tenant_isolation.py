#!/usr/bin/env python3
"""
Tenant Isolation Security Scanner
Automatically scans all router files for potential tenant data leaks
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Any

class TenantIsolationScanner:
    """Scans for tenant data leak vulnerabilities in FastAPI routers"""
    
    def __init__(self, base_path: str = "backend/app/routers"):
        self.base_path = Path(base_path)
        self.vulnerabilities = []
        self.patterns = {
            # Dangerous patterns that might leak tenant data
            'select_without_tenant': r'select\([^)]+\)\.where\([^)]*shipment_id[^)]*\)',
            'where_without_tenant': r'\.where\([^)]*shipment_id[^)]*\)(?!.*tenant_id)',
            'get_by_id_no_tenant': r'get.*\{id\}.*current_user.*User.*Depends.*get_current_user',
            'join_without_tenant': r'\.join\([^)]+\)\.where\([^)]*\)(?!.*tenant_id)',
        }
        
    def scan_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan a single file for tenant isolation vulnerabilities"""
        vulnerabilities = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            for i, line in enumerate(lines, 1):
                # Check for dangerous patterns
                for pattern_name, pattern in self.patterns.items():
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        # Check if tenant_id is present in the same line or nearby
                        has_tenant_filter = 'tenant_id' in line
                        
                        # Also check a few lines above and below for tenant_id
                        context_lines = 5
                        start_line = max(0, i - context_lines)
                        end_line = min(len(lines), i + context_lines)
                        context = '\n'.join(lines[start_line:end_line])
                        
                        if not has_tenant_filter:
                            has_tenant_filter = 'tenant_id' in context
                        
                        if not has_tenant_filter:
                            vulnerabilities.append({
                                'file': str(file_path),
                                'line': i,
                                'pattern': pattern_name,
                                'code': line.strip(),
                                'severity': 'HIGH',
                                'description': f"Potential tenant data leak: {pattern_name}"
                            })
                        
                # Special check for router endpoints that get by ID
                if re.search(r'@router\.(get|patch|delete)\(".*\{.*id.*\}"', line):
                    # Check if this endpoint uses tenant context
                    func_start = i
                    
                    # Find the function body (look for def after the decorator)
                    func_def_line = None
                    for j in range(i, min(len(lines), i + 10)):
                        if 'def ' in lines[j]:
                            func_def_line = j
                            break
                    
                    if func_def_line:
                        # Get function content until next decorator or end
                        func_content = []
                        for j in range(func_def_line, min(len(lines), func_def_line + 50)):
                            func_line = lines[j]
                            func_content.append(func_line)
                            
                            # Stop at next decorator or class/function definition
                            if j > func_def_line and (re.match(r'@|def |class ', func_line.strip())):
                                break
                        
                        func_text = '\n'.join(func_content)
                        
                        # Check for tenant filtering patterns (more comprehensive)
                        tenant_patterns = [
                            r'tenant_id',
                            r'TenantContext',
                            r'_assert_owned',
                            r'current_tenant_id',
                            r'get_tenant_context',
                            r'WHERE.*tenant_id',  # SQL patterns
                            r'\.tenant_id'
                        ]
                        
                        has_tenant_filter = any(re.search(pattern, func_text, re.IGNORECASE) for pattern in tenant_patterns)
                        
                        # Also check if it's a system/admin endpoint (may not need tenant filtering)
                        is_system_endpoint = any(keyword in func_text.lower() for keyword in ['sys', 'admin', 'super'])
                        
                        if not has_tenant_filter and not is_system_endpoint:
                            vulnerabilities.append({
                                'file': str(file_path),
                                'line': i,
                                'pattern': 'endpoint_without_tenant_filter',
                                'code': line.strip(),
                                'severity': 'HIGH',  # Reduced from CRITICAL
                                'description': "Endpoint may access resource without tenant filtering"
                            })
                
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")
            
        return vulnerabilities
    
    def scan_all_files(self) -> List[Dict[str, Any]]:
        """Scan all router files for vulnerabilities"""
        all_vulnerabilities = []
        
        if not self.base_path.exists():
            print(f"Path {self.base_path} does not exist")
            return all_vulnerabilities
        
        for file_path in self.base_path.rglob("*.py"):
            if file_path.is_file():
                vulnerabilities = self.scan_file(file_path)
                all_vulnerabilities.extend(vulnerabilities)
        
        return all_vulnerabilities
    
    def generate_report(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        """Generate a security report"""
        report = []
        report.append("# 🔒 Tenant Isolation Security Report")
        report.append(f"Generated: {__import__('datetime').datetime.now()}")
        report.append("")
        
        if not vulnerabilities:
            report.append("✅ No tenant isolation vulnerabilities found!")
            return '\n'.join(report)
        
        # Group by severity
        critical = [v for v in vulnerabilities if v['severity'] == 'CRITICAL']
        high = [v for v in vulnerabilities if v['severity'] == 'HIGH']
        
        if critical:
            report.append("## 🚨 CRITICAL Vulnerabilities")
            report.append("")
            for vuln in critical:
                report.append(f"### {vuln['file']}:{vuln['line']}")
                report.append(f"**Pattern**: {vuln['pattern']}")
                report.append(f"**Code**: `{vuln['code']}`")
                report.append(f"**Description**: {vuln['description']}")
                report.append("")
        
        if high:
            report.append("## ⚠️ HIGH Severity Vulnerabilities")
            report.append("")
            for vuln in high:
                report.append(f"### {vuln['file']}:{vuln['line']}")
                report.append(f"**Pattern**: {vuln['pattern']}")
                report.append(f"**Code**: `{vuln['code']}`")
                report.append(f"**Description**: {vuln['description']}")
                report.append("")
        
        # Summary
        report.append("## 📊 Summary")
        report.append(f"- Critical: {len(critical)}")
        report.append(f"- High: {len(high)}")
        report.append(f"- Total: {len(vulnerabilities)}")
        report.append("")
        
        # Recommendations
        report.append("## 🛠️ Recommendations")
        report.append("1. Add `tenant_id` filter to all database queries")
        report.append("2. Use `TenantContext` dependency instead of `get_current_user`")
        report.append("3. Implement Row Level Security (RLS) at database level")
        report.append("4. Add automated security scanning to CI/CD pipeline")
        report.append("")
        
        return '\n'.join(report)

def main():
    """Run the tenant isolation scanner"""
    scanner = TenantIsolationScanner()
    vulnerabilities = scanner.scan_all_files()
    
    if vulnerabilities:
        print("🚨 TENANT ISOLATION VULNERABILITIES FOUND!")
        print(f"Found {len(vulnerabilities)} potential issues")
        print("\n" + "="*50)
        
        for vuln in vulnerabilities:
            print(f"\n📁 {vuln['file']}:{vuln['line']}")
            print(f"🔍 {vuln['pattern']} ({vuln['severity']})")
            print(f"💻 {vuln['code']}")
            print(f"📝 {vuln['description']}")
        
        # Generate detailed report
        report = scanner.generate_report(vulnerabilities)
        with open('tenant_isolation_report.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📄 Detailed report saved to: tenant_isolation_report.md")
        return 1
    else:
        print("✅ No tenant isolation vulnerabilities found!")
        return 0

if __name__ == "__main__":
    exit(main())
