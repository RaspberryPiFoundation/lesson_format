# Manifest Files 

A manifest file is a json file which is a list of all files needed for a term.


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
            "note": "note for instructor"
        }
    ],
    "extras": [
        {
            "name": "notes",
            "materials": ["same as above"],
            "note": "note for instructor"
    ]
}
```

id is the identifier, and used for filenames and urls 
title is the proper name of the term, used for lists and headers
description is used in the term page, with a list of projects
number is the term number. currently scratch is 1&2, webdev is 3, python is 4.

then there is a list of projects, and a list of extra files to include


# Document Header

Each worksheet should contain a header, with a title, and level. Notes should contain a title.

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
```

The language is optional, but useful. the stylesheet is needed for scratch worksheets. Embeds is a string, or list of strings with glob patterns "*.foo" of images or files included in the document, needed for browsing.

Materials is a list of files, or glob patterns, of files that people will need to download to try out the exercise.

Note is a single file, or glob pattern, which is any notes for instructors which accompany the worksheet.

NB: the title, emebds, materials and note can also be set in the term manifest file

# Markdown formatting

We use pandoc, with a number of fairly common markdown extentions atop GitHub flavoured markdown.

- We use YAML blocks for header information
- Mark up introduction headers `# Intro {.intro}`
- To make a green "activity step headers" { .activty} is added to the step header (which needs to be a H1)
- For each checklist { .check} (needs to be h2 (+ remember to indent code blocks))
- For things to try { .try} (needs to be h2)
- For challenges { .challenge} (needs to be h2)
- For save { .save} (needs to be h2)
- For test { .flag} (because to run you code is to click a flag in Scratch I guess) needs to be h2
- use ```...``` delimited blocks for sources.

