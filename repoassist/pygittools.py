#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import inspect
import subprocess
from pathlib import Path


__version__ = '0.1.0'

GIT_SSH_COMMAND = 'GIT_SSH_COMMAND'


class PygittoolsError(Exception):
    def __init__(self, msg, returncode):
        super().__init__(msg)
        self.returncode = returncode
        
        
class CmdError(PygittoolsError):
    pass


class ValueError(PygittoolsError):
    pass


class TagNotFoundError(PygittoolsError):
    pass

class NotInWorkTreeError(PygittoolsError):
    pass


def check_work_tree(func):
    def wrapper(*args, **kwargs):
        sign = inspect.signature(func)
        arg_names = list(sign.parameters.keys())
        passed = {k:v for k,v in zip(arg_names[:len(args)], args)}
        passed.update({k:v for k,v in kwargs.items()})
        defaults = {key:value.default for key, value in sign.parameters.items() if value.default is not inspect._empty}
        
        if 'cwd' in passed:
            cwd = passed['cwd']
        else:
            cwd = defaults['cwd']
            
        if not is_work_tree(cwd):
            raise NotInWorkTreeError('Not in work tree', returncode=1)
        return func(*args, **kwargs)
         
    return wrapper
        

def init(cwd='.'):
    return _execute_cmd(['git', 'init'], cwd=cwd)


def clone(url, cwd='.'):
    return _execute_cmd(['git', 'clone', str(url)], cwd=cwd)


@check_work_tree
def add(path, cwd='.'):
    return _execute_cmd(['git', 'add', str(path)], cwd=cwd)


@check_work_tree
def get_origin(cwd='.'):
    return _execute_cmd(['git', 'config', '--get', 'remote.origin.url'], cwd=cwd)


@check_work_tree
def set_origin(url, cwd='.'):
    return _execute_cmd(['git', 'remote', 'add', 'origin', str(url)], cwd=cwd)


@check_work_tree
def is_origin_set(cwd='.'):
    try:
        _execute_cmd(['git', 'config', '--local', 'remote.origin.url'], cwd=cwd)
        return True
    except CmdError:
        return False


@check_work_tree
def set_upstream_to(branch, cwd='.'):
    return _execute_cmd(['git', 'branch', '-u', f'origin/{branch}'], cwd=cwd)    


@check_work_tree
def commit(msg, cwd='.'):
    return _execute_cmd(['git', 'commit', '-m', msg], cwd=cwd)


@check_work_tree
def push(ssh_key=None, cwd='.'):
    return _execute_cmd(['git', 'push'], ssh_key=ssh_key, cwd=cwd)


@check_work_tree
def push_with_tags(ssh_key=None, cwd='.'):
    return _execute_cmd(['git', 'push', '--follow-tags'], ssh_key=ssh_key, cwd=cwd)


@check_work_tree
def revert(commit_rollback, cwd='.'):
    return _execute_cmd(['git', 'reset', '--hard', 'HEAD~{}'.format(commit_rollback)], cwd=cwd)


@check_work_tree
def get_latest_tag(cwd='.'):
    return _execute_cmd(['git', 'describe', '--abbrev=0', '--tags'], cwd=cwd)


@check_work_tree
def get_latest_tag_all_branches(cwd='.'):
    commit_hash = _execute_cmd(['git', 'rev-list', '--tags', '--max-count=1'], cwd=cwd)
    return _execute_cmd(['git', 'describe', '--tags', commit_hash], cwd=cwd)


@check_work_tree
def delete_latest_tag(all_branches=False, cwd='.'):
    try:
        if all_branches:
            latest_tag = get_latest_tag_all_branches(cwd)
        else:
            latest_tag = get_latest_tag(cwd)
    except CmdError:
        raise TagNotFoundError('No tag found.', returncode=1)
    
    return _execute_cmd(['git', 'tag', '-d', latest_tag], cwd=cwd)
        

@check_work_tree
def delete_tag(tag, cwd='.'):
    return _execute_cmd(['git', 'tag', '-d', tag], cwd=cwd)
    

@check_work_tree
def get_latest_tag_msg(cwd='.'):
    return _execute_cmd(['git', 'for-each-ref', '--count=1', '--sort=-taggerdate', '--format', '%(contents)', 'refs/tags'], cwd=cwd)
    

@check_work_tree
def set_tag(tag, msg, cwd='.'):
    return _execute_cmd(['git', 'tag', '-a', tag, '-m', msg], cwd=cwd)
    

@check_work_tree
def list_tags(cwd='.'):
    return list(filter(None, _execute_cmd(['git', 'tag'], cwd=cwd).split('\n')))


@check_work_tree
def list_repo_tree(cwd='.'):
    try:
        return list(filter(None, _execute_cmd(['git', 'ls-tree', '-r', '--name-only', 'HEAD'], cwd=cwd).split('\n')))
    except CmdError as e:
        if 'Not a valid object name HEAD'.lower() in e.__str__().lower():
            return []
        else:
            raise CmdError(e.__str__(), returncode=1)
    

@check_work_tree
def is_any_commit(cwd='.'):
    try:
        _execute_cmd(['git', 'log'], cwd=cwd)
        return True
    except CmdError:
        return False    


@check_work_tree
def is_any_tag(cwd='.'):
    return list_tags(cwd).__len__() > 0

    
def is_work_tree(cwd='.'):
    try:
        if _execute_cmd(['git', 'rev-parse', '--is-inside-work-tree'], cwd=cwd).lower() == 'true':
            return True
        else:
            return False
    except CmdError:
        return False
    

@check_work_tree
def are_uncommited_changes(cwd='.'):
    is_normal_changes = _execute_cmd(['git', '--no-pager', 'diff', '--no-ext-diff'], cwd=cwd) != ''
    is_staged_changes = _execute_cmd(['git', '--no-pager', 'diff', '--no-ext-diff', '--cached'], cwd=cwd) != ''
    
    return is_normal_changes or is_staged_changes
    

@check_work_tree
def get_latest_commit_hash(cwd='.'):
    return _execute_cmd(["git", "log", "--pretty=format:%h", "-n", "1"], cwd=cwd)


@check_work_tree
def get_tag_commit_hash(tag, cwd='.'):
    return _execute_cmd(["git", "log", "--pretty=format:%h", "-n", "1", tag], cwd=cwd)


@check_work_tree
def get_changelog(report_format=None, cwd='.'):
    if not report_format:
        report_format = "%(taggerdate:short) | Release: %(tag) \r\n%(contents)"
        
    return _execute_cmd(["git", "for-each-ref", "--sort=-creatordate",
                               "--format={}".format(report_format),
                               "refs/tags"], cwd=cwd)


@check_work_tree
def update_all_submodules(ssh_key=None, cwd='.'):
    return _execute_cmd(["git", "submodule", "update", "--recursive", "--remote"], ssh_key=ssh_key, cwd=cwd)


@check_work_tree
def deinit_all_submodules(cwd='.'):
    return _execute_cmd(["git", "submodule", "deinit", "--force", "--all"], cwd=cwd)


@check_work_tree
def clear_cache(path, cwd='.'):
    return _execute_cmd(["git", "rm", "-rf", "--cached", str(path)], cwd=cwd)


@check_work_tree
def get_commit_msgs_from_last_tag(cwd='.'):
    try:
        latest_tag = get_latest_tag(cwd)
        msg_list = _execute_cmd(['git', 'log', '--pretty=%B', f'{latest_tag}..HEAD'], cwd=cwd).split('\n')
    except PygittoolsError:
        msg_list = _execute_cmd(['git', 'log', '--pretty=%B', 'HEAD'], cwd=cwd).split('\n')
    msg_list.reverse()

    return '\n'.join(msg_list) 


def _execute_cmd(args, ssh_key=None, cwd='.'):
    cwd = Path(cwd).resolve()
    if not cwd.exists():
        raise CmdError('Current working directory not exists.', returncode=1)
    
    if ssh_key:
        ssh_key_path = Path(ssh_key).resolve().as_posix()
        env = os.environ.copy()
        env[GIT_SSH_COMMAND] = f'ssh -i "{ssh_key_path}"'
    else:
        env = None
        
    try:
        process = subprocess.run(args,
                                 check=True,
                                 cwd=cwd.__str__(),
                                 env=env,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 encoding="utf-8")
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise CmdError(e.output, returncode=e.returncode)
