@echo off
echo instalando
pip install pygame pyinstaller

echo compilando
pyinstaller --onedir --windowed --name "Dead Zone" --add-data "assets;assets" main.py

echo Pronto! Pasta "dist/Dead Zone" contem o executavel.
pause
