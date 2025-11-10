param(
    [string]$Entry="src\\workproof\\main.py",
    [string]$GuiEntry="src\\workproof\\app_ui.py"
)

python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller
pyinstaller `
    --noconfirm `
    --onefile `
    --name workproof `
    --icon assets\\icon.png `
    --add-data "assets\\templates;assets\\templates" `
    $Entry

Write-Host "Build complete. See dist\\workproof.exe"

pyinstaller `
    --noconfirm `
    --onefile `
    --windowed `
    --name workproof_gui `
    --icon assets\\icon.png `
    --add-data "assets\\templates;assets\\templates" `
    $GuiEntry

Write-Host "GUI build complete. See dist\\workproof_gui.exe"



