#!/bin/bash
# EasyRAG 代码验证脚本
# 用法: ./validate.sh [python|frontend|all]

set -e

echo "🔍 EasyRAG 代码验证"
echo "===================="
echo ""

validate_python() {
    echo "📦 验证Python代码..."
    
    # 检查flake8
    if command -v flake8 &> /dev/null; then
        echo "  ✓ 运行 flake8..."
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
        echo "  ✅ flake8 检查完成"
    else
        echo "  ⚠️  flake8 未安装，跳过Python代码检查"
        echo "  💡 运行: pip install -r requirements-dev.txt"
    fi
    echo ""
}

validate_frontend() {
    echo "🎨 验证前端代码..."
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        echo "  ⚠️  Node.js 未安装，跳过前端代码检查"
        return
    fi
    
    # 检查node_modules
    if [ ! -d "node_modules" ]; then
        echo "  📥 安装前端依赖..."
        npm install --quiet
    fi
    
    # 运行ESLint
    echo "  ✓ 运行 ESLint..."
    npx eslint@8.57.0 static/**/*.js || {
        echo "  ⚠️  ESLint 发现问题，运行 'npx eslint@8.57.0 static/**/*.js --fix' 自动修复"
    }
    echo "  ✅ 前端代码检查完成"
    echo ""
}

validate_all() {
    validate_python
    validate_frontend
}

# 主逻辑
case "${1:-all}" in
    python)
        validate_python
        ;;
    frontend)
        validate_frontend
        ;;
    all)
        validate_all
        ;;
    *)
        echo "❌ 未知选项: $1"
        echo "用法: $0 [python|frontend|all]"
        exit 1
        ;;
esac

echo "✅ 验证完成！"
