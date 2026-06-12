@echo off
REM ============================================================
REM  构建脚本：把 credit_agent (React) 的构建产物复制到
REM  my-second-agent (FastAPI 后端) 的 static/ 目录
REM  这样 FastAPI 就能同时 serve API + 前端，实现"一个项目部署"
REM  用法：在 d:\pycharm\python项目\ 目录下执行：build-frontend.bat
REM ============================================================

setlocal
set HERE=%~dp0
set FRONTEND_DIR=%HERE%credit_agent
set BACKEND_DIR=%HERE%my-second-agent
set STATIC_DIR=%BACKEND_DIR%\static

echo [1/3] 正在构建 React 前端 (credit_agent)...
cd /d "%FRONTEND_DIR%"

if not exist node_modules (
    echo   · 检测到 node_modules 不存在，先安装依赖...
    call npm install
    if errorlevel 1 (
        echo   ✗ npm install 失败
        exit /b 1
    )
)

call npm run build
if errorlevel 1 (
    echo   ✗ npm run build 失败
    exit /b 1
)

echo.
echo [2/3] 正在把构建产物复制到后端 static/...
cd /d "%HERE%"

if not exist "%STATIC_DIR%" (
    mkdir "%STATIC_DIR%"
)

REM 清理旧的构建产物（但保留可能存在的其它静态文件）
if exist "%STATIC_DIR%\index.html" (
    del /q "%STATIC_DIR%\index.html"
)
if exist "%STATIC_DIR%\assets" (
    rmdir /s /q "%STATIC_DIR%\assets"
)

REM 复制 React 的 index.html
if exist "%FRONTEND_DIR%\dist\index.html" (
    copy /y "%FRONTEND_DIR%\dist\index.html" "%STATIC_DIR%\index.html" >nul
    echo   · 已复制 dist\index.html 到 my-second-agent\static\
) else (
    echo   ✗ 找不到 dist\index.html — 构建可能失败了
    exit /b 1
)

REM 复制 React 的 assets 目录（JS/CSS/图片）
if exist "%FRONTEND_DIR%\dist\assets" (
    xcopy /e /i /y /q "%FRONTEND_DIR%\dist\assets" "%STATIC_DIR%\assets" >nul
    echo   · 已复制 dist\assets\ 到 my-second-agent\static\assets\
)

REM 复制 dist 根目录下可能存在的其它文件（favicon 等）
for %%f in ("%FRONTEND_DIR%\dist\*.*") do (
    if /i not "%%~nxf"=="index.html" (
        copy /y "%%f" "%STATIC_DIR%\" >nul
    )
)

echo.
echo [3/3] 完成！后端 static/ 目录现在包含前端构建产物。
echo.
echo    下一步：
echo      · 本地测试：在 my-second-agent\ 运行 python -m uvicorn main:app --reload
echo        然后访问 http://localhost:8001/ 查看是否同时看到前端界面
echo.
echo      · 部署到 PythonAnywhere：把整个 my-second-agent/ 上传
echo        （credit_agent/ 是源码，部署不需要）
echo.

endlocal
