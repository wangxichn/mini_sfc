#!/bin/bash
set -e

# 1. 权限检查
if [ ! -w .git/objects ]; then
  sudo chown -R $USER:$USER .git || {
    echo "无法修复.git权限，请手动执行: sudo chown -R $USER:$USER .git"
    exit 1
  }
fi

# 2. 获取当前分支
CURRENT_BRANCH=$(git symbolic-ref --short HEAD)

# 3. 使用更安全的临时目录操作
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT  # 确保退出时清理

# 4. 复制文件（保留权限）
rsync -a docs/build/html/ "$TEMP_DIR/"

# 5. 切换到gh-pages分支
git checkout gh-pages

# 6. 清空分支（使用git rm更安全）
git ls-files -z | xargs -0 git rm -f --

# 7. 复制文件回来（保留隐藏文件）
rsync -a "$TEMP_DIR/" ./

# 8. 确保.nojekyll存在
touch .nojekyll

# 9. 提交和推送
git add .
git commit -m "Update documentation $(date +%Y-%m-%d)"
git push origin gh-pages

# 10. 切回原分支
git checkout "$CURRENT_BRANCH"

echo "成功更新文档到gh-pages分支"