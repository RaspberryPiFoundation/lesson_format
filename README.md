# Lesson Formatter

Currently prototyping, working on building HTML output for markdown sources for lessons. 

We use pandoc, with a number of fairly common markdown extentions atop GitHub flavoured markdown.

- We use YAML blocks for header information
- Mark up introduction headers `# Intro {.intro}`
- To make a green "activity step headers" { .activty} is added to the step header
- For each checklist { .check}
- For things to try { .try}
- For challenges { .challenge}
- For save { .save}
- For test { .flag} (because to run you code is to click a flag in Scratch I guess)
- use ```...``` delimited blocks for sources.


We are using this for the Python Lessons, as well as the Scratch ones, and you can track our progress here

- https://github.com/CodeClub/scratch-curriculum/issues/67
- https://github.com/CodeClub/scratch-curriculum/issues/68
