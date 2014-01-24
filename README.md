# Static site builder for existing lessons


## Install

- Python 2, with pyyaml
- Pandoc (a recent version)
- Phantomjs

## Running

```
./build.sh <path to python repository> <path to scratch repository> ... <output_directory>
```

## Testing

Run a webserver in the output directory, e.g.

```
$ python -m SimpleHTTPServer
```

## Status

- Builds Python lessons from manifest, transforming markdown into html


## Todo

- Use pandoc scratchblocks filter to transform scratch into images
- Manifests for en-GB Scratch, Term 1 & 2
- Manifests for en-GB Web Dev, Term 3
- Document manifest format 
- Build index.html for each term
- Build index.html for each language
- Build index.html showing languages
- Style index and directory listings
- CCUK Legal disclaimer and template
- CCW legal disclaimer and template
- Zip/Bundle up project resources, add them to index
- Zip/Bundle up Terms, add them to index
- Unstyled PDF output, add it to index
- Custom TeX output for pandoc, to make PDFs look more in-house style.
- Nicer error messages and recovery
