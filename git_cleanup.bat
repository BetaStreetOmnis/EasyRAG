@echo off
echo ==========================================
echo Git 缓存清理脚本
echo ==========================================

echo.
echo 1. 检查Git状态...
git status

echo.
echo 2. 预览将要清理的文件...
git clean -n

echo.
echo 3. 清理未跟踪的文件和目录...
git clean -fd

echo.
echo 4. 清理Git对象缓存...
git gc --aggressive --prune=now

echo.
echo 5. 清理远程跟踪分支...
git remote prune origin

echo.
echo 6. 显示仓库大小...
du -sh .git 2>nul || echo "无法显示仓库大小"

echo.
echo 7. 清理Python缓存...
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "core\__pycache__" rmdir /s /q "core\__pycache__"
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q "*.pyc" 2>nul

echo.
echo 8. 清理临时文件...
if exist "*.tmp" del /q "*.tmp"
if exist "*.log" del /q "*.log"
if exist ".DS_Store" del /q ".DS_Store"

echo.
echo ==========================================
echo Git 缓存清理完成！
echo ==========================================
pause 