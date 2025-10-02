import os
import sys
import random
import re
import subprocess
from datetime import datetime

# чтобы импорты работали и при прямом запуске
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from auto_updater.notify import notify

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
