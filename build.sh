#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OUT=output
pushd $DIR > /dev/null
rm -fR $OUT
mkdir -p $OUT
touch $OUT/.keep


legal="templates/UK_LEGAL.md"

MARKDOWN="markdown_github+header_attributes+yaml_metadata_block+inline_code_attributes"

PANDOC_HTML="pandoc -f $MARKDOWN -t html5 -s --highlight-style pygments -c codeclub.css --section-divs --template=templates/template.html"

PANDOC_PDF="pandoc -f $MARKDOWN -t latex  --latex-engine=pdflatex"


for f in examples/example.md;
do
	base=`basename "$f"`
	output="lesson${base%%.*}.html"
	$PANDOC_HTML --include-after-body "$legal" "$f" -o "$OUT/$output"
	#pdf="lesson${base%%.*}.pdf"
	#cat "$f" "$legal" | $PANDOC_PDF  -o "$OUT/$pdf"

done

cp -r assets/ $OUT


