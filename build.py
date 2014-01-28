#!/usr/bin/env python
import os
import os.path
import sys
import shutil
import collections
import glob
import json
import subprocess
import tempfile
import string

import xml.etree.ElementTree as ET
try:
    import yaml
except ImportError:
    print >> sys.stderr, "You need to install pyyaml using pip or easy_install, sorry"
    sys.exit(-10)

Region = collections.namedtuple('Region','name stylesheets legal logo css_variables')
Style = collections.namedtuple('Style', 'name template stylesheets')

base = os.path.dirname(os.path.abspath(__file__))
template_base = os.path.join(base, "templates")

with open(os.path.join(template_base, "uk_legal.html")) as fh:
    uk_legal = fh.read()

with open(os.path.join(template_base, "world_legal.html")) as fh:
    world_legal = fh.read()

note_style = index_style = Style(
    name = 'lesson', 
    template = "template.html",
    stylesheets = ["/css/main.css", "/css/notes.css"],
)
index_style = Style(
    name = 'lesson', 
    template = "template.html",
    stylesheets = ["/css/main.css", "/css/index.css"],
)
lesson_style = Style(
    name = 'lesson', 
    template = "template.html",
    stylesheets = ["/css/main.css","/css/lesson.css"],
)

codeclubworld = Region(
    name='Code Club World',
    legal = world_legal,
    stylesheets = [],
    logo = "/img/ccw_logo.svg",
    css_variables = {
        "header_bg_light": "#ADCAEA",
        "header_bg_dark": "#007CC9",
        "header_text": "#FFFFFF",
    }
)

codeclubuk = Region(
    name='Code Club',
    legal = uk_legal,
    stylesheets = [],
    logo = "/img/ccuk_logo.svg",
    css_variables = {
        "header_bg_light": "#B1DAAE",
        "header_bg_dark": "#349946",
        "header_text": "#FFFFFF",
    }
)

# todo : real classes

Term = collections.namedtuple('Term', 'name language number projects extras')
Project = collections.namedtuple('Project', 'filename number title materials note embeds')
Extra = collections.namedtuple('Extra', 'name materials note')
Worksheet = collections.namedtuple('Worksheet','format filename')

css_assets = os.path.join(template_base,"css")

scratchblocks_filter = os.path.join(base, "pandoc_scratchblocks/filter.py")
html_assets = [os.path.join(base, "assets",x) for x in ("fonts", "img")]

# Markup process

def markdown_to_html(markdown_file, style, organization, output_file):
    commands = (
        "-f", "markdown_github+header_attributes+yaml_metadata_block+inline_code_attributes",
    )

    pandoc_html(markdown_file, style, organization, {}, commands, output_file)

def make_html(variables, html, style, organization, output_file):
    variables = dict(variables)
    variables['body'] = ET.tostring(html, encoding='utf-8', method='html')

    commands = (
        "-f", "html",
        "-R",
    )
    
    input_file = '/dev/null'

    pandoc_html(input_file, style, organization, variables, commands, output_file)


def pandoc_html(input_file, style, organization, variables, commands, output_file):
    cmd = [
        "pandoc",
        input_file, 
        "-o", output_file,
        "-t", "html5",
        "-s",  # smart quotes
        "--highlight-style", "pygments",
        "--section-divs",
        "--template=%s"%os.path.join(template_base, style.template), 
        "--filter", scratchblocks_filter,
        "-M", "legal=%s"%organization.legal,
        "-M", "organization=%s"%organization.name,
        "-M", "logo=%s"%organization.logo,
    ]
    for stylesheet in style.stylesheets:
        cmd.extend(("-c", stylesheet,))
    for stylesheet in organization.stylesheets:
        cmd.extend(("-c", stylesheet,))
    for k,v in variables.iteritems(): 
        cmd.extend(("-M", "%s=%s"%(k,v)))
    
    working_dir = os.path.dirname(output_file)

    subprocess.check_call(cmd, cwd=working_dir)


    
def build_pdf(markdown_file, style, output_file):
    # todo: add pandoc call, but use a different template
    # than the default, or perhaps a lua writer for xetex.
    # then call xetex :/
    pass


def process_file(input_file, style, organization, output_dir):
    output = []
    name, ext = os.path.basename(input_file).rsplit(".",1)
    if ext == "md":
        output_file = os.path.join(output_dir, "%s.html"%name)
        markdown_to_html(input_file, style, organization, output_file)
        output.append(Worksheet(filename=output_file, format="html"))
    else:
        output_file = os.path.join(output_dir, os.path.basename(input_file))
        shutil.copy(input_file, output_file)
        output.append(Worksheet(filename=output_file, format=ext))
    return output 

# Process files within project and resource containers

def build_project(project, organization, output_dir):
    # todo clean up this code because we keep repeating things.

    input_file = project.filename
    name, ext = os.path.basename(input_file).rsplit(".",1)

    output_files = process_file(input_file, lesson_style, organization, output_dir)

    notes = []

    if project.note:
        notes.extend(process_file(project.note, note_style, organization, output_dir))
    
    materials = []
    for file in project.materials:
        materials.append(copy_file(file, output_dir))

    embeds = []
    for file in project.embeds:
        embeds.append(copy_file(file, output_dir))

    # todo: zip materials. 

    return Project(
        filename = output_files,
        number = project.number,
        title = project.title,
        materials = materials,
        note = notes,
        embeds = embeds,
    )


def build_extra(extra, organization, output_dir):
    note = []
    if extra.note:
        note.extend(process_file(extra.note, note_style, organization, output_dir))
    materials = []
    for name in extra.materials:
        materials.append(copy_file(name, output_dir))
    return Extra(name = extra.name, note=note, materials=materials)

def sort_files(files):
    sort_key = {
        'html':2,
        'pdf':1,
    }
    return sorted(files, key=lambda x:sort_key.get(x.format,0), reverse=True)

def make_term_index(term, organization, output_dir):

    output_file = os.path.join(output_dir, "index.html")
    title = term.name

    root = ET.Element('body')
    section = ET.SubElement(root,'section', {'class':'projects'})
    h1 = ET.SubElement(section,'h1')
    h1.text = "Projects"
    ol = ET.SubElement(root, 'ol', {'class': 'projects'})
    
    for project in sorted(term.projects, key=lambda x:x.number):
        li = ET.SubElement(ol, 'li', {'class': 'projectfiles'})
        ul = ET.SubElement(li, 'ul')

        files = sort_files(project.filename)
        first, others = files[0], files[1:]

        url = os.path.relpath(first.filename, output_dir)

        a_li = ET.SubElement(ul, 'li')
        a = ET.SubElement(a_li, 'a', {'href': url})
        a.text = project.title or url

        for file in others:
            url = os.path.relpath(file.filename, output_dir)
            a_li = ET.SubElement(ul, 'li')
            a = ET.SubElement(a_li, 'a', {'href': url})
            a.text = file.format
            
        for file in project.note:
            url = os.path.relpath(file.filename, output_dir)
            a_li = ET.SubElement(ul, 'li')
            a = ET.SubElement(a_li, 'a', {'href': url})
            a.text = "Notes (%s)"%(file.format)


    for extra in term.extras:
        section = ET.SubElement(root, 'section', {'class':'extras'})
        h1 = ET.SubElement(section, 'h1')
        h1.text = extra.name
        ol = ET.SubElement(root, 'ol')

        if extra.note:
            file = sort_files(extra.note)[0]
            # todo: handle multiple formats
            url = os.path.relpath(file.filename, output_dir)
            li = ET.SubElement(ol, 'li')
            a = ET.SubElement(li, 'a', {'href': url})
            a.text = extra.name
        
        
        for file in extra.materials: 
            url = os.path.relpath(file.filename, output_dir)
            li = ET.SubElement(ol, 'li')
            a = ET.SubElement(li, 'a', {'href': url})
            a.text = file.filename


    make_html({'title':title, 'level':"T%d"%term.number}, root, index_style, organization, output_file)
    return output_file, term


def make_lang_index(language, terms, organization, output_dir):
    output_file = os.path.join(output_dir, "index.html")
    title = "Terms"

    root = ET.Element('section')
    h1 = ET.SubElement(root, 'h1')
    h1.text = "Projects"
    ol = ET.SubElement(root, 'ol')
    for term_index, term in sorted(terms, key=lambda x:x[1].number):
        url = os.path.relpath(term_index, output_dir)

        li = ET.SubElement(ol, 'li')
        a = ET.SubElement(li, 'a', {'href': url})
        a.text = term.name or url


    make_html({'title':title, 'level':language}, root, index_style, organization, output_file)
    return output_file

def make_index(languages, organization, output_dir):
    output_file = os.path.join(output_dir, "index.html")
    title = organization.name

    root = ET.Element('section')
    h1 = ET.SubElement(root, 'h1')
    h1.text = "Languages"
    ol = ET.SubElement(root, 'ol')

    for language, filename in languages.iteritems(): # todo, sort?
        url = os.path.relpath(filename, output_dir)

        li = ET.SubElement(ol, 'li')
        a = ET.SubElement(li, 'a', {'href': url})
        a.text = language


    make_html({'title':title}, root, index_style, organization, output_file)

def build(repositories, organization, output_dir):

    print "Searching for manifests .."

    termlangs = {}
    
    for m in find_files(repositories, ".manifest"):
        print "Found Manifest:", m
        try:
            term = parse_manifest(m)
            if term.language not in termlangs:
                termlangs[term.language] = []
            termlangs[term.language].append(term)
        except StandardError as e:

            import traceback
            traceback.print_exc()
            print "Failed", e

    print "Copying assets"

    copydir(html_assets, output_dir)
    css_dir = os.path.join(output_dir, "css")
    makedirs(css_dir)
    make_css(css_assets, organization, css_dir)

    languages = {}
    project_count = {}

    for language, terms in termlangs.iteritems():
        out_terms = []
        count = 0;
        lang_dir = os.path.join(output_dir, term.language)

        for term in terms:
            term_dir = os.path.join(lang_dir, "%s.%d"%(term.name, term.number))
            makedirs(term_dir)
            
            print "Building Term:", term.name,

            projects = []
            
            for p in term.projects:
                count+=1
                project = parse_project_meta(p)
                print "Building Project:", project.title, project.filename

                project_dir = os.path.join(term_dir,"%.02d"%(project.number))
                makedirs(project_dir)

                built_project = build_project(project, organization, project_dir)
                
                projects.append(built_project)

            extras = []
            
            for r in term.extras:
                print "Building Extra:", r.name
                extras.append(build_extra(r, organization, term_dir))

            term = Term(
                name = term.name, number = term.number, language = term.language,
                projects = projects,
                extras = extras,
            )

            out_terms.append(make_term_index(term, organization, term_dir))

            print "Term built!"

        print "Building",language,"index"

        languages[language]=make_lang_index(language, out_terms, organization, lang_dir)
        project_count[language]=count

    print "Building", organization.name, "index"

    sorted_languages = collections.OrderedDict()
    for lang in sorted(project_count.keys(), key=lambda x:project_count[x], reverse=True):
        sorted_languages[lang] = languages[lang]


    make_index(sorted_languages, organization, output_dir)
    print "Complete"
    
# Manifest and Project Header Parsing

def parse_manifest(filename):
    with open(filename) as fh:
        json_manifest = json.load(fh)
    
    base_dir = os.path.join(os.path.dirname(filename))

    projects = []
    for p in json_manifest['projects']:
        filename = expand_glob(base_dir, p['filename'], one_file=True)
        materials = expand_glob(base_dir, p.get('materials',[]))
        embeds = expand_glob(base_dir, p.get('embeds',[]))

        if 'note' in p:
            note = expand_glob(base_dir, p['note'], one_file=True)
        else:
            note = None
    
        project = Project(
            filename = filename,
            number = p['number'],
            title = p.get('title', None),
            materials = materials,
            note = note,
            embeds = embeds,
        )
        projects.append(project)

    extras = []
    for s in json_manifest.get('extras',()):
        if 'note' in s:
            note = expand_glob(base_dir, s['note'], one_file=True)
        else:
            note = None
        materials = expand_glob(base_dir, s.get('materials', ()))
        
        extras.append(Extra(
            name=s['name'],
            note=note,
            materials=materials,
        ))

    m = Term(
        name = json_manifest['name'],
        language = json_manifest['language'],
        number = int(json_manifest['number']),
        projects = projects,
        extras = extras,
    )

    return m

def parse_project_meta(p):
    if not p.filename.endswith('md'):
        return p

    with open(p.filename) as fh:

        in_header = False
        header_lines = []
        for line in fh.readlines():
            l = line.strip()
            if l == "---":
                in_header = True
            elif l == "...":
                in_header = False
            elif in_header:
                header_lines.append(line)
    header = yaml.safe_load("".join(header_lines))

    if header:
        title = header.get('title', p.title)
        number = header.get('number', p.number)
        title = header.get('title', p.title)

        raw_note = header.get('note', None)
        if raw_note:
            base_dir = os.path.dirname(p.filename)
            note = expand_glob(base_dir, raw_note, one_file=True)
        else:
            note = p.note

        raw_materials = header.get('materials', ())
        if raw_materials:
            base_dir = os.path.dirname(p.filename)
            materials = expand_glob(base_dir, raw_materials)
            materials.extend(p.materials)
        else:
            materials = p.materials

        raw_embeds = header.get('embeds', ())
        if raw_embeds:
            base_dir = os.path.dirname(p.filename)
            embeds = expand_glob(base_dir, raw_embeds)
            embeds.extend(p.embeds)
        else:
            embeds = p.embeds

        return Project(
            filename = p.filename,
            number = number,
            title = title,
            materials = materials,
            note = note,
            embeds = embeds,
        )
    else:
        return p

def make_css(stylesheet_dir, organization, output_dir):
    for asset in os.listdir(stylesheet_dir):
        if not asset.startswith('.'):
            src = os.path.join(stylesheet_dir, asset)
            dst = os.path.join(output_dir, asset)
            if os.path.exists(dst):
                if os.path.isdir(dst):
                    shutil.rmtree(dst)
                    makedirs(dst)
                else:
                    os.remove(dst)
                    
            if os.path.isdir(src):
                make_css(src, organization, dst)
            else:
                if asset.endswith('.css'):
                    with open(src,"r") as src_fh, open(dst,"w") as dst_fh:
                        template = string.Template(src_fh.read())
                        dst_fh.write(template.substitute(organization.css_variables))

                else:
                    shutil.copy(src, output_dir)
    
# File and directory handling

def find_files(dir, extension):
    manifests = []
    def visit(m, dirname, names):
        for n in names:
            if n.endswith(extension):
                m.append(os.path.join(dirname, n))
    for d in dir:
        os.path.walk(d, visit, manifests)
    
        
    return manifests

def expand_glob(base_dir, paths, one_file=False):
    if one_file:
        output = glob.glob(os.path.join(base_dir, paths))
        if len(output) != 1:
            print os.path.join(base_dir, paths), output
            raise AssertionError("Bad things")
        return output[0]

    else:
        output = []
        if not hasattr(paths, '__iter__'):
            paths = (paths,)
        for p in paths:
            output.extend(glob.glob(os.path.join(base_dir, p)))
        return output
    
def makedirs(path, clear=False):
    if clear and os.path.exists(path):
        shutil.rmtree(path)
    if not os.path.exists(path):
        os.makedirs(path)


def copydir(assets, output_dir):
    for src in assets:
        asset = os.path.basename(src)
        if not asset.startswith('.'):
            dst = os.path.join(output_dir, asset)
            if os.path.exists(dst):
                if os.path.isdir(dst):
                    shutil.rmtree(dst)
                else:
                    os.remove(dst)
                    
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy(src, output_dir)


def copy_file(input_file, output_dir):
        name, ext = os.path.basename(input_file).rsplit(".",1)
        output_file = os.path.join(output_dir, os.path.basename(input_file))
        shutil.copy(input_file, output_file)
        return output_file


if __name__ == '__main__':
    args = sys.argv[1::]
    if len(args) < 3:
        print "usage: %s <region> <input repository directories> <output directory>"
        sys.exit(-1)

    organization = {'world':codeclubworld, 'uk':codeclubuk}[args[0]]
    args = [os.path.abspath(a) for a in args[1:]]

    repositories, output_dir = args[:-1], args[-1]

    build(repositories, organization, output_dir)

    sys.exit(0)

