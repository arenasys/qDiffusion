import os
import time
import pygit2

QDIFF_URL = "https://github.com/arenasys/qDiffusion"
INFER_URL = "https://github.com/arenasys/sd-inference-server"

def git_reset(path, origin):
    repo = pygit2.Repository(os.path.abspath(path))
    repo.remotes.set_url("origin", origin)
    repo.remotes[0].fetch()
    head = repo.lookup_reference("refs/remotes/origin/master").raw_target
    repo.reset(head, pygit2.GIT_RESET_HARD)

def git_last(path):
    try:
        repo = pygit2.Repository(os.path.abspath(path))
        commit = repo[repo.head.target]
        message = commit.raw_message.decode('utf-8').strip()
        delta = time.time() - commit.commit_time
    except:
        return None, None
    
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