# Lesson Formatter

Currently prototyping, working on building HTML output for markdown sources for lessons. 

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


We are using this for the Python Lessons, as well as the Scratch ones, and you can track our progress here

- https://github.com/CodeClub/scratch-curriculum/issues/67
- https://github.com/CodeClub/scratch-curriculum/issues/68
