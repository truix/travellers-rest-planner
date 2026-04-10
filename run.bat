@echo off
title Travellers Rest Planner
echo.
echo   Starting planner at http://127.0.0.1:8765/
echo   Press Ctrl+C to stop
echo.
start http://127.0.0.1:8765/
python -m planner
pause
