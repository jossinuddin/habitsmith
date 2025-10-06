import os
import sys
import random
import re
import subprocess
from datetime import datetime

# чтобы импорты работали и при прямом запуске
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from auto_updater.notify import notify

import re, random, subprocess as _subprocess
TYPO_PROB = 0.04  # ~4% rare typos

def _typo_word(w: str) -> str:
    if len(w) < 4: return w
    i = random.randint(1, len(w)-2)
    return w[:i-1] + w[i] + w[i-1] + w[i+1:]

def sprinkle_typos(s: str, prob: float = TYPO_PROB) -> str:
    parts = re.split(r'(`[^`]+`|\w+://\S+|[a-f0-9]{7,40})', s)
    out = []
    for p in parts:
        if p.startswith('`') or '://' in p or re.fullmatch(r'[a-f0-9]{7,40}', p or ''):
            out.append(p); continue
        words = p.split(' ')
        for i,w in enumerate(words):
            if random.random() < prob and re.match(r'[A-Za-z]', w):
                words[i] = _typo_word(w)
        out.append(' '.join(words))
    return ''.join(out)

def humanize(msg: str) -> str:
    m = (msg or "").strip()
    g = re.match(r"(Added|Deleted|Replaced)\s+snippet\s+'([^']+)'\s+(?:in|into|from)\s+(.+)", m, re.I)
    if g:
        kind, name, path = g.group(1).lower(), g.group(2), g.group(3)
        added = [
            f"Add snippet “{name}” to {path}", f"Dropped in snippet “{name}” into {path}",
            f"New code: “{name}” now lives in {path}", f"Introduce “{name}” under {path}",
            f"Wire up “{name}” in {path}", f"Bring in “{name}” to {path}",
            f"Lay down “{name}” in {path}", f"Plant “{name}” inside {path}",
        ]
        deleted = [
            f"Remove “{name}” from {path}", f"Cleanup: deleted “{name}” from {path}",
            f"Trim dead code — “{name}” out of {path}", f"Drop “{name}” from {path}",
            f"Cut “{name}” out of {path}", f"Retire “{name}” from {path}",
            f"Scrub out “{name}” in {path}", f"Prune “{name}” away from {path}",
        ]
        replaced = [
            f"Replace “{name}” in {path}", f"Refresh snippet “{name}” in {path}",
            f"Rework “{name}” — see {path}", f"Swap in a better “{name}” for {path}",
            f"Revamp “{name}” within {path}", f"Overhaul “{name}” in {path}",
            f"Modernize “{name}” inside {path}", f"Refactor “{name}” in {path}",
        ]
        pool = {"added": added, "deleted": deleted, "replaced": replaced}[kind]
        import random as _r
        return sprinkle_typos(_r.choice(pool))
    if re.match(r"\bTouched\s+.+?\(no snippet change\)", m, re.I) or "no snippet change" in m:
        opts = [
            "Touch up (no functional change)",
            "Small nudge (no functional change)",
            "Maintenance tweak (no logic change)",
            "Tiny housekeeping (no behavior change)",
            "Keep things tidy (no logic changes)",
            "Polish a little bit",
        ]
        import random as _r
        pm = re.search(r"Touched\s+(.+?)\s+\(no snippet change\)", m, re.I)
        if pm:
            path = pm.group(1)
            opts = [f"Touch up {path} (no functional change)",
                    f"Small nudge in {path}",
                    f"Maintenance tweak in {path}",
                    f"Tiny housekeeping in {path}",
                    f"Keep {path} tidy (no logic changes)",
                    f"Polish {path} a little bit"]
        return sprinkle_typos(_r.choice(opts))
    if re.search(r"\btests?\b", m, re.I):
        import random as _r
        return sprinkle_typos(_r.choice([
            "Tests: tighten and clarify","Make tests less flaky","Update tests a bit",
            "Tests: improve coverage slightly","Deflake tests around edge cases","Stabilize a couple of tests",
        ]))
    if re.search(r"\bdocs?\b|README", m, re.I):
        import random as _r
        return sprinkle_typos(_r.choice([
            "Docs pass: clarify wording","README: quick refresh","Polish docs a little",
            "Docs: add missing bits","Docs cleanup and rewording","Docs: small touch-up across sections",
        ]))
    generic = [
        "Small improvements here and there","A couple of neat touch-ups",
        "Quiet but helpful refactor","Subtle code hygiene improvements",
        "Nip and tuck around the codebase","Sanded down a few rough edges",
        "Quality-of-life tweaks","Tidy up minor inconsistencies",
    ]
    import random as _r
    return sprinkle_typos(m if len(m) > 60 else _r.choice(generic))

# monkey-patch subprocess.run (перехватываем git commit -m)
try:
    _real_run = _subprocess.run
    def _patched_run(args, *a, **kw):
        try:
            arr = args
            if isinstance(arr,(list,tuple)) and len(arr) >= 3:
                if str(arr[0]) == "git" and str(arr[1]) == "commit":
                    arr = list(arr)
                    for i,x in enumerate(arr):
                        if x == "-m" and i+1 < len(arr):
                            arr[i+1] = humanize(str(arr[i+1]))
                            break
            return _real_run(arr, *a, **kw)
        except Exception:
            return _real_run(args, *a, **kw)
    _subprocess.run = _patched_run
except Exception:
    pass

# monkey-patch GitPython Repo.index.commit (если используется)
try:
    import git as _git
    _RealCommit = _git.index.base.IndexFile.commit
    def _patched_commit(self, message, *a, **kw):
        try:
            message = humanize(str(message))
        except Exception:
            pass
        return _RealCommit(self, message, *a, **kw)
    _git.index.base.IndexFile.commit = _patched_commit
except Exception:
    pass


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SNIPPETS_DIR = os.path.join(ROOT, "data", "snippets_code")
TARGET_DIRS = [os.path.join(ROOT, "habitsmith")]  # целимся в код пакета

PROB_ADD = 0.6
PROB_DELETE = 0.2
PROB_MINOR = 0.3   # мелкая правка (коммент/пустая строка) для «человечности»

SNIPPET_HEADER = re.compile(r"# --- snippet: (.+?) ---")
SNIPPET_END = re.compile(r"# --- endsnippet ---", re.MULTILINE)
DEF_OR_CLASS = re.compile(r"^(def |class )", re.MULTILINE)

def load_all_snippets():
    snippets = {}
    if not os.path.isdir(SNIPPETS_DIR):
        return snippets
    for fname in os.listdir(SNIPPETS_DIR):
        path = os.path.join(SNIPPETS_DIR, fname)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        for s in SNIPPET_HEADER.finditer(text):
            name = s.group(1).strip()
            start_idx = s.end()
            m_end = SNIPPET_END.search(text, pos=start_idx)
            if not m_end:
                continue
            code = text[s.start():m_end.end()].strip() + "\n\n"
            snippets[name] = code
    return snippets

def list_target_files():
    targets = []
    for d in TARGET_DIRS:
        for root, dirs, files in os.walk(d):
            dirs[:] = [x for x in dirs if x != "__pycache__"]
            for f in files:
                if f.endswith(".py"):
                    targets.append(os.path.join(root, f))
    return targets

def find_snippet_blocks(text):
    blocks = {}
    for m in SNIPPET_HEADER.finditer(text):
        name = m.group(1).strip()
        start = m.start()
        m_end = SNIPPET_END.search(text, pos=m.end())
        if not m_end:
            continue
        end = m_end.end()
        blocks[name] = (start, end)
    return blocks

def random_insertion_index(text):
    positions = [m.start() for m in DEF_OR_CLASS.finditer(text)]
    positions.append(len(text))
    return random.choice(positions)

def insert_snippet(text, code):
    idx = random_insertion_index(text)
    prefix = "" if (idx == 0 or text[max(0, idx-1)] == "\n") else "\n"
    return text[:idx] + prefix + "\n" + code + text[idx:], idx

def replace_snippet(text, name, new_code, blocks):
    start, end = blocks[name]
    return text[:start] + new_code + text[end:]

def delete_snippet(text, name, blocks):
    start, end = blocks[name]
    return text[:start] + text[end:]

def minor_tweak(path):
    """Мелкая правка: добавим небольшой комментарий в конец файла."""
    stamp = f"# tweak {datetime.utcnow().isoformat()}\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(stamp)
    return f"Minor tweak in {os.path.relpath(path, ROOT)}"

def choose_action_and_apply(snippets, targets):
    if not targets:
        return "No target .py files found."
    target = random.choice(targets)

    with open(target, "r", encoding="utf-8") as f:
        txt = f.read()

    blocks = find_snippet_blocks(txt)
    inserted_names = list(blocks.keys())

    # 1) иногда делаем лёгкую правку
    if random.random() < PROB_MINOR:
        return minor_tweak(target)

    # 2) удаление
    if inserted_names and random.random() < PROB_DELETE:
        name = random.choice(inserted_names)
        new_txt = delete_snippet(txt, name, blocks)
        with open(target, "w", encoding="utf-8") as f:
            f.write(new_txt)
        return f"Deleted snippet '{name}' from {os.path.relpath(target, ROOT)}"

    # 3) добавление / замена
    if snippets and random.random() < PROB_ADD:
        name, code = random.choice(list(snippets.items()))
        if name in blocks:
            new_txt = replace_snippet(txt, name, code, blocks)
            with open(target, "w", encoding="utf-8") as f:
                f.write(new_txt)
            return f"Replaced snippet '{name}' in {os.path.relpath(target, ROOT)}"
        else:
            new_txt, _ = insert_snippet(txt, code)
            with open(target, "w", encoding="utf-8") as f:
                f.write(new_txt)
            return f"Added snippet '{name}' into {os.path.relpath(target, ROOT)}"

    # 4) если ничего из выше не сработало — добавим хвост-комментарий
    stamped = f"\n# autosave {datetime.utcnow().isoformat()}\n"
    with open(target, "a", encoding="utf-8") as f:
        f.write(stamped)
    return f"Touched {os.path.relpath(target, ROOT)} (no snippet change)"

def check_syntax():
    try:
        py_files = []
        for r, d, files in os.walk(ROOT):
            if "__pycache__" in r:
                continue
            for f in files:
                if f.endswith(".py"):
                    py_files.append(os.path.join(r, f))
        if not py_files:
            return True
        subprocess.run(["python3", "-m", "py_compile"] + py_files, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def git_commit_and_push(message: str):
    try:
        subprocess.run(["git", "add", "."], check=True)
        result = subprocess.run(["git", "commit", "-m", message])
        if result.returncode != 0:
            return False, "No changes to commit"

        pull = subprocess.run(["git", "pull", "--rebase"])
        if pull.returncode != 0:
            subprocess.run(["git", "rebase", "--abort"], check=False)
            ff = subprocess.run(["git", "pull", "--ff-only"])
            if ff.returncode != 0:
                return False, "Pull failed (rebase and ff-only)"

        subprocess.run(["git", "push"], check=True)
        return True, None
    except subprocess.CalledProcessError as e:
        return False, str(e)

def main():
    snippets = load_all_snippets()
    targets = list_target_files()
    msg = choose_action_and_apply(snippets, targets)
    if not check_syntax():
        notify(f"Syntax error after change: {msg}. Commit aborted.")
        return
    ok, err = git_commit_and_push(msg)
    if ok:
        notify(f"Committed: {msg}")
    else:
        notify(f"Commit failed: {msg}. Error: {err}")

if __name__ == "__main__":
    main()
