*** This repository is soon to be retired. Please read github issue 168 (https://github.com/CodeClub/lesson_format/issues/168) for more information. ***

# Code Club Lesson Formatter

The lesson formatter transforms our markdown lessons into a static website.

## Installation and Running

The site builder is a python script, which uses [pandoc](http://johnmacfarlane.net/pandoc/) for rendering, as well as [phantom.js](http://phantomjs.org/) for beautifying scratch code. For generating PDFs, it uses phantom.js.

If you have downloaded a zip file, you will need to set the script pandoc_scratchblocks/filter.py to +x

These instructions are for installing on linux / OSX. You may be able to get it running on Windows, but unfortunately we’re not able to help with that. Sorry.

We recommend using [virtualenv](https://virtualenv.pypa.io/en/latest/) when working with any Python project, and have illustrated this as an optional step in the installation instructions below.

### Dependencies

- [Python 2](https://www.python.org/download), [pip](http://pip.readthedocs.org/en/latest/installing.html)
- [Pandoc](http://johnmacfarlane.net/pandoc/installing.html) >= 1.12
- [node.js](http://nodejs.org/download/)

### Installing

```
# clone the repo
git clone https://github.com/CodeClub/lesson_format.git && cd lesson_format

# [optional] create a virtual environment using virtualenv
virtualenv venv
source venv/bin/activate

# install python requirements
pip install -r requirements.txt

# install phantom.js etc
npm install
```

### Running

The script reads from locally checked out files, and writes to an output directory. We run it with the `scratch-curriculum`, `webdev-curriculum`, and `python-curriculum` as inputs, and write to a directory.

The first argument is the theme for the website, currently either `world` or `uk`. Always specify `world`.

### Compiling Sass

```
# install css compilation stuff
bundle install

# install bower dependencies
$(npm bin)/bower install

# compile the Sass
$(npm bin)/grunt sass:dev
```

### Examples

```
./build.py world lessons/scratch lessons/webdev lessons/python output/codeclubworld
```

To build the PDFs, specify the `--pdf phantomjs` option as follows:

```
./build.py --pdf phantomjs world lessons/scratch lessons/webdev lessons/python output/codeclubworld
```

There is also a makefile which can be used to automate the process.

- First run `make clone` to build a local copy of all of the source and target repositories
- Next, run `make pages_world`.

You only need to run `make clone` once, and not before every `make pages_world`.

## Lesson Formatting

See [this guide](https://github.com/CodeClub/curriculum_documentation/blob/master/projects.md) to writing projects.

## Term Manifests

A manifest file is a json file which is a list of all files needed for a term, and looks like the following:

```
{
    "id": "example",
    "title":"Example Term",
    "description":"This is for example purposes",
    "language": "en-GB",
    "number": 1,

    "projects": [
        {
            "filename": "01 Felix and Herbert/01 Felix and Herbert.md",
            "number": 1
        },
        {
            "filename": "02 Ghostbusters/02 Ghostbusters.md",
            "number": 2
        }
    ],
    "extras": [
        {
            "name": "Volunteer notes",
            "note": "volunteer resources/*.md"
        }
    ]
}
```

- id is the identifier, and used for filenames and urls
- title is the proper name of the term, used for lists and headers
- description is used in the term page, with a list of projects
- number is the term number. currently scratch is 1 & 2, webdev is 3, python is 4.

Then there is a list of projects, and a list of extra files to include.

- Projects must contain `filename` and `number`, but optionally any project header can be included here too, including `note`, `materials`, `title`.

You can find the [manifest for the en-GB scratch term 1 here](https://github.com/CodeClub/lesson_format/blob/master/lessons/scratch/en-GB/Term 1/en-GB_scratch_term1.manifest).

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
        "Download PDF": "…",
        "Download Project Materials": "…",
        "Extras": "…"
    }
}
```

You can find a full list of translations [in the en-GB.language.sample file](https://github.com/CodeClub/lesson_format/blob/master/assets/languages/en-GB.language.sample).

## Themes

There are two themes, Code Club World, and Code Club UK. They specify the default css, html templates, and css color variables. You should always specify that you want the Code Club World theme as the UK theme is no longer used.

## Underneath the hood

Before starting, themes are loaded from `assets/themes/*` and language support from `assets/languages/*`.

Various directories and files from `/assets` are then copied directly to the output.

All of the input directories are scanned for manifest files, and an index is built for each language, containing all of the terms.

It then creates `/<lang-code>/<term>-<num>/<project num>/<project files>` for each project and ancillary data, creating indexes by language, term, too.

## Testing

Run a webserver in the output directory, e.g.

```
$ cd <output directory>
$ python -m SimpleHTTPServer <port>
```
