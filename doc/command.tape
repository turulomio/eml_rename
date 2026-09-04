# VHS documentation
#
# Output:
#   Output <path>.gif               Create a GIF output at the given <path>
#   Output <path>.mp4               Create an MP4 output at the given <path>
#   Output <path>.webm              Create a WebM output at the given <path>
#
# Require:
#   Require <string>                Ensure a program is on the $PATH to proceed
#
# Settings:
#   Set FontSize <number>           Set the font size of the terminal
#   Set FontFamily <string>         Set the font family of the terminal
#   Set Height <number>             Set the height of the terminal
#   Set Width <number>              Set the width of the terminal
#   Set LetterSpacing <float>       Set the font letter spacing (tracking)
#   Set LineHeight <float>          Set the font line height
#   Set LoopOffset <float>%         Set the starting frame offset for the GIF loop
#   Set Theme <json|string>         Set the theme of the terminal
#   Set Padding <number>            Set the padding of the terminal
#   Set Framerate <number>          Set the framerate of the recording
#   Set PlaybackSpeed <float>       Set the playback speed of the recording
#   Set MarginFill <file|#000000>   Set the file or color the margin will be filled with.
#   Set Margin <number>             Set the size of the margin. Has no effect if MarginFill isn't set.
#   Set BorderRadius <number>       Set terminal border radius, in pixels.
#   Set WindowBar <string>          Set window bar type. (one of: Rings, RingsRight, Colorful, ColorfulRight)
#   Set WindowBarSize <number>      Set window bar size, in pixels. Default is 40.
#   Set TypingSpeed <time>          Set the typing speed of the terminal. Default is 50ms.
#
# Sleep:
#   Sleep <time>                    Sleep for a set amount of <time> in seconds
#
# Type:
#   Type[@<time>] "<characters>"    Type <characters> into the terminal with a
#                                   <time> delay between each character
#
# Keys:
#   Escape[@<time>] [number]        Press the Escape key
#   Backspace[@<time>] [number]     Press the Backspace key
#   Delete[@<time>] [number]        Press the Delete key
#   Insert[@<time>] [number]        Press the Insert key
#   Down[@<time>] [number]          Press the Down key
#   Enter[@<time>] [number]         Press the Enter key
#   Space[@<time>] [number]         Press the Space key
#   Tab[@<time>] [number]           Press the Tab key
#   Left[@<time>] [number]          Press the Left Arrow key
#   Right[@<time>] [number]         Press the Right Arrow key
#   Up[@<time>] [number]            Press the Up Arrow key
#   Down[@<time>] [number]          Press the Down Arrow key
#   PageUp[@<time>] [number]        Press the Page Up key
#   PageDown[@<time>] [number]      Press the Page Down key
#   Ctrl+<key>                      Press the Control key + <key> (e.g. Ctrl+C)
#
# Display:
#   Hide                            Hide the subsequent commands from the output
#   Show                            Show the subsequent commands in the output

# VHS Tape: Demostración del uso de eml_rename
# Genera command.gif

Output command.gif

Require echo

Set Shell "bash"
Set FontSize 15
Set Width 1200
Set Height 650
Set WindowBar Colorful
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms
Set PlaybackSpeed 1.0

# Prepara el entorno accediendo al directorio demo
Hide
Type "cd demo && clear" Enter
Sleep 1s
Show

# 1. Mostrar los correos originales antes del procesado
Type "# Paso 1: Correos originales sin formato" Enter
Sleep 1.5s
Type "ls -1" Enter
Sleep 3s

# 2. Ejecutar eml_rename en modo simulación (dry-run sin modificar ficheros)
Enter
Type "# Paso 2: Simulamos el renombrado con eml_rename (dry-run)" Enter
Sleep 1.5s
Type "eml_rename" Enter
Sleep 6s

# 3. Aplicar el renombrado real en disco mediante la opción --save
Enter
Type "# Paso 3: Aplicamos los cambios en disco con --save" Enter
Sleep 1.5s
Type "eml_rename --save" Enter
Sleep 6s

# 4. Comprobar los nuevos nombres estandarizados: YYYYMMDD HHMM [remitente] asunto
Enter
Type "# Paso 4: Comprobamos los nuevos nombres de archivo generados" Enter
Sleep 1.5s
Type "ls -1" Enter
Sleep 4s

# 5. Volver a ejecutar para verificar la protección de ficheros ya renombrados
Enter
Type "# Paso 5: Proteccion: los ficheros ya formateados se respetan" Enter
Sleep 1.5s
Type "eml_rename" Enter
Sleep 5s

Sleep 2s

