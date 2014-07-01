# Code Club Lesson Formatter

The lesson formatter transforms our markdown lessons into a static website.

You can see an example term in this repository, complete with a scratch lesson, python lesson, and term manifest.

## Code Club Markdown

We use the GitHub flavoured Markdown that pandoc understands, in particular the format `markdown_github+header_attributes+yaml_metadata_block+inline_code_attributes`. Pandoc's documentation covers these options and more http://johnmacfarlane.net/pandoc/demo/example9/pandocs-markdown.html

In particular:

- Each markdown file can begin with a YAML header
- Headers in markdown `# Header` can be annotated with styles `# {.style}`
- Fenced Code blocks can specify their language
- Inline code sections can too

For Example

    ---
    title: An example Markdown File
    ...

    # Introduction {.intro}

    ```scratch
    when FLAG clicked
      move 10 steps
    ```

## Headers in Markdown files.

Each markdown file should contain a YAML block, with the title set. For lessons, the header should contain a title, and level.

An example lesson header looks like this:

```
---
title: Felix and Herbert
level: Level 1
language: en-GB
stylesheet: scratch
embeds: "*.png"
materials: "Felix-and-Herbert.sb"
note: "notes for club leaders.md"
...

Rest of markdown file ...
```

- The language is optional, but useful.
- The stylesheet is needed for scratch worksheets.
- Embeds is a file, or a list of files for images used inside the document
- Materials is a file, or list of files of things that accompany the lesson (e.g scratch files)
- Note is the filename of the optional notes for volunteers.
- Level is the difficulty of the project.

Any file name is taken to be relative to the markdown file's directory, file names can also be globbed, i.e "*.png".

The lesson formatter parses these headers for building the static pages and indexes, however they can also be defined in the Term Manifest, which is detailed later.

## Code Club Markdown Annotations

Each lesson begins with an introduction,

- Mark up introduction headers `# Intro {.intro}` (always a h1)

Each lesson is broken down into steps

- Mark up steps with `# Step 1 {.activity}` (always a h1)

Each step has a series of activities, in a list.

- Before each list, use a subheader `## Activity checklist {.check}` (always a h2)

Each step can have things to optionally try.

- Use `## Things to try {.try}` (always h2)

Each step can also have challenges too.

- Use `## Challenge {.challenge}` (always a h2)

A note to save:

- Use `## Save Your Project {.save}` (always a h2)

A note to test:

- Use `## Test Your Project {.flag}` (always a h2)

## Scratchblocks

We use the scratchblocks2 library, and PhantomJS to render scratch blocks as png files.

Scratch blocks inside lessons must follow the syntax set out here: http://wiki.scratch.mit.edu/wiki/Block_Plugin/Syntax

You can test your syntax here, http://blob8108.github.io/scratchblocks2/, (remembering to set the language!).

We use `scratch`, or `blocks` as the name of the language, for example, in markdown:

    Some paragraph

    ```scratch
    when FLAG clicked
      move 10 steps
    ```

    Another paragraph


## Term Manifests

A manifest file is a json file which is a list of all files needed for a term, and looks like the following:

```
{
    "id": "example",
    "title":"Example Term",
    "description":"This is for example purposes",
    "language": "en-GB",
    "number": 0,

    "projects": [
        {
            "filename": "01 Turtle Power/01.md",
            "number": 1
        },
        {
            "filename": "02 Ghostbusters/Ghostbusters.md",
            "number": 2
        },
        {
            "filename": "pdf/*.pdf",
            "number": 3,
            "title": "A lesson",
            "materials": ["files to include in the lesson downlaod"],
            "note": "note for instructor",
            "extras": [
                {
                    "name": "Handout",
                    "materials": ["same as above"],
                    "note": "lesson-handout.md"
                }

            ]
        }
    ],
    "extras": [
        {
            "name": "notes",
            "materials": ["same as above"],
            "note": "note for instructor"
        }
    ]
}
```

- id is the identifier, and used for filenames and urls
- title is the proper name of the term, used for lists and headers
- description is used in the term page, with a list of projects
- number is the term number. currently scratch is 1&2, webdev is 3, python is 4.

Then there is a list of projects, and a list of extra files to include

- Projects must contain `filename` and `number`, but optionally any project header can be included here too, including `note`, `materials`, `title`.

## Translations

The lesson formatter can use different languages in the project listing.

```
{
        "code": "en-GB",
        "name": "English",
        "legal": {
            "uk": "Disclaimer for Code Club UK, UK ONLY",
            "world": "Disclaimer for Code Club World, OUTSIDE UK"
        },
        "translations": {
            "Projects": "Translation",
            "Notes": "...",
            "Extras": "...."
        }
}
```


## Themes

There are two themes, Code Club World, and Code Club UK. They specify the default css, html templates, and css color variables.

# Installation and Running

The site builder is a python script, which uses pandoc for rendering, as well as phantomjs for handling scratch.

If you have downloaded a zip file, you will need to set the script pandoc_scratchblocks/filter.py to +x

It won't work on Windows.

## Dependencies

- Python 2, with the pyyaml library (`pip install pyyaml`)
- Pandoc (a recent version, 1.12 or newer)
- Phantomjs

### Compiling CSS

You'll need the following to compile the SASS files into CSS.
- [Node.JS](http://nodejs.org/)
- [NPM](https://www.npmjs.org/)
- Grunt (`npm install -g grunt-cli`)
- Bower (`npm install -g bower`, then `bower install`)
- sass-globbing (`sudo gem install sass-globbing`)

## Running

The script reads from locally checked out files, and writes to an output directory. We run it with the `scratch-curriculum`, `webdev-curriculum`, and `python-curriculum` as inputs, and write to a directory.

The first argument is the theme for the website, currently either `world` or uk`.

### Examples:

```
./build.py world <path to python repository> <path to scratch repository> ... <world output repository>
./build.py uk <path to python repository> <path to scratch repository> ... <uk output repository>
```

There is also a makefile which can be used to automate the process. First run `make clone` to build a local copy of all of the source and target repositories, then run `make pages_uk pages_world` or just `make pages_uk`/`make pages_world`. You only need to run `make clone` once, and not before every `make pages_uk pages_world`.

If you have changed the resources, you should force the build script to rebuild the zip files. This is done by passing a flag `--rebuild` to `build.py`, i.e `./build.py --rebuild uk ...` or `make options=--rebuild pages_uk pages_world`

## Underneath the hood

It loads themes from `themes/*`, language support from `languages/*`, before starting.

It copies /assets over, then copies /templates/css over, replacing ${variables} inside the files. These variables are set in the theme configuration file.

It scans all of the input directories for manifest files, and builds up an index for each
language, containing all of the terms.

It then creates `/<lang-code>/<term>-<num>/<project num>/<project files>` for each project and ancillary data,
creating indexes by language, term, too.

## Testing

Run a webserver in the output directory, e.g.

```
$ cd <output directory>
$ python -m SimpleHTTPServer <port>
```

## Bugs/Features Missing

When it encounters an error in the manifest, the entire term is skipped. Errors can be missing files or json syntax errors.

Only projects can have embedded files, not notes. If you have a note/extra with pngs etc, put those file names inside the manifest, under the project embeds.
