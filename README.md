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
- CCW legal disclaimer and template
- CCUK Legal disclaimer and template

## Next

- Clean up and split out CSS
    - make a new template to start from, not lesson_template.html
        - Inject the logo into the document
        - Seperate out colours and styles
        - inject colors too with inline stylesheet, or ?
    - Move lesson specific things to own lesson sheet.
    - level should only be inserted if there.
- Print and media queries for sizes.

## Todo

- Split out CSS for lesson, scratch, and world scheme.

- Build index.html for each term
- Build index.html for each language
- Build index.html showing languages
- Style index and directory listings


- Zip/Bundle up project resources, add them to index
- Zip/Bundle up Terms, add them to index

- Complete Manifests for en-GB Scratch, Term 1 & 2
- Add missing headers to markdown project files.
- Manifests for en-GB Web Dev, Term 3

- Document manifest format 
- Unstyled PDF output, add it to index
- Custom TeX output for pandoc, to make PDFs look more in-house style.
- Nicer error messages and recovery
