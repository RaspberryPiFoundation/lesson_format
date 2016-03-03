import os
import sys
import shutil
import subprocess
import argparse
import requests
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
#   heroku run python autobuild.py [--rebuild]

def rm_files(directory, ignore_list):
    rm_files = [os.path.join(directory, x) for x in os.listdir(directory) if x not in ignore_list]
    for rm_file in rm_files:
        if os.path.isdir(rm_file):
            # print 'deleting directory: %s' % rm_file
            shutil.rmtree(rm_file)
        else:
            # print 'deleting file: %s' % rm_file
            os.remove(rm_file)

def get_reason_text(reason):
    if reason is None:
        return "Someone told me to run a build"

    if reason == 'cron':
        return "I ran my scheduled nightly build"

    repos = ['%s-curriculum' % x for x in ['scratch', 'python', 'webdev']]
    if reason in repos:
        return "Changes were made to the %s repository" % reason

    return "I became self-aware"

def autobuild(reason, **kwargs):
    # TODO: fail gracefully if these aren't set
    gh_user = os.environ['GITHUB_USER']
    gh_token = os.environ['GITHUB_TOKEN']
    gh_push_url = os.environ['PUSH_URL']
    print "Let's autobuild this sucker!"
    print "GITHUB_USER: %s" % gh_user

    verbose = kwargs.get('verbose', False)
    rebuild = kwargs.get('rebuild', False)
    clean = kwargs.get('clean', False)
    pdf_generator = 'phantomjs'

    dont_remove = ['.git', '.gitignore', '.travis.yml', 'CNAME', 'README.md', 'requirements.txt']
    output_dir = 'output/codeclubworld_autobuild'

    gh_repo = 'CodeClubWorld-Projects'

    r = Github(gh_user, gh_token).get_repo('CodeClub/%s' % gh_repo)

    # clone the curricula repos (the lazy way)
    subprocess.call('make clone'.split())

    # clone the output repo
    subprocess.call(('git clone https://%s:%s@github.com/CodeClub/%s.git %s' % (gh_user, gh_token, gh_repo, output_dir)).split())

    if clean:
        # delete everything in the output dir
        rm_files(output_dir, dont_remove)

    # init gitpython!
    repo = Repo(output_dir)

    # run the build
    print "** running the build"
    build.build(pdf_generator, ['lessons/scratch', 'lessons/webdev', 'lessons/python'], "cc", output_dir, verbose, repo, rebuild)

    repo.git.remote('set-url', '--push', 'origin', gh_push_url)

    # stage everything...
    print "** stage everything"
    repo.git.add('--all')
    # NB. it seems weird, but this reason can disagree
    # with the PR (since we force push)
    reason_text = get_reason_text(reason)

    try:
        # ... commit it...
        print "** commiting the rebuild"
        repo.git.commit('-m', 'Rebuild', '-m', reason_text)
        # ...and push!
        # TODO: Don't force push here!
        print "** pushing the changes"
        repo.git.push('-f', 'origin', 'gh-pages')
    except GitCommandError as e:
        print "** ERROR GitCommandError: "
        print e
        sys.exit()

    # submit pull request
    try:
        print "** creating the PR"
        msg = "Hello!\n\n"
        msg += "I've been hard at work, rebuilding the Code Club World's projects website from the latest markdown.\n\n"
        msg += "%s and I found some updates, so I thought I'd best send a pull request. You can view my updated version here:\nhttp://%s.github.io/%s/\n\n" % (reason_text, gh_user, gh_repo)
        msg += "Have a nice day!"
        r.create_pull(title='Rebuild', body=msg, head='%s:gh-pages' % gh_user, base='gh-pages')
    except GithubException as e:
        print "** ERROR GithubException: "
        print e
        # TODO: handle this.
        # Usually it just means the PR already exists, which is
        # nothing too much to worry about.
        pass

def snitch(reason):
    #ping dead man's snitch to let it know we're done
    requests.get("https://nosnch.in/fa3c5a1026?m=finished+world+build")

# this is run by the nightly cron, or a one-off call
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--rebuild', action='store_true')
    parser.add_argument('--clean', action='store_true')
    parser.add_argument('reason', nargs='?')
    p = parser.parse_args()

    autobuild(p.reason, verbose=p.verbose, rebuild=p.rebuild, clean=p.clean)
    snitch(p.reason)

