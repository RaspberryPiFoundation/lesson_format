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

pandoc_markdown="markdown_github+header_attributes+yaml_metadata_block+inline_code_attributes"
base = os.path.dirname(os.path.abspath(__file__))
html_template = os.path.join(base, "templates/template.html")
html_assets = os.path.join(base, "assets")

Term = collections.namedtuple('Term', 'filename name language term projects resources')
Project = collections.namedtuple('Project', 'filename number title materials notes')
Resources = collections.namedtuple('Resources', 'name files')

# Utility
def expand_glob(base_dir, paths):
    output = []
    for p in paths:
        output.extend(glob.glob(os.path.join(base_dir, p)))
    return output
    
def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Build process

def find_manifests(dir):
    manifests = []
    def visit(m, dirname, names):
        for n in names:
            if n.endswith(".manifest"):
                m.append(os.path.join(dirname, n))
    for d in dir:
        os.path.walk(d, visit, manifests)
    
        
    return manifests

def parse_manifest(filename):
    with open(filename) as fh:
        json_manifest = json.load(fh)
    
    base_dir = os.path.join(os.path.dirname(filename))

    projects = []
    for p in json_manifest['projects']:
        filename = os.path.join(base_dir, p['filename'])
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

    resources = []
    for s in json_manifest['resources']:
        files = expand_glob(base_dir, s.get('files', []))
        
        resources.append(Resources(
            name=s['name'],
            files=files,
        ))

    m = Term(
        filename = filename, 
        name = json_manifest['name'],
        language = json_manifest['language'],
        term = int(json_manifest['term']),
        projects = projects,
        resources = resources,
    )

    return m

def parse_project(p):
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

    title = header.get('lesson_title', p.title)
    return Project(
        filename = p.filename,
        number = p.number,
        title = title,
        materials = p.materials,
        notes = p.notes,
    )



def build_term_dir(manifest, output_dir):
    dir = os.path.join(output_dir, manifest.language, manifest.name)
    makedirs(dir)
    return dir


def build_project(project, output_dir):
    input_file = project.filename
    output_dir = os.path.join(output_dir,"%.02d"%project.number)

    if input_file.endswith('.md'):
        name, ext = os.path.basename(input_file).rsplit(".",1)
        output_file = os.path.join(output_dir, "%s.html"%name)
        build_html(input_file, output_file)
    else:
        output_file = os.path.join(output_dir, os.path.basename(input_file))
        shutil.copy(input_file, output_file)

    # todo: zip materials
    # todo: convert any notes

    return Project(
        filename = output_file,
        number = project.number,
        title = project.title,
        materials = project.materials,
        notes = project.notes,
    )

def build_html(markdown_file, output_file):
    cmd = [
        "pandoc",
        "-t", "html5",
        "-s", 
        "--highlight-style", "pygments",
        "--section-divs",
        "--template=%s"%html_template, 
        markdown_file, 
        "-o", output_file,
    ]
    
    working_dir = os.path.dirname(output_file)
    makedirs(output_file)

    # todo: add scratch filter, optional template

    subprocess.check_call(cmd, cwd=working_dir)
    
    

def build_term(manifest, projects, output_dir):
    pass

def make_index(manifest, output_dir):
    pass


if __name__ == '__main__':
    print "Cloning repository"

    args = sys.argv[1::]
    if len(args) < 2:
        print "usage: %s <input repository directories> <output directory>"
        sys.exit(-1)

    args = [os.path.abspath(a) for a in args]

    repositories, output_dir = args[:-1], args[-1]

    print "Searching for manifests"

    manifests = []
    
    for m in find_manifests(repositories):
        print m
        manifests.append(parse_manifest(m))

    print "Building Terms:"

    terms = {}
    for term in manifests:
        term_dir = build_term_dir(term, output_dir)
        
        print term.name, " -> ", term_dir
        projects = []
        for p in term.projects:
            project = parse_project(p)
            print term.name, project.title, project.filename

            built_project = build_project(project, term_dir)
            
            projects.append(built_project)

        terms[term.term] = build_term(term, projects, output_dir)


    print "Building Index"

    make_index(terms, output_dir)

    print "Copying assets"

    for asset in os.listdir(html_assets):
        if not asset.startswith('.'):
            src = os.path.join(html_assets, asset)
            dst = os.path.join(output_dir, asset)
            if os.path.isdir(src):
                shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy(src, dst)

    sys.exit(0)
