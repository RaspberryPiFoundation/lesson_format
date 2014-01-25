#!/usr/bin/env python
import os
import os.path
import sys
import shutil
import collections
import glob
import json
import subprocess
try:
    import yaml
except ImportError:
    print >> sys.stderr, "You need to install pyyaml using pip or easy_install, sorry"
    sys.exit(-10)

# todo : real classes
Term = collections.namedtuple('Term', 'name language number projects extras')
Project = collections.namedtuple('Project', 'filename number title materials notes')
Extra = collections.namedtuple('Extra', 'name materials notes')
Style = collections.namedtuple('Style', 'name template stylesheets')
Region = collections.namedtuple('Region','name stylesheets legal logo')

base = os.path.dirname(os.path.abspath(__file__))

template_base = os.path.join(base, "templates")
html_assets = os.path.join(base, "assets")
scratchblocks_filter = os.path.join(base, "pandoc_scratchblocks/filter.py")

with open(os.path.join(base, "templates/uk_legal.html")) as fh:
    uk_legal = fh.read()

with open(os.path.join(base, "templates/world_legal.html")) as fh:
    world_legal = fh.read()

note_style = lesson_style = Style(
    name = 'lesson', 
    template = "lesson_template.html",
    stylesheets = ["/css/lesson.css"],
)

codeclubworld = Region(
    name='Code Club World',
    legal = world_legal,
    stylesheets = [],
    logo = "/img/logo.svg",
)

def build(repositories, organization, output_dir):

    print "Searching for manifests .."

    manifests = []
    
    for m in find_files(repositories, ".manifest"):
        print "Found Manifest:", m
        try:
            manifests.append(parse_manifest(m))
        except StandardError:
            print "Failed"

    print "Copying assets"

    copydir(html_assets, output_dir), 

    terms = []
    for term in manifests:
        term_dir = os.path.join(output_dir, term.language, term.name, str(term.number))
        makedirs(term_dir)
        
        print "Building Term:", term.name,

        projects = []
        
        for p in term.projects:
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

        terms.append(make_term_index(term, organization, output_dir))
        print "Term built!"

    print "Building Index"

    make_index(terms, organization, output_dir)

    print "Complete"

# Markup process

def build_html(markdown_file, style, organization, output_file):
    cmd = [
        "pandoc",
        "-f", "markdown_github+header_attributes+yaml_metadata_block+inline_code_attributes",
        "-t", "html5",
        "-s", 
        "--highlight-style", "pygments",
        "--section-divs",
        "--template=%s"%os.path.join(template_base, style.template), 
        markdown_file, 
        "-o", output_file,
        "--filter", scratchblocks_filter,
        "-M", "legal=%s"%organization.legal,
        "-M", "organization=%s"%organization.name,
        "-M", "logo=%s"%organization.logo,
    ]
    for stylesheet in style.stylesheets:
        cmd.extend(("-c", stylesheet,))
    for stylesheet in organization.stylesheets:
        cmd.extend(("-c", stylesheet,))

    
    working_dir = os.path.dirname(output_file)

    subprocess.check_call(cmd, cwd=working_dir)
    
def build_pdf(markdown_file, style, output_file):
    # todo: add pandoc call, but use a different template
    # than the default, or perhaps a lua writer for xetex.
    # then call xetex :/
    pass


def process_file(input_file, style, organization, output_dir):
    output = {}
    name, ext = os.path.basename(input_file).rsplit(".",1)
    if ext == "md":
        output_file = os.path.join(output_dir, "%s.html"%name)
        build_html(input_file, style, organization, output_file)
        output["html"] = output_file
    else:
        output_file = os.path.join(output_dir, os.path.basename(input_file))
        shutil.copy(input_file, output_file)
        output[ext] = output_file
    return output 

# Process files within project and resource containers

def build_project(project, organization, output_dir):
    # todo clean up this code because we keep repeating things.

    input_file = project.filename
    name, ext = os.path.basename(input_file).rsplit(".",1)

    output_files = {}

    output_files.update(process_file(input_file, lesson_style, organization, output_dir))

    notes = []

    for note in project.notes:
        notes.append(process_file(note, note_style, organization, output_dir))
    
    materials = []
    for file in project.materials:
        materials.append(copy_file(file, output_dir))

    # todo: zip materials. 

    return Project(
        filename = output_files,
        number = project.number,
        title = project.title,
        materials = materials,
        notes = notes,
    )


def build_extra(extra, organization, output_dir):
    notes = []
    for name in extra.notes:
        notes.append(process_file(name, note_style, organization, output_dir))
    materials = []
    for name in extra.materials:
        materials.append(copy_file(name, output_dir))
    return Extra(name = extra.name, notes=notes, materials=materials)

def make_term_index(manifest, organization, output_dir):
    # todo: build index of all projects, and associated notes/extras
    pass

def make_index(manifests, organization, output_dir):
    # todo: build an index of all terms
    pass

# Manifest and Project Header Parsing

def parse_manifest(filename):
    with open(filename) as fh:
        json_manifest = json.load(fh)
    
    base_dir = os.path.join(os.path.dirname(filename))

    projects = []
    for p in json_manifest['projects']:
        filename = expand_glob(base_dir, p['filename'], one_file=True)
        materials = expand_glob(base_dir, p.get('materials',[]))
        notes = expand_glob(base_dir, p.get('notes', []))
    
        project = Project(
            filename = filename,
            number = p['number'],
            title = p.get('title', None),
            materials = materials,
            notes = notes,
        )
        projects.append(project)

    extras = []
    for s in json_manifest.get('extras',()):
        notes = expand_glob(base_dir, s.get('notes', ()))
        materials = expand_glob(base_dir, s.get('materials', ()))
        
        extras.append(Extra(
            name=s['name'],
            notes=notes,
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

    title = p.title
    if header:
        title = header.get('lesson_title', p.title)
    if title is None:
        title = ""

    return Project(
        filename = p.filename,
        number = p.number,
        title = title,
        materials = p.materials,
        notes = p.notes,
    )

    
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
        if len(output) > 1:
            raise AssertionError("Bad things")
        return output[0]

    else:
        output = []
        for p in paths:
            output.extend(glob.glob(os.path.join(base_dir, p)))
        return output
    
def makedirs(path, clear=False):
    if clear and os.path.exists(path):
        shutil.rmtree(path)
    if not os.path.exists(path):
        os.makedirs(path)


def copydir(assets, output_dir):
    for asset in os.listdir(assets):
        if not asset.startswith('.'):
            src = os.path.join(assets, asset)
            dst = os.path.join(output_dir, asset)
            if os.path.exists(dst):
                if os.path.isdir(dst):
                    shutil.rmtree(dst)
                else:
                    os.path.rm(dst)
                    
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
    organization = codeclubworld
    args = sys.argv[1::]
    if len(args) < 2:
        print "usage: %s <input repository directories> <output directory>"
        sys.exit(-1)

    args = [os.path.abspath(a) for a in args]

    repositories, output_dir = args[:-1], args[-1]

    build(repositories, organization, output_dir)

    sys.exit(0)

