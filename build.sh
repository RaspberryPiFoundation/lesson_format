#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OUT=output
pushd $DIR
rm -fR $OUT
mkdir -p $OUT


legal="templates/UK_LEGAL.md"

MARKDOWN="markdown_github+header_attributes+yaml_metadata_block+inline_code_attributes"

PANDOC_HTML="pandoc -f $MARKDOWN -t html5 -s --highlight-style pygments -c codeclub.css --section-divs --template=templates/template.html"

PANDOC_PDF="pandoc -f $MARKDOWN -t latex  --latex-engine=pdflatex"


for f in examples/example.md;
do
	base=`basename "$f"`
	output="lesson${base%%.*}.html"
	cat "$f" "$legal" | $PANDOC_HTML -o "$OUT/$output"
	#pdf="lesson${base%%.*}.pdf"
	#cat "$f" "$legal" | $PANDOC_PDF  -o "$OUT/$pdf"

done

#cat "../en-GB/volunteer resources/resources_and_gotchas.md" | $PANDOC_HTML -o "$OUT/guide.html"
#cat "../en-GB/volunteer resources/resources_and_gotchas.md" | $PANDOC_PDF -o "$OUT/guide.pdf"

cp -r assets/ $OUT


