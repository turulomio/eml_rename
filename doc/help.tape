# VHS Tape: Ayuda y versión de eml_rename
# Genera help.gif

Output help.gif

Require echo

Set Shell "bash"
Set FontSize 14
Set Width 1200
Set Height 600
Set WindowBar Colorful
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms
Set PlaybackSpeed 1.0

# Limpiar pantalla al inicio
Hide
Type "clear" Enter
Sleep 1s
Show

# 1. Comprobar la versión instalada
Type "# Comprobamos la versión instalada" Enter
Sleep 1.5s
Type "eml_rename --version" Enter
Sleep 3s

# 2. Mostrar la ayuda completa y opciones disponibles
Enter
Type "# Ayuda y opciones completas de la herramienta" Enter
Sleep 1.5s
Type "eml_rename --help" Enter
Sleep 8s

Sleep 2s
