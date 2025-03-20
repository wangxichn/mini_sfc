#!/bin/bash
set -e  # 脚本遇到错误时立即退出

# 项目根目录
PROJECT_ROOT=$(pwd)

# 构建Sphinx文档
cd docs
make clean 
make html
cd ..

# 获取当前分支名称
CURRENT_BRANCH=$(git symbolic-ref --short HEAD)

# 定义一个临时目录来保存生成的HTML文件
TEMP_DIR=$(mktemp -d)

# 复制构建好的HTML文件到临时目录
cp -r docs/build/html/. $TEMP_DIR

# 切换到gh-pages分支并清空该分支下的所有文件
git checkout gh-pages && git rm -rf .

# 从临时目录复制HTML文件回来
cp -r $TEMP_DIR/. .

touch .nojekyll

# 添加所有文件到暂存区
git add .

# 提交更改
git commit -m "Update documentation"

# 推送更改到远程仓库
git push origin gh-pages

# 清理临时目录
rm -rf "$TEMP_DIR"

# 切回原来的分支
git checkout "$CURRENT_BRANCH"

echo "Documentation update and deploy to gh-pages completed."