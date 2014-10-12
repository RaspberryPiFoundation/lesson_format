import os
import sys
import shutil
import subprocess
from git import Repo
from git.exc import GitCommandError
from github import Github
from github.GithubException import GithubException
import build

# Set these before deploying:
#   heroku config:set BUILDPACK_URL=git://github.com/andylolz/heroku-buildpack-python-extras.git
#   heroku config:set GITHUB_USER=[github username]
#   heroku config:set GITHUB_TOKEN=[github token]
#
# One-off usage:
#   heroku run python autobuild.py [uk|world]

def rm_files(directory, ignore_list):
    rm_files = [os.path.join(directory, x) for x in os.listdir(directory) if x not in ignore_list]
    for rm_file in rm_files:
        if os.path.isdir(rm_file):
            # print 'deleting directory: %s' % rm_file
            shutil.rmtree(rm_file)
        else:
            # print 'deleting file: %s' % rm_file
            os.remove(rm_file)

def reason_text(reason):
    if reason is None:
        return "Someone told me to run a build"

    if reason == 'cron':
        return "I ran my scheduled nightly build"

    repos = ['%s-curriculum' % x for x in ['scratch', 'python', 'webdev']]
    if reason in repos:
        return "Someone pushed a commit to the %s repository" % reason

    return "I became self-aware"

def autobuild(region, reason=None):
    # TODO: fail gracefully if these aren't set
    gh_user = os.environ['GITHUB_USER']
    gh_token = os.environ['GITHUB_TOKEN']

    dont_remove = ['.git', '.gitignore', '.travis.yml', 'CNAME', 'README.md', 'requirements.txt']
    output_dir = 'output/codeclub%s' % region
    # case sensitivity issues
    pp_region = {
        'uk': 'UK',
        'world': 'World'
    }[region]
    gh_repo = 'CodeClub%s-Projects' % pp_region

    r = Github(gh_user, gh_token).get_repo('andylolz/%s' % gh_repo)

    # TODO: Sort out world css so we can generate world pdfs!
    pdf_generator = 'phantomjs' if region == 'uk' else None

    # clone all the repos (the lazy way)
    subprocess.call('make clone'.split())

    # delete everything in the output dir
    rm_files(output_dir, dont_remove)

    # init gitpython!
    repo = Repo(output_dir)

    # run the build
    build.build(pdf_generator, ['lessons/scratch', 'lessons/webdev', 'lessons/python'], region, output_dir, repo)

    # add username and token to remote url
    # (so we can write)
    origin_url = repo.remotes.origin.url
    origin_url = 'https://%s:%s@github.com/%s/%s' % (gh_user, gh_token, gh_user, origin_url[28:])
    repo.git.remote('set-url', '--push', 'origin', origin_url)

    # stage everything...
    repo.git.add('--all')
    # ... commit it...
    # TODO: Explain *why* we're doing this build
    # (e.g. someone pushed to scratch-curriculum)
    repo.git.commit('-m', 'Rebuild')
    # ...and push!
    # TODO: Don't force push here!
    repo.git.push('-f', 'origin', 'gh-pages')

    # submit pull request
    try:
        msg = "Hello!\n\n"
        msg += "I've been hard at work, rebuilding the Code Club %s projects website from the latest markdown.\n\n" % pp_region
        msg += reason_text(reason)
        msg += " and I found some updates, so I thought I'd best send a pull request. You can view my updated version here:\nhttp://%s.github.io/%s/\n\n" % (gh_user, gh_repo)
        msg += "Have a nice day!"
        r.create_pull(title='Rebuild', body=msg, head='%s:gh-pages' % gh_user, base='gh-pages')
    except GithubException:
        # TODO: handle this.
        # Usually it just means the PR already exists, which is
        # nothing too much to worry about.
        pass

if __name__ == "__main__":
    region = sys.argv[1]
    reason = sys.argv[2] if len(sys.argv > 1) else None
    autobuild(region, reason)
