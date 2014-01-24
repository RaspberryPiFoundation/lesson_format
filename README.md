# Static site builder for existing lessons


## Install

- Python 2, with pyyaml
- Pandoc (a recent version)
- Phantomjs

## Running

Check out the project repositories somewhere locally.

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
- Use pandoc scratchblocks filter to transform scratch into images
- Manifest for Term 1, handling notes and main file, no resources
- Copy across project notes, project materials into project directory
- Copy across term resources into term directory
- Transform any markdown which is a note for a project, or a resource for a term into html


## Todo

- Build index.html for each term
- Build index.html for each language
- Build index.html showing languages
- Style index and directory listings

- CCUK Legal disclaimer and template
- CCW legal disclaimer and template

- Zip/Bundle up project resources, add them to index
- Zip/Bundle up Terms, add them to index

- Complete Manifests for en-GB Scratch, Term 1 & 2
- Add missing headers to markdown project files.
- Manifests for en-GB Web Dev, Term 3

- Document manifest format 
- Unstyled PDF output, add it to index
- Custom TeX output for pandoc, to make PDFs look more in-house style.
- Nicer error messages and recovery
