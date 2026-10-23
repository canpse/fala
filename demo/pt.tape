# Gera demo/fa-pt.gif:  bash demo/preparar.sh pt && vhs demo/pt.tape
Output demo/fa-pt.gif

Set Shell "bash"
Set FontSize 22
Set Width 1200
Set Height 600
Set Padding 26
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set TypingSpeed 40ms

Hide
Type "source demo/ambiente.sh /tmp/projeto" Enter
Sleep 500ms
Show

Type "ls" Sleep 300ms Enter
Sleep 1.5s

# 1. juntar pdfs, trocando o nome do arquivo antes do Enter
Type "fa junta capitulo1.pdf e capitulo2.pdf num livro.pdf"
Sleep 400ms Enter
Sleep 4s
Backspace 9
Sleep 300ms
Type "apostila.pdf"
Sleep 1.2s Enter
Sleep 1s

# 2. documento pra pdf
Type "fa converte relatorio.docx pra pdf"
Sleep 400ms Enter
Sleep 4s Enter
Sleep 4s

# 3. áudio
Type "fa converte musica.wav pra mp3, sem log"
Sleep 400ms Enter
Sleep 4s Enter
Sleep 1.5s

# 4. descompactar
Type "fa descompacta fotos.zip numa pasta fotos"
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
