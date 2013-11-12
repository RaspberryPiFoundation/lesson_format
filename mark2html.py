#!/usr/bin/env python
'''Command line for generating Code Club lessons.

Example:

  
'''

import markdown
import codecs
import re
from string import Template

#### Template definition ########

#Templates

lessonBodyTemplate =  """
<!DOCTYPE html>
<html lang="$lang">
<head>
    <meta charset="utf-8">
    <meta name="description" content="Code Club - $curriculum - $level - $lesson - $lesson_title">
    <title> Code Club - $curriculum - $level - $lesson - $lesson_title </title>
    <link rel="stylesheet" href="../../assets/codeclub.css">
    <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.7.2/jquery.js"></script> 
    <link rel="stylesheet" href="../../assets/scratchblocks2.css">
    <script src="../../assets/scratchblocks2.js"></script>

    
</head>
<body>
<div id="cclesson">

$intro
$activities

</div>

<!-- Parse blocks -->
    <script>
        scratchblocks2.parse("code.scratch");         
     </script>
</body>
</html>
"""
lessonIntroTemplate = """
    <section class="intro">
        <header>
            
            <div> <strong> $level </strong></div>
            <h1> $lesson_title </h1>
            
         </header>

         $intro_text
        
         </section>
"""
lessonActivityTemplate = """
    <section class="activity">
        <header>
            
            <div> <strong> $level </strong></div>
            <h1> $lesson_title </h1>
            
         </header>

         $lesson_text
        
         </section>
"""

#### End Template definition ####




def parse_cmdline_vars(cmdline_vars):
    return dict(var.split('=', 1) for var in cmdline_vars)

def get_meta(md,key,default):
    return ' '.join(md.Meta.get(key,default))



def main(argv=None):
    import sys
    from argparse import ArgumentParser, FileType

    argv = argv or sys.argv

    parser = ArgumentParser(description='Generate Code Club lessons from markup')
    parser.add_argument('markdown', help='markdown lesson folder')
    parser.add_argument('--output', '-o', help='output html file')


    args = parser.parse_args(argv[1:])
    


    #  Read markdown file and meta data
    markin = codecs.open(args.markdown, mode="r", encoding="utf-8").read()
    output_file = codecs.open(args.output, "w", encoding="utf-8", errors="xmlcharrefreplace")


    #Split into section using ~+ separator
    sep = re.compile("\^{3,}")
    sections = sep.split(markin)
    md = markdown.Markdown(['attr_list','meta','fenced_code']) 
    introHtml = md.convert(sections[0])

    #Extract meta data
    lang = get_meta(md,'lang','en')
    curriculum = get_meta(md,'curriculum','Curriculum')
    level = get_meta(md,'level','Level ?')
    lesson = get_meta(md,'lesson', 'Lesson ?')
    lesson_title = get_meta(md,'lesson_title','Title')

    #Load body template
    html = Template(lessonBodyTemplate);

    #Load intro temaplate
    intro = Template(lessonIntroTemplate);
    activity = Template(lessonActivityTemplate);
    #Load Activity template



    #Substitute placeholder

    introSub = intro.substitute(level=level, lesson_title=lesson_title, intro_text=introHtml)

  
    #Generate activities html
    activitySub = ''
    for activitymd in sections[1:]:
        activityHtml = md.convert(activitymd)
        activitySub += activity.substitute(level=level, lesson_title=lesson_title, lesson_text=activityHtml)

    htmlSub = html.substitute(lang=lang, curriculum=curriculum, level=level, lesson=lesson, lesson_title=lesson_title, intro=introSub, activities=activitySub)
    output_file.write(htmlSub)


if __name__ == '__main__':
    main()

