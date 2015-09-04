#!/usr/bin/env python
import os
import re
import os.path
import sys
import shutil
import collections
import glob
import json
import subprocess
import string
import argparse
from datetime import datetime

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import xml.etree.ElementTree as ET
try:
    import yaml
except ImportError:
    print >> sys.stderr, "You need to install pyyaml using pip or easy_install, sorry"
    sys.exit(1)

PANDOC_INSTALL_URL      = 'http://johnmacfarlane.net/pandoc/installing.html'
WKHTMLTOPDF_INSTALL_URL = 'http://wkhtmltopdf.org'

Theme    = collections.namedtuple('Theme','id name language stylesheets registration_note legal logo favicon css_variables analytics_account analytics_domain webmaster_tools_verification')
Style    = collections.namedtuple('Style', 'name html_template tex_template scripts stylesheets')
Language = collections.namedtuple('Language', 'code name rtl registration_note legal translations links resources')

def progress_print(*args):
    global verbose
    if verbose:
        for a in args:
            if type(a) is unicode:
                a = a.encode('utf-8')
            print a

def translate(self, text):
    trans = self.translations.get(text, text)
    return (text, trans)[trans is not None]

Language.translate = translate
base               = os.path.dirname(os.path.abspath(__file__))
template_base      = os.path.join(base, "assets", "templates")
theme_base         = os.path.join(base, "assets", "themes")
language_base      = os.path.join(base, "assets", "languages")
phantomjs          = os.path.join(base, "node_modules", ".bin", "phantomjs")
PANDOC_MARKDOWN    = "markdown_github-implicit_figures+header_attributes+yaml_metadata_block+inline_code_attributes+footnotes"
year               = datetime.now().year
banned_chars       = re.compile(r'[\\/?|;:!#@$%^&*<>, ]+')

index_style = Style(
    name          = 'lesson',
    html_template = "index.html",
    tex_template  = None,
    scripts       = ["/js/prism.js"],
    stylesheets   = ["/css/prism.css", "/css/master.min.css"],
)

extra_style = Style(
    name          = 'lesson',
    html_template = "extra.html",
    tex_template  = None,
    scripts       = ["/js/prism.js"],
    stylesheets   = ["/css/prism.css", "/css/master.min.css"],
)

lesson_style = Style(
    name          = 'lesson',
    html_template = "lesson.html",
    tex_template  = None,
    scripts       = ["/js/prism.js", "/js/lesson.js"],
    stylesheets   = ["/css/prism.css", "/css/master.min.css"],
)

note_style = Style(
    name          = 'lesson',
    html_template = "note.html",
    tex_template  = None,
    scripts       = ["/js/prism.js"],
    stylesheets   = ["/css/prism.css", "/css/master.min.css"],
)

# todo : real classes
Term                 = collections.namedtuple('Term', 'id manifest title warning description language number projects extras category')
Project              = collections.namedtuple('Project', 'filename pdf number level title beta materials note note_pdf embeds extras')
Extra                = collections.namedtuple('Extra', 'name materials note pdf')
Resource             = collections.namedtuple('Resource', 'format filename')
css_assets           = os.path.join(base, "assets", "css")
js_assets            = os.path.join(base, "assets", "js")
scratchblocks_filter = os.path.join(base, "lib", "pandoc_scratchblocks", "filter.py")
rasterize            = os.path.join(base, "rasterize.js")
html_assets          = [os.path.join(base, "assets", x) for x in ("fonts", "img")]

# if pandoc is installed locally, use that
pandoc               = os.path.join(base, "pandoc")
pandoc               = ("pandoc", pandoc)[os.path.exists(pandoc)]

# if zip is installed locally, use that
zip_bin              = os.path.join(base, "zip")
zip_bin              = ("zip", zip_bin)[os.path.exists(zip_bin)]

if not os.path.exists(scratchblocks_filter):
    print >> sys.stderr, "There was a problem with the pandoc scratchblocks filter.\nPerhaps you need to run: `git submodule update --init`"
    sys.exit(1)

# Markup processing
def pandoc_html(input_file, style, project, language, theme, variables, commands, root_dir, output_file):
    root  = get_path_to(root_dir, output_file)
    registration_note = language.registration_note.get(theme.id, theme.registration_note)
    legal = language.legal.get(theme.id, theme.legal)
    beta = project.beta if project is not None else False
    cmd   = [
        pandoc,
        input_file,
        "-o", output_file,
        "-t", "html5",
        "--section-divs",
        "--smart",  # smart quotes
        "--template=%s"%os.path.join(template_base, style.html_template),
        "--filter", scratchblocks_filter,
        "-M", "registration_note=%s"%registration_note,
        "-M", "legal=%s"%legal,
        "-M", "year=%s"%year,
        "-M", "beta=%s"%beta,
        "-M", "organization=%s"%theme.name,
        "-M", "logo=%s"%theme.logo,
        "-M", "favicon=%s"%theme.favicon,
        "-M", "root=%s"%root,
        "-M", "lang=%s"%language.code,
        "-M", "rtl=%s"%language.rtl,
        "-M", "theme=%s"%theme.id,
        "-M", "webmaster_tools_verification=%s"%theme.webmaster_tools_verification,
    ]

    if theme.analytics_account:
        cmd.extend([
            "-M", "analytics_account=%s"%theme.analytics_account,
            "-M", "analytics_domain=%s"%theme.analytics_domain,
        ])

    cmd.extend(commands)

    for script in style.scripts:
        cmd.extend(("-c", root + script,))

    for stylesheet in style.stylesheets:
        cmd.extend(("-c", root + stylesheet,))

    for stylesheet in theme.stylesheets:
        cmd.extend(("-c", root + stylesheet,))

    for k, v in variables.iteritems():
        cmd.extend(("-M", "%s=%s"%(k, v)))

    working_dir = os.path.dirname(output_file)

    try:
        subprocess.check_call(cmd, cwd=working_dir)
    except OSError:
        logger.error('Pandoc is required, check %s' % PANDOC_INSTALL_URL)
        sys.exit(1)

def markdown_to_html(markdown_file, breadcrumb, style, project, language, theme, root_dir, output_file):
    commands = (
        "-f", PANDOC_MARKDOWN,
    )

    variables = get_legend_translations(language)

    if breadcrumb:
        variables['breadcrumbs'] = ET.tostring(build_breadcrumb(breadcrumb, output_file), encoding='utf-8', method='html')

    pandoc_html(markdown_file, style, project, language, theme, variables, commands, root_dir, output_file)

def make_html(variables, breadcrumb, html, style, language, theme, root_dir, output_file):
    variables = dict(variables)

    if breadcrumb:
        variables['breadcrumbs'] = ET.tostring(build_breadcrumb(breadcrumb, output_file), encoding='utf-8', method='html')

    variables['body'] = ET.tostring(html, encoding='utf-8', method='html')

    commands = (
        "-f", "html",
        "-R",
    )

    input_file = '/dev/null'

    pandoc_html(input_file, style, None, language, theme, variables, commands, root_dir, output_file)

def phantomjs_pdf(input_file, output_file, root_dir, legal):
    # fetch the phantom footer
    footer_fn = os.path.join(template_base, "_phantomjs_footer.html")
    with open(footer_fn, "r") as footer_file:
        footer = footer_file.read().replace('{{ legal }}', legal)

    root = get_path_to(root_dir, output_file)
    cmd = [
        phantomjs, rasterize,
        # include pdf-specific stylesheet
        '--style', os.path.join(root, 'css', 'pdf.min.css'),
        # include pdf-specific javascript
        '--script', 'assets/js/pdf.js',
        '--footer', footer,
        '--waitFor', 'document.getElementById("legend").style.display == "block"',
        input_file, output_file, '"A4"'
    ]

    return 0 == subprocess.call(cmd)

def qtwebkit_to_pdf(input_file, output_file, root_dir, legal):
    # faff to inject some custom javascript
    print_js_fn = os.path.join(js_assets, "pdf.js")
    with open(print_js_fn, "r") as print_js_file:
        print_js = print_js_file.read()

    # massive faff to inject a custom stylesheet
    root = get_path_to(root_dir, output_file)
    with open(input_file, "r") as i:
        input_file = '%s.tmp.html' % input_file[:-5]
        with open(input_file, 'w') as o:
            for line in i:
                if '</head>' in line:
                    o.write('<link rel="stylesheet" href="%s/css/pdf.min.css">\n' % root)
                o.write(line)

    cmd = [
        "wkhtmltopdf",
        # this doesn't work properly, for various reasons.
        # "--user-style-sheet", os.path.join(root_dir, "css", "pdf.min.css"),
        "--print-media-type",
        "--run-script", print_js,
        "--footer-html", os.path.join(template_base, "_wkhtmltopdf_footer.html"),
        "--replace", "legal", legal,
        "-T", "1.2cm",
        "-B", "2.5cm",
        "-L", "0",
        "-R", "0",
        input_file,
        output_file,
    ]

    working_dir = os.path.dirname(output_file)

    try:
        result = subprocess.call(cmd, cwd=working_dir)
    except OSError:
        logger.error('wkhtmltopdf is required, check %s' % WKHTMLTOPDF_INSTALL_URL)
        sys.exit(1)
    finally:
        os.remove(input_file)

    return 0 == result

def pandoc_pdf(input_file, style, language, theme, variables, commands, output_file):
    cmd = [
        pandoc,
        input_file,
        "-o", output_file,
        "-t", "latex",
    ]

    cmd.extend(commands)

    if style.tex_template:
        cmd.append("--template=%s"%os.path.join(template_base, style.tex_template))

    for k,v in variables.iteritems():
        cmd.extend(("-M", "%s=%s"%(k,v)))

    working_dir = os.path.dirname(output_file)

    return 0 == subprocess.call(cmd, cwd=working_dir)

def markdown_to_pdf(markdown_file, style, language, theme, output_file):
    commands = (
        "-f", PANDOC_MARKDOWN,
    )

    return pandoc_pdf(markdown_file, style, language, theme, {}, commands, output_file)

def process_file(input_file, breadcrumb, style, project, language, theme, root_dir, output_dir, pdf_generator):
    output            = []
    registration_note = language.registration_note.get(theme.id, theme.registration_note)
    legal             = language.legal.get(theme.id, theme.legal)
    name, ext         = os.path.basename(input_file).rsplit(".", 1)
    generated_pdf     = None

    if ext == "md":
        # Generate HTML
        output_file = os.path.join(output_dir, "%s.html"%name)
        markdown_to_html(input_file, breadcrumb, style, project, language, theme, root_dir, output_file)
        output.append(Resource(filename = output_file, format = "html"))

        if pdf_generator is not None:
            # Set input to newly generated HTML to act as source for PDF generation
            input_file  = output_file
            output_file = os.path.join(output_dir, "%s.pdf"%name)

            # dirtiest hack of all.
            # If file appears unchanged, don't generate a pdf
            if not rebuild and output_repo is not None and output_repo.git.diff('--name-only', '--', input_file.encode('utf8')) == '':
                if output_repo.git.ls_files(output_file.encode('utf8')) != '':
                    output_repo.git.checkout('--', output_file.encode('utf8'))
                    return output, output_file

            #
            # Here are three methods of generating PDFs.
            #
            if pdf_generator == 'wkhtmltopdf':
                # Requires wkhtmltopdf - http://wkhtmltopdf.org
                success = qtwebkit_to_pdf(input_file, output_file, root_dir, legal)
                if success:
                    generated_pdf = output_file
            elif pdf_generator == 'phantomjs':
                # Requires PhantomJS - `npm install`
                success = phantomjs_pdf(input_file, output_file, root_dir, legal)
                if success:
                    generated_pdf = output_file

            # Requires Pandoc and LaTeX/MacTeX
            # success = markdown_to_pdf(input_file, style, language, theme, output_file)

    else:
        output_file = os.path.join(output_dir, os.path.basename(input_file))
        shutil.copy(input_file, output_file)
        output.append(Resource(filename = output_file, format = ext))

    return output, generated_pdf

# Process files within project and resource containers

def build_project(pdf_generator, term, project, language, theme, root_dir, output_dir, breadcrumb):
    # todo clean up this code because we keep repeating things.
    embeds = []

    for file in project.embeds:
        embeds.append(copy_file(file, output_dir))

    input_file         = project.filename
    pdf                = project.pdf
    note_pdf           = project.note_pdf
    name, ext          = os.path.basename(input_file).rsplit(".", 1)
    project_breadcrumb = breadcrumb + [(project.title, "")]
    notes              = []

    if pdf != None:
        pdf = copy_file(pdf, output_dir)
        progress_print("There is a PDF already present. Copied PDF: " + pdf)
        pdf_generator = None

    output_files, generated_pdf = process_file(input_file, project_breadcrumb, lesson_style, project, language, theme, root_dir, output_dir, pdf_generator)
    if generated_pdf is not None:
        progress_print("A PDF was generated. Generated PDF: " + generated_pdf)
        pdf = generated_pdf

    if note_pdf != None:
        note_pdf = copy_file(note_pdf, output_dir)
        progress_print("Copied Notes PDF: " + note_pdf)

    if project.note:
        notes.extend(process_file(project.note, None, note_style, project, language, theme, root_dir, output_dir, None)[0])

    extras = []

    for e in project.extras:
        extras.append(build_project_extra(pdf_generator, term, project, e, language, theme, root_dir, output_dir, breadcrumb))

    materials = None

    if project.materials:
        zipfilename = "%s_%d-%02.d_%s_%s.zip" % (term.id, term.number, project.number, project.title, language.translate("resources"))
        materials   = zip_files(os.path.dirname(input_file), project.materials, output_dir, zipfilename)

    return Project(
        filename  = output_files,
        pdf       = pdf,
        number    = project.number,
        title     = project.title,
        beta      = project.beta,
        level     = project.level,
        materials = materials,
        note      = notes,
        note_pdf  = note_pdf,
        embeds    = embeds,
        extras    = extras
    )

def build_project_extra(pdf_generator, term, project, extra, language, theme, root_dir, output_dir, term_breadcrumb):
    note       = []
    breadcrumb = term_breadcrumb + [(extra.name, '')]
    pdf        = None

    if theme.id == 'uk':
        pdf = extra.pdf

    if pdf != None:
        pdf = copy_file(pdf, output_dir)
        progress_print("Copied Extra PDF: " + pdf)

    if extra.note:
        note.extend(process_file(extra.note, breadcrumb, note_style, project, language, theme, root_dir, output_dir, None)[0])

    materials = None

    if extra.materials:
        zipfilename = "%s_%d-%02.d_%s_%s.zip" % (term.id, term.number, project.number, extra.name, language.translate("resources"))
        materials   = zip_files(os.path.dirname(project.filename), extra.materials,output_dir, zipfilename)

    return Extra(
        name      = extra.name,
        note      = note,
        materials = materials,
        pdf       = pdf,
    )

def build_extra(pdf_generator, term, extra, project, language, theme, root_dir, output_dir, term_breadcrumb):
    note       = []
    breadcrumb = term_breadcrumb + [(extra.name, '')]
    pdf        = extra.pdf

    if pdf != None:
        pdf = copy_file(pdf, output_dir)
        progress_print("Copied Extra PDF: " + pdf)

    if extra.note:
        note.extend(process_file(extra.note, breadcrumb, note_style, project, language, theme, root_dir, output_dir, None)[0])

    materials = None

    if extra.materials:
        zipfilename = "%s_%d_%s_%s.zip" % (term.id, term.number, extra.name, language.translate("resources"))
        materials   = zip_files(os.path.dirname(term.manifest), extra.materials,output_dir, zipfilename)

    return Extra(
        name      = extra.name,
        note      = note,
        materials = materials,
        pdf       = pdf,
    )

def sort_files(files):
    sort_key = {
        'html': 2,
        'pdf': 1,
    }

    return sorted(files, key=lambda x:sort_key.get(x.format,0), reverse = True)

def make_term_index(term, language, theme, root_dir, output_dir, output_file, project_breadcrumb):
    title = u"%s"%(term.title)

    index_section = ET.Element('section', {
        'class': 'index'
    })

    index_title = ET.SubElement(index_section, 'h1', {
        'class': 'index-title'
    })

    index_title.text = language.translate('Projects')

    if term.warning:
        index_warning = ET.SubElement(index_section, 'p', {
            'class': 'index-warning'
        })

        index_warning.text = term.warning

    if term.description:
        index_description = ET.SubElement(index_section, 'p', {
            'class': 'index-description'
        })

        index_description.text = term.description

    projects_list = ET.SubElement(index_section, 'ul', {
        'class': 'projects-list'
    })

    project_counter = 1

    for project in sorted(term.projects, key=lambda x:x.number):
        files  = sort_files(project.filename)
        first  = files[0]
        others = files[1:]
        url    = os.path.relpath(first.filename, output_dir)

        if project.title:
            project_title = project.title
            if project.beta:
                project_title = '(New) ' + project_title
        else:
            project_title = url

        projects_item = ET.SubElement(projects_list, 'li', {
            'class': 'projects-item'
        })

        projects_title = ET.SubElement(projects_item, 'span', {
            'class': 'projects-title'
        })

        projects_title.text = str(project_counter) + '. ' + project_title

        if project.level:
            projects_level = ET.SubElement(projects_title, 'span', {
                'class': 'projects-level'
            })

            projects_level.text = unicode(project.level)


        files_list = ET.SubElement(projects_item, 'ul', {
            'class': 'files-list'
        })

        files_item = ET.SubElement(files_list, 'li', {
            'class': 'files-item'
        })

        files_link = ET.SubElement(files_item, 'a', {
            'class': 'files-link worksheet',
            'href': url
        })

        files_link.text = language.translate('Student Project')

        if hasattr(project, 'pdf') and project.pdf != None:
            pdf_url = os.path.relpath(project.pdf, output_dir)

            separator = ET.SubElement(files_item, 'span')
            separator.text = ' ' + unichr(8212) + ' ';

            pdf_link = ET.SubElement(files_item, 'a', {
                'class': 'files-link pdf',
                'href': pdf_url
            })

            pdf_link.text = language.translate('Download PDF')

        for file in others:
            url        = os.path.relpath(file.filename, output_dir)
            files_item = ET.SubElement(files_list, 'li', {
                'class': 'files-item'
            })

            files_link = ET.SubElement(files_item, 'a', {
                'class': 'files-link alternate',
                'href': url
            })

            files_link.text = file.format

        note_pdf_url = False

        if hasattr(project, 'note_pdf') and project.note_pdf != None:
            note_pdf_url = os.path.relpath(project.note_pdf, output_dir)

        for file in sort_files(project.note):
            url        = os.path.relpath(file.filename, output_dir)
            files_item = ET.SubElement(files_list, 'li', {
                'class': 'files-item'
            })

            files_link = ET.SubElement(files_item, 'a', {
                'class': 'files-link notes',
                'href': url
            })

            files_link.text = language.translate("Notes for Club Leader")

            if file.format != 'html':
                files_link.text = "%s (%s)"%(language.translate("Notes"),file.format)

            if note_pdf_url:
                separator = ET.SubElement(files_item, 'span')
                separator.text = ' ' + unichr(8212) + ' ';

                pdf_link = ET.SubElement(files_item, 'a', {
                    'class': 'files-link pdf',
                    'href': note_pdf_url
                })

                pdf_link.text = language.translate('Download PDF')

        if project.materials:
            file       = project.materials
            url        = os.path.relpath(file.filename, output_dir)
            files_item = ET.SubElement(files_list, 'li', {
                'class': 'files-item materials'
            })

            files_link = ET.SubElement(files_item, 'a', {
                'class': 'files-link materials',
                'href': url
            })

            files_link.text = language.translate("Download Project Materials")

        if project.extras:
            extras_list_title = ET.SubElement(projects_item, 'span', {
                'class': 'projects-title'
            })

            extras_list_title.text = language.translate("Scratch Cards for this lesson");

            extras_list = ET.SubElement(projects_item, 'ul', {
                'class': 'files-list extras'
            })

            for extra in sorted(project.extras, key=lambda x:x.name):
                pdf_url = None

                if hasattr(extra, 'pdf') and extra.pdf != None:
                    pdf_url  = os.path.relpath(extra.pdf, output_dir)

                for file in sort_files(extra.note):
                    url        = os.path.relpath(file.filename, output_dir)
                    files_item = ET.SubElement(extras_list, 'li', {
                        'class': 'files-item'
                    })

                    files_link = ET.SubElement(files_item, 'a', {
                        'class': 'files-link extra',
                        'href': url
                    })

                    files_link.text = extra.name

                    if file.format != 'html':
                        files_link.text = "%s (%s)"%(extra.name,file.format)

                    if pdf_url != None:
                        separator = ET.SubElement(files_item, 'span')
                        separator.text = ' ' + unichr(8212) + ' ';

                        pdf_link = ET.SubElement(files_item, 'a', {
                            'class': 'files-link pdf',
                            'href': pdf_url
                        })

                        pdf_link.text = language.translate('Download PDF')

        project_counter += 1

    if term.extras:
        index_title = ET.SubElement(index_section, 'h1', {
            'class': 'index-title'
        })

        index_title.text = language.translate('Extras')

        index_list = ET.SubElement(index_section, 'ul', {
            'class': 'index-list'
        })

        for extra in term.extras:
            index_item = ET.SubElement(index_list, 'li', {
                'class': 'index-item'
            })

            if extra.note:
                # todo: handle multiple formats
                file       = sort_files(extra.note)[0]
                url        = os.path.relpath(file.filename, output_dir)
                index_link = ET.SubElement(index_item, 'a', {
                    'class': 'index-link note',
                    'href': url
                })

                index_link.text = extra.name

            if extra.materials:
                filename = extra.materials
                url      = os.path.relpath(filename, output_dir)

                index_link = ET.SubElement(index_item, 'a', {
                    'class': 'index-link material',
                    'href': url
                })

                index_link.text = filename

    make_html({'title':title}, project_breadcrumb, index_section, index_style, language, theme, root_dir, output_file)

    return output_file, term

def make_lang_index(language, terms, theme, root_dir, output_dir, output_file, lang_breadcrumb):
    index_section = ET.Element('section', {
        'class': 'index'
    })

    index_list = ET.SubElement(index_section, 'ul', {
        'class': 'index-list'
    })

    previous_category = None

    for term_index, term in sorted(terms, key=lambda x:x[1].number):

        category = term.category or (previous_category or "Terms")

        if category != previous_category:

            index_title = ET.SubElement(index_list, 'h1', {
              'class': 'index-title'
            })

            index_title.text = language.translate(category)

            index_description_to_translate = category + ".description"
            index_description_text = language.translate(index_description_to_translate)
            if index_description_text != index_description_to_translate:
                index_description = ET.SubElement(index_list, 'span')
                index_description.text = index_description_text

            previous_category = category


        url = os.path.relpath(term_index, output_dir)

        index_item = ET.SubElement(index_list, 'li', {
            'class': 'index-item'
        })

        index_link = ET.SubElement(index_item, 'a', {
            'class': 'index-link',
            'href': url
        })

        index_link.text = term.title or url

    if language.links:
        for title, links in language.links.iteritems():
            index_title = ET.SubElement(index_section, 'h1', {
                'class': 'index-title'
            })

            index_title.text = title

            index_list = ET.SubElement(index_section, 'ul', {
                'class': 'index-list'
            })

            for link in links:
                index_item = ET.SubElement(index_list, 'li', {
                    'class': 'index-item'
                })

                index_link = ET.SubElement(index_item, 'a', {
                    'class': 'index-link',
                    'href': link['url']
                })

                index_link.text = link['name']

    if language.resources:
        resources = language.resources

        if resources:
            title      = resources.get('title',      None)
            disclaimer = resources.get('disclaimer', None)
            links      = resources.get('links',      None)

            if title:
                index_title = ET.SubElement(index_section, 'h1', {
                    'class': 'index-title'
                })

                index_title.text = title

            if disclaimer:
                index_warning = ET.SubElement(index_section, 'p', {
                    'class': 'index-warning'
                })

                index_warning.text = disclaimer

            if links:
                index_list = ET.SubElement(index_section, 'ul', {
                    'class': 'index-list'
                })

                for link in links:
                    index_item = ET.SubElement(index_list, 'li', {
                        'class': 'index-item'
                    })

                    index_link = ET.SubElement(index_item, 'a', {
                        'class': 'index-link',
                        'href': link['url']
                    })

                    index_link.text = link['name']

    make_html({
        'title': language.translate("Terms &amp; Resources")
    }, lang_breadcrumb, index_section, index_style, language, theme, root_dir, output_file)

    return output_file

def make_index(languages, language, theme, root_dir, output_file):
    title = theme.name
    index_section = ET.Element('section', {
        'class': 'index'
    })

    index_title = ET.SubElement(index_section, 'h1', {
        'class': 'index-title'
    })

    index_title.text = language.translate("Languages")

    index_list = ET.SubElement(index_section, 'ul', {
        'class': 'index-list'
    })

    for lang, filename in languages:
        url = os.path.relpath(filename, root_dir)

        index_item = ET.SubElement(index_list, 'li', {
            'class': 'index-item'
        })

        index_link = ET.SubElement(index_item, 'a', {
            'class': 'index-link',
            'href': url
        })

        index_link.text = lang.name

    make_html({'title':title}, None, index_section, index_style, language, theme, root_dir, output_file)

def build_breadcrumb(breadcrumb, output_file):
    output_dir = os.path.dirname(output_file)

    breadcrumbs_list = ET.Element('ul', {
        'class': 'breadcrumbs-list'
    })

    for name, path in breadcrumb[:-1]:
        url = os.path.relpath(path, output_dir)

        breadcrumbs_item = ET.SubElement(breadcrumbs_list, 'li', {
            'class': 'breadcrumbs-item'
        })

        breadcrumbs_link = ET.SubElement(breadcrumbs_item, 'a', {
            'class': 'breadcrumbs-link',
            'href': url
        })

        breadcrumbs_link.text = name

    breadcrumbs_item = ET.SubElement(breadcrumbs_list, 'li', {
        'class': 'breadcrumbs-item current'
    })

    breadcrumbs_item.text = breadcrumb[-1][0]

    return breadcrumbs_list

def build(pdf_generator, lesson_dirs, region, output_dir, v=False, gr=None, rb=False):
    global verbose, output_repo, rebuild
    verbose       = v
    output_repo   = gr
    rebuild       = rb
    lessons       = [os.path.abspath(a) for a in lesson_dirs]
    theme         = themes[region] if region != 'css' else 'css'
    all_languages = load_languages(language_base)
    output_dir    = os.path.abspath(output_dir)

    progress_print("Searching for manifests...")

    termlangs        = {}
    breadcrumbs      = []
    sorted_languages = []

    for m in find_files(lessons, ".manifest"):
        progress_print("Found Manifest:", m)

        try:
            term = parse_manifest(m, theme)

            if term.language not in termlangs:
                termlangs[term.language] = []

            termlangs[term.language].append(term)
        except StandardError as e:
            import traceback

            traceback.print_exc()

            progress_print("Failed", e.message)

    progress_print("Copying assets...")

    copydir(html_assets, output_dir)

    css_dir = os.path.join(output_dir, "css")
    js_dir  = os.path.join(output_dir, "js")

    makedirs(css_dir)
    makedirs(js_dir)

    make_assets(css_assets, theme, css_dir)
    make_assets(js_assets,  theme, js_dir)

    # don't do any of the following if we're simply updating the CSS
    if theme != 'css':
        languages       = {}
        project_count   = {}
        root_index_file = os.path.join(output_dir, "index.html")

        for language_code, terms in termlangs.iteritems():
            if language_code not in all_languages:
                all_languages[language_code] = Language(
                    code              = language_code,
                    name              = language_code,
                    registration_note = {},
                    legal             = {},
                    translations      = {}
                )

            language = all_languages[language_code]

            progress_print("Language", language.name)

            root_breadcrumb = [(language.translate('Languages'), root_index_file)]
            out_terms       = []
            count           = 0;
            lang_dir        = os.path.join(output_dir, language.code)
            lang_index_file = os.path.join(lang_dir, "index.html")
            lang_breadcrumb = root_breadcrumb + [(language.name, lang_index_file)]

            for term in terms:
                term_dir = os.path.join(lang_dir, "%.02d_%s"%(term.number, term.id))

                makedirs(term_dir)

                progress_print("Building Term:", term.title)

                term_index_file = os.path.join(term_dir, "index.html")
                term_breadcrumb = lang_breadcrumb + [(term.title, term_index_file)]
                projects        = []

                for p in term.projects:
                    count += 1
                    project = parse_project_meta(p, theme)

                    progress_print("Building Project: " + project.title)
                    progress_print(project)
                    project_dir = os.path.join(term_dir, "%.02d"%(project.number))

                    makedirs(project_dir)

                    built_project = build_project(pdf_generator, term, project, language, theme, output_dir, project_dir, term_breadcrumb)

                    projects.append(built_project)

                extras = []

                for r in term.extras:
                    progress_print("Building Extra:", r.name)
                    extras.append(build_extra(pdf_generator, term, r, project, language, theme, output_dir, term_dir, term_breadcrumb))

                term = Term(
                    id          = term.id,
                    manifest    = term.manifest,
                    number      = term.number,
                    language    = term.language,
                    title       = term.title,
                    warning     = term.warning,
                    description = term.description,
                    projects    = projects,
                    extras      = extras,
                    category    = term.category
                )

                out_terms.append(make_term_index(term, language, theme, output_dir, term_dir, term_index_file, term_breadcrumb))

                progress_print("Term built!")

            progress_print("Building", language.name, "index")

            languages[language_code] = make_lang_index(language, out_terms, theme, output_dir, lang_dir, lang_index_file, lang_breadcrumb)
            project_count[language_code] = count

        progress_print("Building", theme.name, "index")

        sorted_languages = []

        for lang in sorted(project_count.keys(), key = lambda x:project_count[x], reverse=True):
            sorted_languages.append((all_languages[lang], languages[lang]))

        make_index(sorted_languages,all_languages[theme.language], theme, output_dir, root_index_file)

    progress_print("Complete")

def parse_manifest(filename, theme):
    with open(filename) as fh:
        json_manifest = json.load(fh)

    base_dir = os.path.join(os.path.dirname(filename)).decode('utf8')
    projects = []

    for p in json_manifest['projects']:
        project = parse_project_manifest(p, base_dir, theme)
        projects.append(project)

    extras = parse_extras(json_manifest.get('extras',()), base_dir)

    m = Term(
        id          = json_manifest['id'],
        title       = json_manifest['title'],
        manifest    = filename,
        warning     = json_manifest.get('warning', None),
        description = json_manifest['description'],
        language    = json_manifest['language'],
        number      = int(json_manifest['number']),
        projects    = projects,
        extras      = extras,
        category    = json_manifest.get('category', None)
    )

    return m

def parse_project_manifest(p, base_dir, theme):
    filename  = expand_glob(base_dir, p['filename'],     one_file = True)
    materials = expand_glob(base_dir, p.get('materials', []))
    embeds    = expand_glob(base_dir, p.get('embeds',    []))
    extras    = p.get('extras', [])
    pdf       = None
    note      = None
    note_pdf  = None

    progress_print("Preparing to copy PDFs")

    if 'pdf'      in p: pdf      = expand_glob(base_dir, p['pdf'],      one_file = True)
    if 'note_pdf' in p: note_pdf = expand_glob(base_dir, p['note_pdf'], one_file = True)
    if 'note' in p: note = expand_glob(base_dir, p['note'], one_file = True)

    return Project(
        filename  = filename,
        pdf       = pdf,
        number    = p['number'],
        title     = p.get('title', None),
        beta      = p.get('beta', False),
        level     = p.get('level', None),
        materials = materials,
        note      = note,
        note_pdf  = note_pdf,
        embeds    = embeds,
        extras    = parse_extras(extras, base_dir)
    )

def parse_extras(extras_raw, base_dir):
    extras = []

    for s in extras_raw:
        note = None
        pdf  = None

        if 'note' in s:
            note = expand_glob(base_dir, s['note'], one_file = True)

        if 'pdf' in s:
            pdf = expand_glob(base_dir, s['pdf'], one_file = True)

        materials = expand_glob(base_dir, s.get('materials', ()))

        extras.append(Extra(
            name      = s['name'],
            note      = note,
            materials = materials,
            pdf       = pdf,
        ))

    return extras

def load_languages(dir):
    languages = {}

    for file in expand_glob(dir,"*.language"):
        language                 = parse_language(file)
        languages[language.code] = language

    return languages

def parse_language(filename):
    with open(filename) as fh:
        obj = json.load(fh)

    return Language(
        code              = obj['code'],
        name              = obj['name'],
        rtl               = obj.get('rtl', False),
        registration_note = obj['registration_note'],
        legal             = obj['legal'],
        translations      = obj['translations'],
        links             = obj.get('links', {}),
        resources         = obj.get('resources', None)
    )

def load_themes(dir):
    themes = {}

    for file in expand_glob(dir,"*.theme"):
        theme            = parse_theme(file)
        themes[theme.id] = theme

    return themes

def parse_theme(filename):
    with open(filename) as fh:
        obj = json.load(fh)

    return Theme(
        id                           = obj['id'],
        name                         = obj['name'],
        language                     = obj['language'],
        stylesheets                  = obj['stylesheets'],
        registration_note            = obj['registration_note'],
        legal                        = obj['legal'],
        logo                         = obj['logo'],
        favicon                      = obj['favicon'],
        analytics_account            = obj.get('analytics_account'),
        analytics_domain             = obj.get('analytics_domain'),
        webmaster_tools_verification = obj.get('webmaster_tools_verification'),
        css_variables                = obj['css_variables']
    )

def parse_project_meta(p, theme):
    if not p.filename.endswith('md'):
        return p

    with open(p.filename) as fh:
        in_header    = False
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
        number   = header.get('number', p.number)
        title    = header.get('title', p.title)
        #beta     = header.get('beta', p.beta)
        beta     = False
        level    = header.get('level', p.level)
        raw_note = header.get('note', None)
        pdf      = None
        note_pdf = None

        pdf  = p.pdf
        note_pdf = p.note_pdf

        if raw_note:
            base_dir = os.path.dirname(p.filename)
            note     = expand_glob(base_dir, raw_note, one_file=True)
        else:
            note = p.note

        raw_materials = header.get('materials', ())

        if raw_materials:
            base_dir  = os.path.dirname(p.filename)
            materials = expand_glob(base_dir, raw_materials)

            materials.extend(p.materials)
        else:
            materials = p.materials

        raw_embeds = header.get('embeds', ())

        if raw_embeds:
            base_dir = os.path.dirname(p.filename)
            embeds   = expand_glob(base_dir, raw_embeds)

            embeds.extend(p.embeds)
        else:
            embeds = p.embeds

        return Project(
            filename  = p.filename,
            pdf       = pdf,
            number    = number,
            title     = title,
            beta      = beta,
            level     = level,
            materials = materials,
            note      = note,
            note_pdf  = note_pdf,
            embeds    = embeds,
            extras    = p.extras,
        )

    return p

def make_assets(input_dir, theme, output_dir):
    for asset in os.listdir(input_dir):
        if not asset.startswith('.'):
            src = os.path.join(input_dir, asset)
            dst = os.path.join(output_dir, asset)

            if os.path.exists(dst):
                if os.path.isdir(dst):
                    shutil.rmtree(dst)
                    makedirs(dst)
                else:
                    os.remove(dst)

            if os.path.isdir(src):
                make_assets(src, theme, dst)
            else:
                shutil.copy(src, output_dir)

# File and directory handling

def get_path_to(root_dir, output_file):
    rel  = os.path.relpath(output_file, root_dir)
    dirs = os.path.dirname(rel)
    path = "."

    if dirs:
        subdirs = len(dirs.split("/"))
        path    = "/".join([".."] * subdirs)

    return path

def get_legend_translations(language):
    legend = {
        'activity':      'Activity Checklist',
        'activity_desc': 'Follow these <span class="check_text upper">instructions</span> one by one',
        'test':          'Test your Project',
        'test_desc':     'Click on the green flag to <span class="flag_text upper">test</span> your code',
        'save':          'Save your Project',
        'save_desc':     'Make sure to <span class="save_text upper">save</span> your work now',
    }
    return {'leg_%s' % k: language.translate(v) for k, v in legend.items()}

def find_files(dir, extension):
    manifests = []
    for d in dir:
        for root, dirs, files in os.walk(d, followlinks=True):
            for name in files:
                if name.endswith(extension):
                    manifests.append(os.path.join(root, name))
    return manifests

def expand_glob(base_dir, paths, one_file=False):
    if one_file:
        output = glob.glob(os.path.join(base_dir, paths))

        if len(output) != 1:
            raise AssertionError("Looked for one file matching '%s', found: %r"%(os.path.join(base_dir,paths), output))

        return output[0]

    output = []

    if not hasattr(paths, '__iter__'):
        paths = (paths,)

    for p in paths:
        output.extend(glob.glob(os.path.join(base_dir, p)))

    return output

def makedirs(path, clear = False):
    if clear and os.path.exists(path):
        shutil.rmtree(path)

    if not os.path.exists(path):
        os.makedirs(path)

def safe_filename(filename):
    return banned_chars.sub("_", filename)

def zip_files(relative_dir, source_files, output_dir, output_file):
    if source_files:
        output_file = os.path.join(output_dir, safe_filename(output_file))

        cmd = [zip_bin]

        # dirty hack
        if output_repo is not None and output_repo.git.ls_files(output_file.encode('utf8')) != '':
            output_repo.git.checkout('--', output_file.encode('utf8'))

        if os.path.exists(output_file):
            # cmd.append('-u')
            return Resource(format="zip", filename=output_file)

        cmd.append(output_file)

        for file in source_files:
            cmd.append(os.path.relpath(file, relative_dir))

        ret = subprocess.call(cmd, cwd = relative_dir)

        if ret != 0 and ret != 12: # 12 means zip did nothing
            raise StandardError('zip failure %d'%ret)

        return Resource(format="zip", filename=output_file)

    return None

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
    name, ext   = os.path.basename(input_file).rsplit(".",1)
    output_file = os.path.join(output_dir, os.path.basename(input_file))

    shutil.copy(input_file, output_file)

    return output_file

def check_requirements():
    pass

themes   = load_themes(theme_base)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', choices=['wkhtmltopdf', 'phantomjs'], default=None, dest="pdf_generator")
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('region', choices=themes.keys()+['css'])
    parser.add_argument('lesson_dirs', nargs="+")
    parser.add_argument('output_dir')
    p = parser.parse_args()

    build(p.pdf_generator, p.lesson_dirs, p.region, p.output_dir, p.verbose)

    sys.exit()
