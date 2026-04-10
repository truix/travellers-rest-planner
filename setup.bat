@echo off
title Travellers Rest Planner — Full Setup
color 0A
echo.
echo   ==========================================
echo     Travellers Rest Planner — Full Setup
echo   ==========================================
echo.
echo   This will install everything you need:
echo     - Python (if not installed)
echo     - Git (if not installed)
echo     - All dependencies
echo     - Extract game data
echo     - Launch the planner
echo.
pause

:: Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo   [!] Need admin rights to install Python/Git.
    echo       Right-click this file and "Run as administrator"
    echo.
    pause
    exit /b 1
)

:: ============================================================
:: STEP 1: Python
:: ============================================================
echo.
echo   [1/5] Checking Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo   Python not found. Installing...
    echo   Downloading Python installer...

    :: Download Python using PowerShell
    powershell -NoProfile -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe' -OutFile '%TEMP%\python_installer.exe' }"

    if not exist "%TEMP%\python_installer.exe" (
        echo   [!] Download failed. Install Python manually from python.org
        pause
        exit /b 1
    )

    echo   Running Python installer (this takes a minute)...
    "%TEMP%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1

    :: Refresh PATH
    set "PATH=%PATH%;C:\Program Files\Python312;C:\Program Files\Python312\Scripts"
    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts"

    python --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo   [!] Python installed but not in PATH yet.
        echo       Close this window, reopen, and run setup.bat again.
        pause
        exit /b 1
    )
    echo   Python installed!
) else (
    for /f "tokens=*" %%i in ('python --version') do echo   %%i found
)

:: ============================================================
:: STEP 2: Git
:: ============================================================
echo.
echo   [2/5] Checking Git...
git --version >nul 2>&1
if %errorLevel% neq 0 (
    echo   Git not found. Installing...

    :: Check if winget is available (Windows 10 1709+)
    winget --version >nul 2>&1
    if %errorLevel% equ 0 (
        echo   Installing via winget...
        winget install --id Git.Git -e --silent --accept-package-agreements --accept-source-agreements
    ) else (
        echo   Downloading Git installer...
        powershell -NoProfile -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.2/Git-2.47.1.2-64-bit.exe' -OutFile '%TEMP%\git_installer.exe' }"

        if not exist "%TEMP%\git_installer.exe" (
            echo   [!] Download failed. Install Git manually from git-scm.com
            pause
            exit /b 1
        )

        echo   Running Git installer...
        "%TEMP%\git_installer.exe" /VERYSILENT /NORESTART
    )

    :: Refresh PATH
    set "PATH=%PATH%;C:\Program Files\Git\cmd"

    git --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo   [!] Git installed but not in PATH yet.
        echo       Close this window, reopen, and run setup.bat again.
        pause
        exit /b 1
    )
    echo   Git installed!
) else (
    for /f "tokens=*" %%i in ('git --version') do echo   %%i found
)

:: ============================================================
:: STEP 3: Clone repo (if not already in it)
:: ============================================================
echo.
echo   [3/5] Setting up project...
if not exist "planner\__main__.py" (
    :: We're not inside the repo — clone it
    if exist "travellers-rest-planner" (
        cd travellers-rest-planner
    ) else (
        echo   Cloning repository...
        git clone https://github.com/truix/travellers-rest-planner.git
        cd travellers-rest-planner
    )
)
echo   Project directory: %CD%

:: ============================================================
:: STEP 4: Install Python deps + extract game data
:: ============================================================
echo.
echo   [4/5] Installing dependencies and extracting game data...
python install.py

:: ============================================================
:: STEP 5: Create desktop shortcut
:: ============================================================
echo.
echo   [5/5] Creating desktop shortcut...
powershell -NoProfile -Command "& { $ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut([IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'Travellers Rest Planner.lnk')); $sc.TargetPath = '%CD%\run.bat'; $sc.WorkingDirectory = '%CD%'; $sc.IconLocation = 'shell32.dll,21'; $sc.Description = 'Launch Travellers Rest Planner'; $sc.Save() }" 2>nul

if exist "%USERPROFILE%\Desktop\Travellers Rest Planner.lnk" (
    echo   Desktop shortcut created!
) else (
    echo   Couldn't create shortcut, but that's fine.
)

echo.
echo   ==========================================
echo     Setup complete!
echo   ==========================================
echo.
echo   To run the planner:
echo     - Double-click "Travellers Rest Planner" on your desktop
echo     - Or double-click run.bat in this folder
echo     - Or run: python -m planner
echo.
pause
