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
    sys.exit(-10)

PANDOC_INSTALL_URL      = 'http://johnmacfarlane.net/pandoc/installing.html'
WKHTMLTOPDF_INSTALL_URL = 'http://wkhtmltopdf.org'

Theme    = collections.namedtuple('Theme','id name language stylesheets legal logo css_variables analytics_account analytics_domain webmaster_tools_verification')
Style    = collections.namedtuple('Style', 'name html_template tex_template scripts stylesheets')
Language = collections.namedtuple('Language', 'code name legal translations links')

def progress_print(*args):
    if progress:
        for a in args:
            print a

def translate(self, text):
    return self.translations.get(text, text)

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
    scripts       = ["/js/prism.js"],
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
Term                 = collections.namedtuple('Term', 'id manifest title description language number projects extras')
Project              = collections.namedtuple('Project', 'filename pdf number level title materials note note_pdf embeds extras')
Extra                = collections.namedtuple('Extra', 'name materials note pdf')
Resource             = collections.namedtuple('Resource', 'format filename')
css_assets           = os.path.join(base, "assets", "css")
js_assets            = os.path.join(base, "assets", "js")
scratchblocks_filter = os.path.join(base, "lib", "pandoc_scratchblocks", "filter.py")
rasterize            = os.path.join(base, "rasterize.js")
html_assets          = [os.path.join(base, "assets", x) for x in ("fonts", "img")]

# Markup processing
def pandoc_html(input_file, style, language, theme, variables, commands, root_dir, output_file):
    root  = get_path_to(root_dir, output_file)
    legal = language.legal.get(theme.id, theme.legal)
    cmd   = [
        "pandoc",
        input_file,
        "-o", output_file,
        "-t", "html5",
        "--section-divs",
        "-s",  # smart quotes
        "--highlight-style", "pygments",
        "--template=%s"%os.path.join(template_base, style.html_template),
        "--filter", scratchblocks_filter,
        "-M", "legal=%s"%legal,
        "-M", "year=%s"%year,
        "-M", "organization=%s"%theme.name,
        "-M", "logo=%s"%theme.logo,
        "-M", "root=%s"%root,
        "-M", "lang=%s"%language.code,
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
        exit()

def markdown_to_html(markdown_file, breadcrumb, style, language, theme, root_dir, output_file):
    commands = (
        "-f", PANDOC_MARKDOWN,
    )

    variables = {}

    if breadcrumb:
        variables['breadcrumbs'] = ET.tostring(build_breadcrumb(breadcrumb, output_file), encoding='utf-8', method='html')

    pandoc_html(markdown_file, style, language, theme, variables, commands, root_dir, output_file)

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

    pandoc_html(input_file, style, language, theme, variables, commands, root_dir, output_file)

def phantomjs_pdf(input_file, output_file):
    cmd = [phantomjs, rasterize, input_file, output_file, '"A4"']

    return 0 == subprocess.call(cmd)

def qtwebkit_to_pdf(input_file, output_file, root_dir):
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
                    o.write('<link rel="stylesheet" href="%s/css/wkhtmltopdf.min.css">\n' % root)
                o.write(line)

    cmd = [
        "wkhtmltopdf",
        # this doesn't work properly, for various reasons.
        # "--user-style-sheet", os.path.join(root_dir, "css", "wkhtmltopdf.min.css"),
        "--run-script", print_js,
        "--footer-html", os.path.join(template_base, "_lesson_footer.html"),
        "-T", "1.2cm",
        "-B", "2.5cm",
        "-L", "0",
        "-R", "0",
        input_file,
        output_file,
    ]

    working_dir = os.path.dirname(output_file)

    try:
        result = subprocess.check_call(cmd, cwd=working_dir)
    except OSError:
        logger.error('wkhtmltopdf is required, check %s' % WKHTMLTOPDF_INSTALL_URL)
        exit()
    finally:
        os.remove(input_file)

    return 0 == result

def pandoc_pdf(input_file, style, language, theme, variables, commands, output_file):
    cmd = [
        "pandoc",
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

def process_file(input_file, breadcrumb, style, language, theme, root_dir, output_dir, generate_pdf):
    output        = []
    name, ext     = os.path.basename(input_file).rsplit(".", 1)
    pdf_generated = False

    if ext == "md":
        # Generate HTML
        output_file = os.path.join(output_dir, "%s.html"%name)
        markdown_to_html(input_file, breadcrumb, style, language, theme, root_dir, output_file)
        output.append(Resource(filename = output_file, format = "html"))

        if generate_pdf and pdf_generator is not None:
            # Set input to newly generated HTML to act as source for PDF generation
            input_file  = output_file
            output_file = os.path.join(output_dir, "%s.pdf"%name)

            #
            # Here are three methods of generating PDFs. None of them support
            # webfonts. Uncomment only one at a time to test them
            #
            if pdf_generator == 'wkhtmltopdf':
                # Requires wkhtmltopdf - http://wkhtmltopdf.org
                pdf_generated = qtwebkit_to_pdf(input_file, output_file, root_dir)
            elif pdf_generator == 'phantomjs':
                # Requires PhantomJS - `npm install`
                pdf_generated = phantomjs_pdf(input_file, output_file)

            # Requires Pandoc and LaTeX/MacTeX
            # pdf_generated = markdown_to_pdf(input_file, style, language, theme, output_file)

            if (pdf_generated):
                output.append(Resource(filename = output_file, format = "pdf"))
    else:
        output_file = os.path.join(output_dir, os.path.basename(input_file))
        shutil.copy(input_file, output_file)
        output.append(Resource(filename = output_file, format = ext))

    return output

# Process files within project and resource containers

def build_project(rebuild, term, project, language, theme, root_dir, output_dir, breadcrumb):
    # todo clean up this code because we keep repeating things.
    embeds = []

    for file in project.embeds:
        embeds.append(copy_file(file, output_dir))

    input_file         = project.filename
    pdf                = project.pdf
    note_pdf           = project.note_pdf
    name, ext          = os.path.basename(input_file).rsplit(".", 1)
    project_breadcrumb = breadcrumb + [(project.title, "")]
    output_files       = process_file(input_file, project_breadcrumb, lesson_style, language, theme, root_dir, output_dir, pdf is None)
    notes              = []

    if pdf != None:
        pdf = copy_file(pdf, output_dir)
        progress_print("Copied PDF: " + pdf)

    if note_pdf != None:
        note_pdf = copy_file(note_pdf, output_dir)
        progress_print("Copied Notes PDF: " + note_pdf)

    if project.note:
        notes.extend(process_file(project.note, None, note_style, language, theme, root_dir, output_dir, note_pdf is None))

    extras = []

    for e in project.extras:
        extras.append(build_project_extra(rebuild, term, project, e, language, theme, root_dir, output_dir, breadcrumb))

    materials = None

    if project.materials:
        zipfilename = "%s_%d-%02.d_%s_%s.zip" % (term.id, term.number, project.number, project.title, language.translate("resources"))
        materials   = zip_files(os.path.dirname(input_file), project.materials, output_dir, zipfilename, rebuild)

    return Project(
        filename  = output_files,
        pdf       = pdf,
        number    = project.number,
        title     = project.title,
        level     = project.level,
        materials = materials,
        note      = notes,
        note_pdf  = note_pdf,
        embeds    = embeds,
        extras    = extras
    )

def build_project_extra(rebuild, term, project, extra, language, theme, root_dir, output_dir, term_breadcrumb):
    note       = []
    breadcrumb = term_breadcrumb + [(extra.name, '')]
    pdf        = None

    if theme.id == 'uk':
        pdf = extra.pdf

    if pdf != None:
        pdf = copy_file(pdf, output_dir)
        progress_print("Copied Extra PDF: " + pdf)

    if extra.note:
        note.extend(process_file(extra.note, breadcrumb, note_style, language, theme, root_dir, output_dir, pdf is None))

    materials = None

    if extra.materials:
        zipfilename = "%s_%d-%02.d_%s_%s.zip" % (term.id, term.number, project.number, extra.name, language.translate("resources"))
        materials   = zip_files(os.path.dirname(project.filename), extra.materials,output_dir, zipfilename, rebuild)

    return Extra(
        name      = extra.name,
        note      = note,
        materials = materials,
        pdf       = pdf,
    )

def build_extra(rebuild, term, extra, language, theme, root_dir, output_dir, term_breadcrumb):
    note       = []
    breadcrumb = term_breadcrumb + [(extra.name, '')]
    pdf        = extra.pdf

    if pdf != None:
        pdf = copy_file(pdf, output_dir)
        progress_print("Copied Extra PDF: " + pdf)

    if extra.note:
        note.extend(process_file(extra.note, breadcrumb, note_style, language, theme, root_dir, output_dir, pdf is None))

    materials = None

    if extra.materials:
        zipfilename = "%s_%d_%s_%s.zip" % (term.id, term.number, extra.name, language.translate("resources"))
        materials   = zip_files(os.path.dirname(term.manifest), extra.materials,output_dir, zipfilename, rebuild)

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

        projects_item = ET.SubElement(projects_list, 'li', {
            'class': 'projects-item'
        })

        projects_title = ET.SubElement(projects_item, 'span', {
            'class': 'projects-title'
        })

        projects_title.text = str(project_counter) + '. ' + (project.title or url)

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

            if file.format == 'pdf':
                files_link.text = (project.title or url) + ' (pdf)'

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

    index_title = ET.SubElement(index_section, 'h1', {
        'class': 'index-title'
    })

    index_title.text = language.translate("Terms")

    index_list = ET.SubElement(index_section, 'ul', {
        'class': 'index-list'
    })

    for term_index, term in sorted(terms, key=lambda x:x[1].number):
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

    make_html({'title':u"%s Terms &amp; Resources"%(language.name)}, lang_breadcrumb, index_section, index_style, language, theme, root_dir, output_file)

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

def build(rebuild, lessons, theme, all_languages, output_dir):
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

            progress_print("Failed", e)

    progress_print("Copying assets...")

    copydir(html_assets, output_dir)

    css_dir = os.path.join(output_dir, "css")
    js_dir  = os.path.join(output_dir, "js")

    makedirs(css_dir)
    makedirs(js_dir)

    make_assets(css_assets, theme, css_dir)
    make_assets(js_assets,  theme, js_dir)

    if theme != 'css':
        languages       = {}
        project_count   = {}
        root_index_file = os.path.join(output_dir, "index.html")
        root_breadcrumb = [('Languages', root_index_file)]

        for language_code, terms in termlangs.iteritems():
            if language_code not in all_languages:
                all_languages[language_code] = Language(
                    code         = language_code,
                    name         = language_code,
                    legal        = {},
                    translations = {}
                )

            language = all_languages[language_code]

            progress_print("Language", language.name)

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
                    project = parse_project_meta(p)

                    progress_print("Building Project: " + project.title)

                    project_dir = os.path.join(term_dir, "%.02d"%(project.number))

                    makedirs(project_dir)

                    built_project = build_project(rebuild, term, project, language, theme, output_dir, project_dir, term_breadcrumb)

                    projects.append(built_project)

                extras = []

                for r in term.extras:
                    progress_print("Building Extra:", r.name)
                    extras.append(build_extra(rebuild, term, r, language, theme, output_dir, term_dir, term_breadcrumb))

                term = Term(
                    id          = term.id,
                    manifest    = term.manifest,
                    number      = term.number,
                    language    = term.language,
                    title       = term.title,
                    description = term.description,
                    projects    = projects,
                    extras      = extras
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

    base_dir = os.path.join(os.path.dirname(filename))
    projects = []

    for p in json_manifest['projects']:
        project = parse_project(p, base_dir, theme)
        projects.append(project)

    extras = parse_extras(json_manifest.get('extras',()), base_dir)

    m = Term(
        id          = json_manifest['id'],
        title       = json_manifest['title'],
        manifest    = filename,
        description = json_manifest['description'],
        language    = json_manifest['language'],
        number      = int(json_manifest['number']),
        projects    = projects,
        extras      = extras
    )

    return m

def parse_project(p, base_dir, theme):
    filename  = expand_glob(base_dir, p['filename'],     one_file = True)
    materials = expand_glob(base_dir, p.get('materials', []))
    embeds    = expand_glob(base_dir, p.get('embeds',    []))
    extras    = p.get('extras', [])
    pdf       = None
    note      = None
    note_pdf  = None

    if isinstance(theme, str) == False and theme.id == "uk":
        progress_print("Preparing to copy PDFs")

        if 'pdf'      in p: pdf      = expand_glob(base_dir, p['pdf'],      one_file = True)
        if 'note_pdf' in p: note_pdf = expand_glob(base_dir, p['note_pdf'], one_file = True)

    if 'note' in p: note = expand_glob(base_dir, p['note'], one_file = True)

    return Project(
        filename  = filename,
        pdf       = pdf,
        number    = p['number'],
        title     = p.get('title', None),
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
        code         = obj['code'],
        name         = obj['name'],
        legal        = obj['legal'],
        translations = obj['translations'],
        links        = obj.get('links', {})
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
        legal                        = obj['legal'],
        logo                         = obj['logo'],
        analytics_account            = obj.get('analytics_account'),
        analytics_domain             = obj.get('analytics_domain'),
        webmaster_tools_verification = obj.get('webmaster_tools_verification'),
        css_variables                = obj['css_variables']
    )

def parse_project_meta(p):
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
        level    = header.get('level', p.level)
        raw_note = header.get('note', None)
        pdf      = None
        note_pdf = None

        if theme.id == "uk":
            pdf      = p.pdf
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

def zip_files(relative_dir, source_files, output_dir, output_file, rebuild):
    if source_files:
        output_file = os.path.join(output_dir, safe_filename(output_file))

        cmd = [
            'zip'
        ]

        if rebuild and os.path.exists(output_file):
            os.remove(output_file)

        if not os.path.exists(output_file):
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

if __name__ == '__main__':
    themes     = load_themes(theme_base)

    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', choices=['wkhtmltopdf', 'phantomjs'], default=None, dest="pdf_generator")
    parser.add_argument('--rebuild', action='store_true', default=False)
    parser.add_argument('region', choices=themes.keys()+['css'])
    parser.add_argument('lesson_dirs', nargs="+")
    parser.add_argument('output_dir')
    p = parser.parse_args()

    progress      = True
    lessons       = [os.path.abspath(a) for a in p.lesson_dirs]
    theme         = themes[p.region] if p.region != 'css' else 'css'
    languages     = load_languages(language_base)
    output_dir    = os.path.abspath(p.output_dir)
    pdf_generator = p.pdf_generator

    build(p.rebuild, lessons, theme, languages, output_dir)

    sys.exit(0)
