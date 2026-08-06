#!/usr/bin/env python3
"""部署前安全检查脚本"""

import os
import sys
from pathlib import Path


def check_sensitive_files():
    """检查是否有敏感文件"""
    print("🔍 检查敏感文件...")
    
    try:
        from utils.release_privacy import find_private_release_artifacts
        
        root = Path.cwd()
        artifacts = find_private_release_artifacts(root)
        
        if artifacts:
            print("❌ 发现以下敏感文件，不能部署到公网：")
            for path in artifacts:
                print(f"   - {path.relative_to(root)}")
            return False
        else:
            print("✅ 未发现敏感文件")
            return True
    except Exception as e:
        print(f"⚠️  检查失败: {e}")
        return False


def check_environment():
    """检查环境配置"""
    print("\n🔍 检查环境配置...")
    
    runtime_mode = os.getenv("MINGSHU_RUNTIME_MODE", "public")
    api_key = os.getenv("MOONSHOT_API_KEY", "")
    
    print(f"   运行模式: {runtime_mode}")
    print(f"   AI 密钥: {'已配置' if api_key else '未配置（将使用本地规则）'}")
    
    if runtime_mode not in ["public", "local"]:
        print(f"⚠️  无效的运行模式: {runtime_mode}")
        return False
    
    print("✅ 环境配置正常")
    return True


def check_dependencies():
    """检查依赖库"""
    print("\n🔍 检查依赖库...")
    
    required_modules = [
        ("streamlit", "1.35.0"),
        ("pandas", "2.0.0"),
        ("lunar_python", "1.4.8"),
        ("reportlab", "4.0.0"),
        ("openai", "2.0.0"),
        ("pydantic", "2.0.0"),
    ]
    
    missing = []
    for module_name, min_version in required_modules:
        try:
            module = __import__(module_name)
            version = getattr(module, "__version__", "unknown")
            print(f"   ✓ {module_name}: {version}")
        except ImportError:
            missing.append(module_name)
            print(f"   ✗ {module_name}: 未安装")
    
    if missing:
        print(f"\n❌ 缺少依赖: {', '.join(missing)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 所有依赖已安装")
    return True


def check_rules_integrity():
    """检查规则库完整性"""
    print("\n🔍 检查规则库...")
    
    try:
        from core.bazi_rulebook import load_rulebook
        
        rulebook = load_rulebook()
        print(f"   规则版本: {rulebook.version}")
        print(f"   规则总数: {len(rulebook.rules)}")
        print(f"   章节数量: {len(rulebook.sections)}")
        print("✅ 规则库完整")
        return True
    except Exception as e:
        print(f"❌ 规则库检查失败: {e}")
        return False


def check_gitignore():
    """检查 .gitignore 配置"""
    print("\n🔍 检查 .gitignore...")
    
    gitignore_path = Path.cwd() / ".gitignore"
    
    required_patterns = [
        "data/*.db",
        "logs/",
        ".streamlit/secrets.toml",
        ".env",
        "__pycache__/",
    ]
    
    if not gitignore_path.exists():
        print("⚠️  .gitignore 文件不存在")
        return False
    
    content = gitignore_path.read_text()
    missing = [p for p in required_patterns if p not in content]
    
    if missing:
        print("⚠️  .gitignore 缺少以下配置:")
        for pattern in missing:
            print(f"   - {pattern}")
        return False
    
    print("✅ .gitignore 配置完整")
    return True


def check_docker_files():
    """检查 Docker 配置文件"""
    print("\n🔍 检查 Docker 配置...")
    
    docker_files = ["Dockerfile", "docker-compose.yml", ".dockerignore"]
    all_exist = True
    
    for filename in docker_files:
        path = Path.cwd() / filename
        if path.exists():
            print(f"   ✓ {filename}")
        else:
            print(f"   ✗ {filename} (可选)")
            all_exist = False
    
    if all_exist:
        print("✅ Docker 配置完整")
    else:
        print("⚠️  部分 Docker 文件缺失（如不使用 Docker 可忽略）")
    
    return True


def check_port_availability():
    """检查端口可用性"""
    print("\n🔍 检查端口 8501...")
    
    import socket
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 8501))
    sock.close()
    
    if result == 0:
        print("⚠️  端口 8501 已被占用")
        print("   可运行: lsof -i :8501 查看占用进程")
        return False
    else:
        print("✅ 端口 8501 可用")
        return True


def main():
    """主函数"""
    print("=" * 50)
    print("  命数研究室 - 部署检查")
    print("=" * 50)
    
    checks = [
        ("敏感文件", check_sensitive_files),
        ("环境配置", check_environment),
        ("依赖库", check_dependencies),
        ("规则库", check_rules_integrity),
        ("Git配置", check_gitignore),
        ("Docker配置", check_docker_files),
        ("端口可用性", check_port_availability),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name}检查异常: {e}")
            results.append((name, False))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("  检查结果汇总")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:12} {status}")
    
    print("=" * 50)
    print(f"总计: {passed}/{total} 项检查通过")
    
    if passed == total:
        print("\n🎉 所有检查通过，可以开始部署！")
        print("\n推荐部署方式：")
        print("  1. Docker:     docker-compose up -d")
        print("  2. VPS:        bash deploy.sh")
        print("  3. Cloud:      访问 https://share.streamlit.io")
        return 0
    else:
        print("\n⚠️  部分检查未通过，请修复后再部署")
        return 1


if __name__ == "__main__":
    sys.exit(main())
