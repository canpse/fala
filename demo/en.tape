# Gera demo/fa-en.gif:  bash demo/preparar.sh en && vhs demo/en.tape
Output demo/fa-en.gif

Set Shell "bash"
Set FontSize 22
Set Width 1200
Set Height 600
Set Padding 26
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set TypingSpeed 40ms

Hide
Type "source demo/ambiente.sh /tmp/project" Enter
Sleep 500ms
Show

Type "ls" Sleep 300ms Enter
Sleep 1.5s

# 1. juntar pdfs, trocando o nome do arquivo antes do Enter
Type "fa merge chapter1.pdf and chapter2.pdf into book.pdf"
Sleep 400ms Enter
Sleep 4s
Backspace 8
Sleep 300ms
Type "handbook.pdf"
Sleep 1.2s Enter
Sleep 1s

# 2. documento pra pdf
Type "fa convert report.docx to pdf"
Sleep 400ms Enter
Sleep 4s Enter
Sleep 4s

# 3. áudio
Type "fa convert song.wav to mp3, no logs"
Sleep 400ms Enter
Sleep 4s Enter
Sleep 1.5s

# 4. descompactar
Type "fa unzip photos.zip into a photos folder"
Sleep 400ms Enter
Sleep 4s Enter
Sleep 1.5s

Type "ls" Sleep 300ms Enter
Sleep 3s

Hide
Type "clear" Enter
Show
Type "# pipx install fala && fa --instalar claude"
Sleep 3.5s
