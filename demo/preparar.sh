#!/usr/bin/env bash
# Monta a pasta da demonstração (precisa de ffmpeg, soffice, zip e python-docx).
# Uso: bash demo/preparar.sh pt && vhs demo/pt.tape    (ou en / en.tape)
set -eu
if [ "${1:-pt}" = en ]; then
    d=/tmp/project c1=chapter1 c2=chapter2 doc=report som=song zip=photos foto=beach
else
    d=/tmp/projeto c1=capitulo1 c2=capitulo2 doc=relatorio som=musica zip=fotos foto=praia
fi
rm -rf "$d" && mkdir -p "$d" && cd "$d"
printf 'Capítulo 1\n\nEra uma vez.\n' > $c1.txt
printf 'Capítulo 2\n\nFim.\n' > $c2.txt
soffice --headless --convert-to pdf $c1.txt $c2.txt >/dev/null 2>&1
rm $c1.txt $c2.txt
python3 -c "
import docx
d = docx.Document(); d.add_heading('Relatório', 1); d.add_paragraph('Tudo certo.'); d.save('$doc.docx')"
ffmpeg -loglevel error -f lavfi -i "sine=frequency=440:duration=3" -y $som.wav
mkdir z
for i in 1 2 3; do ffmpeg -loglevel error -f lavfi -i testsrc=size=320x240 -frames:v 1 -y "z/$foto$i.jpg"; done
(cd z && zip -q ../$zip.zip ./*.jpg) && rm -r z
