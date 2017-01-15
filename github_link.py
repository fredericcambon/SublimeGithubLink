import os
import sublime
import sublime_plugin

from subprocess import check_output, CalledProcessError


def shell_cmd(cmd):
    try:
        return check_output(cmd, shell=True).strip().decode('utf-8')
    except CalledProcessError as exc:
        print(exc)


class GithubLinkCommand(sublime_plugin.TextCommand):
    """
    Simple script to translate the current selection
    into Github format
    """
    github_url = 'https://github.com/'
    link_tpl = '{host}{repo}/blob/{branch}/{path}'

    def find_git_root_path(self):
        return shell_cmd('git rev-parse --show-toplevel')

    def get_remote_name(self):
        remote_url = shell_cmd('git config --get remote.origin.url')

        if self.github_url in remote_url:
            return remote_url.replace(self.github_url, '').replace('.git', '')
        else:
            return remote_url.replace('git@github.com:', '').replace('.git', '')

    def get_current_branch(self):
        return shell_cmd('git rev-parse --abbrev-ref HEAD')

    def rows_to_github_format(self, line_a, line_b):
        link = '#L{}'.format(min(line_a, line_b))

        if line_b != line_a:
            link += '-L{}'.format(max(line_a, line_b))

        return link

    def run(self, edit):
        def read_rowcol(p):
            row, col = self.view.rowcol(p)
            return row + 1, col

        abs_cur_path = self.view.file_name()
        abs_cur_folder = os.path.split(abs_cur_path)[0]

        # Necessary for git shell commands
        # ¯\_(ツ)_/¯
        os.chdir(abs_cur_folder)
        root_path = self.find_git_root_path()

        if not root_path:
            self.view.show_popup('No git repo found!')
            return

        repo = self.get_remote_name()
        branch = self.get_current_branch()
        rel_cur_path = os.path.relpath(abs_cur_path, root_path)
        link = self.link_tpl.format(host=self.github_url, repo=repo, branch=branch, path=rel_cur_path)

        sel = self.view.sel()[0]

        if not sel.empty():
            line_a, col_a = read_rowcol(sel.a)
            line_b, col_b = read_rowcol(sel.b)

            if col_b == 0:
                line_b = line_b - 1

            link += self.rows_to_github_format(line_a, line_b)

        sublime.status_message('Path copied to clipboard!')
        sublime.set_clipboard(link)
