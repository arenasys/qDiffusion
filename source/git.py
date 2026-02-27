import os
import time
import pygit2

QDIFF_URL = "https://github.com/stromtroopertk421/qDiffusion_Updateproject"
INFER_URL = "https://github.com/stromtroopertk421/sd-inference-server"
TRAIN_URL = "https://github.com/arenasys/sd-scripts"

DEFAULT_BRANCHES = ("master", "main")


def git_remote_head(repo):
    for branch in DEFAULT_BRANCHES:
        name = f"refs/remotes/origin/{branch}"
        ref = repo.references.get(name)
        if ref:
            return ref.raw_target
    raise KeyError("Could not find origin master/main branch reference")

def git_repair(repo, origin):
    repo.remotes.delete("origin")
    repo.create_remote("origin", origin)
    repo.remotes["origin"].fetch()

def git_reset(path, origin):
    repo = pygit2.Repository(os.path.abspath(path))
    repo.remotes.set_url("origin", origin)
    repo.remotes["origin"].fetch()
    try:
        head = git_remote_head(repo)
    except:
        git_repair(repo, origin)
        head = git_remote_head(repo)
    repo.reset(head, pygit2.GIT_RESET_HARD)

def git_last(path):
    try:
        repo = pygit2.Repository(os.path.abspath(path))
        commit = repo[repo.head.target]
        message = commit.raw_message.decode('utf-8').strip()
        delta = time.time() - commit.commit_time
    except Exception as e:
        if type(e) == pygit2.GitError and str(e).startswith("Repository not found"):
            return None, None
        else:
            raise e
    
    spans = [
        ('year', 60*60*24*365),
        ('month', 60*60*24*30),
        ('day', 60*60*24),
        ('hour', 60*60),
        ('minute', 60),
        ('second', 1)
    ]
    when = "?"
    for label, span in spans:
        if delta >= span:
            count = int(delta//span)
            suffix = "" if count == 1 else "s"
            when = f"{count} {label}{suffix} ago"
            break

    return commit, f"{message} ({commit.short_id}) ({when})"

def git_init(path, origin):
    repo = pygit2.init_repository(os.path.abspath(path), False)
    if not "origin" in repo.remotes:
        repo.create_remote("origin", origin)
    git_reset(path, origin)

def git_clone(path, origin):
    pygit2.clone_repository(origin, path)
