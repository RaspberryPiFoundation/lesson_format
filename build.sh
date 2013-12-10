#!/bin/bash
MARKDOWN="markdown_github+header_attributes+yaml_metadata_block+inline_code_attributes"
PANDOC_HTML="pandoc -f $MARKDOWN -t html5 -s --highlight-style pygments --section-divs --template=templates/template.html"
#PANDOC_PDF="pandoc -f $MARKDOWN -t latex  --latex-engine=pdflatex"


DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OUT=output; pushd $DIR > /dev/null
rm -fR $OUT; mkdir -p $OUT; touch $OUT/.keep

UK_LEGAL="./templates/uk_legal.html"
WORLD_LEGAL="./templates/world_legal.html"
LEGAL="$WORLD_LEGAL"

for f in examples/example.md;
do
	base=`basename "$f"`
	output="lesson${base%%.*}.html"
	$PANDOC_HTML --include-after-body "$LEGAL" "$f" -o "$OUT/$output"
	#pdf="lesson${base%%.*}.pdf"
	#$PANDOC_PDF "$f"  -o "$OUT/$pdf"

done

cp -r templates/assets/ $OUT


