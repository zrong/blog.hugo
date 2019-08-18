# -*- coding: utf-8 -*-

import logging
import sys
from fabric import task, Connection
from invoke.exceptions import Exit

logger = logging.Logger('fabric', level=logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


class Tmux(object):
    """Tmux helper for fabric"""
    def __init__(self, session_name, run_cmd=run):
        self.session_name = session_name
        self.run_cmd = run_cmd

        self.create_session()

    def create_session(self):
        with settings(warn_only=True):
            test = self.run_cmd('tmux has-session -t %s' % self.session_name)

        if test.failed:
            self.run_cmd('tmux new-session -d -s %s' % self.session_name)

        self.run_cmd(
            'tmux set-option -t %s -g allow-rename off' % self.session_name)

    def recreate(self):
        self.kill_session()
        self.create_session()

    def kill_session(self):
        self.run_cmd('tmux kill-session -t %s' % self.session_name)

    def command(self, command, pane=0):
        self.run_cmd('tmux send-keys -t %s:%s "%s" ENTER' % (
            self.session_name, pane, command))

    def new_window(self, name):
        self.run_cmd('tmux new-window -t %s -n %s' % (self.session_name, name))

    def find_window(self, name):
        with settings(warn_only=True):
            test = self.run_cmd('tmux list-windows -t %s | grep \'%s\'' % (self.session_name, name))

        return not test.failed

    def rename_window(self, new_name, old_name=None):
        if old_name is None:
            self.run_cmd('tmux rename-window %s' % new_name)
        else:
            self.run_cmd('tmux rename-window -t %s %s' % (old_name, new_name))

    def wait_for(self, signal_name):
        self.run_cmd('tmux wait-for %s' % signal_name)

    def run_singleton(self, command, orig_name):
        run_name = "run/%s" % orig_name
        done_name = "done/%s" % orig_name

        # If the program is running we wait to be finished.
        if self.find_window(run_name):
            self.wait_for(run_name)

        # If the program is not running we create a window with done_name
        if not self.find_window(done_name):
            self.new_window(done_name)

        self.rename_window(run_name, done_name)

        # Check that we can execute the commands in the correct window
        assert self.find_window(run_name)

        rename_window_cmd = 'tmux rename-window -t %s %s' % (
            run_name, done_name)
        signal_cmd = 'tmux wait-for -S %s' % run_name

        expanded_command = '%s ; %s ; %s' % (
            command, rename_window_cmd, signal_cmd)
        self.command(expanded_command, run_name)

        self.wait_for(run_name)


@task
def test():
    t = Tmux('session', run_cmd=local)
    t.run_singleton('sleep 10', 'sleeping')

SITE_WEBROOT = '/srv/www/hugo.zengrong.net'
GIT_URI = 'git@github.com:zrong/blog.hugo.git'

@task
def test(c):
    if not isinstance(c, Connection):
        raise Exit('Use -H to provide a host!')
    logger.warning('conn: %s', c)
    git_dir = '$HOME/blog.hugo'
    hugo_cache_dir = '{0}/hugo_cache'.format(git_dir)
    r = c.run('test -e ' + git_dir, warn=True)
    logger.warning('r: %s', r.command)
    if r.ok:
        c.run('git --git-dir={0}/.git --work-tree={0} reset --hard'.format(git_dir), warn=False)
        c.run('git --git-dir={0}/.git --work-tree={0} pull origin master'.format(git_dir) , warn=False)
        c.run('tmux -c hugo --cacheDir {0}'.format(hugo_cache_dir))
    else:
        c.run('git clone {0} $HOME/blog.hugo'.format(GIT_URI))
