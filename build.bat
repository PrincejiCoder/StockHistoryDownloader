@echo off
echo Building StockHistoryDownloader...

pyinstaller ^
--onefile ^
--windowed ^
--clean ^
--name StockHistoryDownloader ^
main.py

echo Build complete.
pause
