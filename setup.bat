@echo off
title Travellers Rest Planner - Full Setup
color 0A
echo.
echo   ==========================================
echo     Travellers Rest Planner - Full Setup
echo   ==========================================
echo.
echo   This will install everything you need.
echo.
pause

:: Check admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo   Need admin rights. Right-click and Run as administrator.
    echo.
    pause
    exit /b 1
)

:: ---- PYTHON ----
echo.
echo   [1/5] Checking Python...
python --version >nul 2>&1
if %errorLevel% equ 0 goto python_ok

echo   Python not found. Downloading...
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"

if not exist "%TEMP%\python_installer.exe" goto python_fail

echo   Installing Python (takes a minute)...
"%TEMP%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1

:: Refresh PATH so we can find python
set "PATH=C:\Program Files\Python312;C:\Program Files\Python312\Scripts;%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"

python --version >nul 2>&1
if %errorLevel% neq 0 goto python_restart
goto python_ok

:python_fail
echo   Download failed. Install Python manually from python.org
pause
exit /b 1

:python_restart
echo.
echo   Python installed but PATH needs to refresh.
echo   Close this window, reopen, and run setup.bat again.
pause
exit /b 1

:python_ok
python --version
echo   Python is ready.

:: ---- GIT ----
echo.
echo   [2/5] Checking Git...
git --version >nul 2>&1
if %errorLevel% equ 0 goto git_ok

echo   Git not found. Installing...
winget --version >nul 2>&1
if %errorLevel% equ 0 goto git_winget

echo   Downloading Git...
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.2/Git-2.47.1.2-64-bit.exe' -OutFile '%TEMP%\git_installer.exe'"
if not exist "%TEMP%\git_installer.exe" goto git_fail
"%TEMP%\git_installer.exe" /VERYSILENT /NORESTART
goto git_check

:git_winget
winget install --id Git.Git -e --silent --accept-package-agreements --accept-source-agreements

:git_check
set "PATH=C:\Program Files\Git\cmd;%PATH%"
git --version >nul 2>&1
if %errorLevel% neq 0 goto git_restart
goto git_ok

:git_fail
echo   Download failed. Install Git from git-scm.com
pause
exit /b 1

:git_restart
echo.
echo   Git installed but PATH needs to refresh.
echo   Close this window, reopen, and run setup.bat again.
pause
exit /b 1

:git_ok
git --version
echo   Git is ready.

:: ---- CLONE ----
echo.
echo   [3/5] Setting up project...
if exist "planner\__main__.py" goto clone_ok

if exist "travellers-rest-planner\planner\__main__.py" (
    cd travellers-rest-planner
    goto clone_ok
)

echo   Cloning repository...
git clone https://github.com/truix/travellers-rest-planner.git
cd travellers-rest-planner

:clone_ok
echo   Project: %CD%

:: ---- INSTALL + EXTRACT ----
echo.
echo   [4/5] Installing dependencies and extracting game data...
python install.py

:: ---- SHORTCUT ----
echo.
echo   [5/5] Creating desktop shortcut...
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Travellers Rest Planner.lnk')); $sc.TargetPath = (Join-Path '%CD%' 'run.bat'); $sc.WorkingDirectory = '%CD%'; $sc.Description = 'Launch Travellers Rest Planner'; $sc.Save()"

echo.
echo   ==========================================
echo     Setup complete!
echo   ==========================================
echo.
echo   Double-click "Travellers Rest Planner" on your desktop to run.
echo   Or double-click run.bat in this folder.
echo.
pause
