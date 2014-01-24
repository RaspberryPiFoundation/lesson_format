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
scratchblocks_filter = os.path.join(base, "pandoc_scratchblocks/filter.py")

Term = collections.namedtuple('Term', 'name language term projects resources')
Project = collections.namedtuple('Project', 'filename number title materials notes')
Resource = collections.namedtuple('Resource', 'name files')

# Utility
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
    
def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


def copy(assets, output_dir):
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
# Build process

# Manifest and Project Header Parsing

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

    resources = []
    for s in json_manifest['resources']:
        files = expand_glob(base_dir, s.get('files', []))
        
        resources.append(Resource(
            name=s['name'],
            files=files,
        ))

    m = Term(
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


# Turning source materials into Final product

def build_term_dir(manifest, output_dir):
    dir = os.path.join(output_dir, manifest.language, manifest.name)
    makedirs(dir)
    return dir


def build_project(project, output_dir):
    input_file = project.filename
    output_dir = os.path.join(output_dir,"%.02d"%project.number)
    name, ext = os.path.basename(input_file).rsplit(".",1)

    output_files = {}

    if ext == "md":
        output_file = os.path.join(output_dir, "%s.html"%name)
        build_html(input_file, output_file)
        output_files["html"] = output_file
    else:
        output_file = os.path.join(output_dir, os.path.basename(input_file))
        shutil.copy(input_file, output_file)
        output_files[ext] = output_file

    notes = []

    for n in project.notes:
        name, ext = os.path.basename(n).rsplit(".",1)
        if ext == "md":
            output_file = os.path.join(output_dir, "%s.html"%name)
            build_html(n, output_file)
        else:
            output_file = os.path.join(output_dir, os.path.basename(n))
            shutil.copy(n, output_file)
        notes.append(output_file)
    
    materials = []
    for file in project.materials:
        output_file = os.path.join(output_dir, os.path.basename(file))
        shutil.copy(file, output_file)
        materials.append(output_file)

    # todo: zip materials. 

    return Project(
        filename = output_files,
        number = project.number,
        title = project.title,
        materials = materials,
        notes = notes,
    )

def build_resource(resource, output_dir):
    files = []
    for n in resource.files:
        name, ext = os.path.basename(n).rsplit(".",1)
        if ext == "md":
            output_file = os.path.join(output_dir, "%s.html"%name)
            build_html(n, output_file)
        else:
            output_file = os.path.join(output_dir, os.path.basename(n))
            shutil.copy(n, output_file)
        files.append(output_file)
    return Resource(name = resource.name, files=files)

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
        "--filter", scratchblocks_filter,
    ]
    
    working_dir = os.path.dirname(output_file)
    makedirs(working_dir)

    subprocess.check_call(cmd, cwd=working_dir)
    
    

def make_term_index(manifest, output_dir):
    # todo: build index of all projects, and associated notes/resources
    pass

def make_index(manifests, output_dir):
    # todo: build an index of all terms
    pass


if __name__ == '__main__':
    args = sys.argv[1::]
    if len(args) < 2:
        print "usage: %s <input repository directories> <output directory>"
        sys.exit(-1)

    args = [os.path.abspath(a) for a in args]

    repositories, output_dir = args[:-1], args[-1]

    print "Searching for manifests .."

    manifests = []
    
    for m in find_manifests(repositories):
        print "Found Manifest:", m
        try:
            manifests.append(parse_manifest(m))
        except StandardError:
            print "Failed"

    terms = []
    for term in manifests:
        term_dir = build_term_dir(term, output_dir)
        
        print "Building Term:", term.name,
        projects = []
        for p in term.projects:
            project = parse_project(p)
            print "Building Project:", project.title, project.filename

            built_project = build_project(project, term_dir)
            
            projects.append(built_project)

        resources = []
        for r in term.resources:
            print "Building Resource:", r.name
            resources.append(build_resource(r, output_dir))

        term = Term(
            name = term.name, term = term.term, language = term.language,
            projects = projects,
            resources = resources,
        )

        terms.append(make_term_index(term, output_dir))
        print "Term built!"

    print "Building Index"

    make_index(terms, output_dir)

    print "Copying assets"

    copy(html_assets, output_dir), 

    print "Complete"

    sys.exit(0)
