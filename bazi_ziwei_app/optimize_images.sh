#!/bin/bash
# 图片优化脚本 - P0性能优化

echo "🖼️  开始优化图片..."

# 检查是否安装了优化工具
if ! command -v convert &> /dev/null; then
    echo "❌ ImageMagick未安装"
    echo "📦 macOS安装方法: brew install imagemagick"
    echo ""
fi

if ! command -v pngquant &> /dev/null; then
    echo "❌ pngquant未安装" 
    echo "📦 macOS安装方法: brew install pngquant"
    echo ""
fi

# 优化PNG图片
echo "📊 当前图片大小："
du -h assets/*.png 2>/dev/null

if command -v pngquant &> /dev/null; then
    echo ""
    echo "🔧 压缩PNG图片..."
    for file in assets/*.png; do
        if [ -f "$file" ]; then
            echo "  处理: $file"
            # 备份原文件
            cp "$file" "${file}.bak"
            # 压缩（保持70-85%质量）
            pngquant --quality=70-85 --force --ext .png "$file" 2>/dev/null || echo "  ⚠️  跳过: $file"
        fi
    done
    echo "✅ PNG压缩完成"
else
    echo "⚠️  跳过PNG压缩（pngquant未安装）"
fi

# 转换为WebP格式（可选）
if command -v cwebp &> /dev/null; then
    echo ""
    echo "🔧 转换为WebP格式..."
    for file in assets/*.png; do
        if [ -f "$file" ]; then
            output="${file%.png}.webp"
            echo "  转换: $file -> $output"
            cwebp -q 80 "$file" -o "$output" 2>/dev/null
        fi
    done
    echo "✅ WebP转换完成"
else
    echo "ℹ️  跳过WebP转换（cwebp未安装）"
    echo "📦 macOS安装方法: brew install webp"
fi

echo ""
echo "📊 优化后图片大小："
du -h assets/*.png assets/*.webp 2>/dev/null

echo ""
echo "✅ 图片优化完成！"
echo ""
echo "💡 提示："
echo "  - 原始文件已备份为 .bak"
echo "  - 如果图片出现问题，可以恢复备份"
echo "  - WebP格式体积更小，建议在代码中优先使用"
