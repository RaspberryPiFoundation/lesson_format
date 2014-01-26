# Status

- Builds Python lessons from manifest, transforming markdown into html
- Use pandoc scratchblocks filter to transform scratch into images
- Manifest for Term 1, handling notes and main file, no resources
- Copy across project notes, project materials into project directory
- Copy across term resources into term directory
- Transform any markdown which is a note for a project, or a resource for a term into html
- CCW/UK legal disclaimer
- Clean up and split out CSS
    - make a new template to start from, not lesson_template.html
    - Inject the logo into the document
    - level should only be inserted if there.
- Term, Language, Root Index Created.
- Write links to worksheets, links to terms

## Next

- Write links to extra items in project index.
- Write links to alternative formats for project worksheets
- Write links to project materials for projects.

- Generate CCW/CCUK builds
    - Parse arguments..
    - Seperate out colours and styles
    - Split out CSS for lesson, and world scheme.
    - Templated CSS by python, generate when copying across? (heh, sweet)

- Zip/Bundle up project resources, add them to index
- Zip/Bundle up Terms, add them to index

- Print and media queries for sizes.

- Tidy up manifests
- Complete Manifests for en-GB Scratch, Term 1 & 2
- Add missing headers to markdown project files.
- Manifests for en-GB Web Dev, Term 3

- Document the manifest format 
- Unstyled PDF output, add it to index
- Custom TeX output for pandoc, to make PDFs look more in-house style.
- Nicer error messages and recovery
