@echo off
setlocal enabledelayedexpansion

:: Set console code page to UTF-8
chcp 65001 > nul

echo =======================================================
echo        Python 3.9 手动安装指南
echo =======================================================
echo.
echo 如果自动安装失败，请按照以下步骤手动安装Python 3.9：
echo.

echo [步骤 1] 下载Python 3.9.13
echo ----------------------------------------
echo 1. 访问官方下载页面：
echo    https://www.python.org/downloads/release/python-3913/
echo.
echo 2. 选择适合的安装包：
echo    - Windows x86-64 executable installer (推荐，适用于64位系统)
echo    - Windows x86 executable installer (适用于32位系统)
echo.

echo [步骤 2] 安装Python 3.9.13
echo ----------------------------------------
echo 1. 双击下载的安装文件
echo 2. ✅ 重要：勾选 "Add Python 3.9 to PATH"
echo 3. 选择 "Install Now" 或 "Customize installation"
echo 4. 如果选择自定义安装：
echo    - 确保勾选 "pip"
echo    - 安装路径可以使用默认值
echo 5. 等待安装完成
echo.

echo [步骤 3] 验证安装
echo ----------------------------------------
echo 1. 打开新的命令提示符窗口
echo 2. 输入：python --version
echo 3. 应该显示：Python 3.9.13
echo.

echo [步骤 4] 继续部署
echo ----------------------------------------
echo 安装完成后，重新运行 deploy.bat 脚本
echo.

echo =======================================================
echo 常见问题解决
echo =======================================================
echo.
echo 问题1：安装时提示权限不足
echo 解决：右键点击安装文件，选择"以管理员身份运行"
echo.
echo 问题2：安装后命令行找不到python
echo 解决：重新安装时确保勾选"Add Python to PATH"
echo.
echo 问题3：系统已有其他Python版本
echo 解决：Python 3.9可以与其他版本共存，安装时选择不同的目录
echo.
echo 问题4：杀毒软件阻止安装
echo 解决：临时关闭杀毒软件，或将Python安装文件添加到白名单
echo.

echo =======================================================
echo 需要帮助？
echo =======================================================
echo.
echo 如果遇到其他问题，可以：
echo 1. 查看Python官方文档：https://docs.python.org/3.9/
echo 2. 重新下载安装文件，确保文件完整
echo 3. 尝试使用Microsoft Store版本的Python
echo.

pause 