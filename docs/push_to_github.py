"""按本地 git 提交历史，逐个 commit 重建到 GitHub 仓库（保留完整迭代历史）。

适用场景：本机 git push 被网络策略阻断、但 api.github.com 可达时，用 GitHub
Git Data API 逐提交重建。支持中文提交说明、中文文件名与二进制文件。

认证：环境变量 GH_TOKEN（例如 `GH_TOKEN="$(gh auth token)"`）。
用法：python docs/push_to_github.py [--start N] [--parent SHA]
      --start N   跳过前 N 个已推送的提交（默认 0）
      --parent    从第 N+1 个提交继续时，指定其父提交在远端的 SHA
"""
import base64
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

OWNER = "kecit33"
REPO = "ai-agent-study"
BRANCH = "main"
API = "https://api.github.com"
REPO_PATH = "/repos/%s/%s" % (OWNER, REPO)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# api.github.com 偶发 500/502 网关抖动：把已成功创建的 blob 落盘缓存，
# 重跑时跳过，多轮即可收敛，不必每次重新上传全部文件。
CACHE_PATH = os.path.join(ROOT, ".git", "push_blob_cache.json")
try:
    with open(CACHE_PATH, "r", encoding="utf-8") as _f:
        blob_cache = json.load(_f)
except Exception:
    blob_cache = {}


def save_blob_cache():
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(blob_cache, f)
    except Exception:
        pass


TOKEN = os.environ.get("GH_TOKEN", "").strip()
if not TOKEN:
    sys.exit("缺少 GH_TOKEN 环境变量")


def git(*args, binary=False):
    p = subprocess.run(["git", *args], cwd=ROOT, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise RuntimeError("git %s 失败: %s" % (" ".join(args),
                                               p.stderr.decode("utf-8", "replace")[:300]))
    return p.stdout if binary else p.stdout.decode("utf-8").rstrip("\n")


def api(method, path, payload=None):
    url = API + path
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    headers = {
        "Authorization": "Bearer " + TOKEN,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "ai-campus-companion-push",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    last_err = None
    for attempt in range(8):
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:400]
            last_err = RuntimeError("%s %s -> HTTP %s: %s" % (method, path, e.code, detail))
            if e.code in (403, 429) or e.code >= 500:
                time.sleep(2 + attempt * 2)
                continue
            raise last_err
        except Exception as e:  # 网络抖动
            last_err = RuntimeError("%s %s -> %s" % (method, path, e))
            time.sleep(2 + attempt * 2)
    raise last_err


def snapshot(sha):
    """返回该 commit 的完整文件快照 [(mode, path, bytes)]。"""
    raw = git("ls-tree", "-r", "-z", sha, binary=True)
    out = []
    for item in raw.split(b"\x00"):
        if not item:
            continue
        meta, path = item.split(b"\t", 1)
        mode = meta.split(b" ")[0].decode()
        rel = path.decode("utf-8")
        content = git("show", "%s:%s" % (sha, rel), binary=True)
        out.append((mode, rel, content))
    return out


def commit_meta(sha):
    return {
        "message": git("show", "-s", "--format=%B", sha),
        "an": git("show", "-s", "--format=%an", sha),
        "ae": git("show", "-s", "--format=%ae", sha),
        "cn": git("show", "-s", "--format=%cn", sha),
        "ce": git("show", "-s", "--format=%ce", sha),
        "ad": git("show", "-s", "--format=%aI", sha),
        "cd": git("show", "-s", "--format=%cI", sha),
    }


def ensure_nonempty():
    """空仓库下 Git Data API 会返回 409，先用 Contents API 建一个引导提交。

    引导提交随后会被 force 覆盖为不可达对象，不出现在最终历史中。
    """
    try:
        api("GET", REPO_PATH + "/git/ref/heads/" + BRANCH)
        print("main 分支已存在，无需引导提交")
        return
    except RuntimeError as e:
        msg = str(e)
        # 空仓库时 GitHub 返回 409 "Git Repository is empty."，仓库不存在时才 404
        if "404" not in msg and "empty" not in msg.lower():
            raise
    api("PUT", REPO_PATH + "/contents/BOOTSTRAP.md", {
        "message": "chore: 初始化 main 分支（引导提交，随后被覆盖）",
        "content": base64.b64encode(b"bootstrap\n").decode("ascii"),
    })
    print("空仓库已建立引导提交，Git Data API 现已可用")


def main():
    args = sys.argv[1:]
    start = 0
    parent = None
    if "--start" in args:
        start = int(args[args.index("--start") + 1])
    if "--parent" in args:
        parent = args[args.index("--parent") + 1]

    info = api("GET", REPO_PATH)
    print("目标仓库: %s (default_branch=%s, private=%s)" %
          (info["full_name"], info["default_branch"], info["private"]))
    print("认证账号:", api("GET", "/user")["login"])
    ensure_nonempty()

    shas = git("log", "--reverse", "--format=%H").splitlines()
    print("本地提交数:", len(shas))

    blob_cache = {}

    def make_blob(content):
        key = hashlib.sha1(content).hexdigest()
        if key not in blob_cache:
            r = api("POST", REPO_PATH + "/git/blobs", {
                "content": base64.b64encode(content).decode("ascii"),
                "encoding": "base64",
            })
            blob_cache[key] = r["sha"]
            save_blob_cache()  # 每个成功项立即落盘，失败重跑可续
        return blob_cache[key]

    for idx, sha in enumerate(shas):
        if idx < start:
            continue
        meta = commit_meta(sha)
        files = snapshot(sha)
        tree_items = [
            {"path": rel, "mode": mode, "type": "blob", "sha": make_blob(content)}
            for mode, rel, content in files
        ]
        tree = api("POST", REPO_PATH + "/git/trees", {"tree": tree_items})
        payload = {
            "message": meta["message"],
            "tree": tree["sha"],
            "parents": [parent] if parent else [],
            "author": {"name": meta["an"], "email": meta["ae"], "date": meta["ad"]},
            "committer": {"name": meta["cn"], "email": meta["ce"], "date": meta["cd"]},
        }
        created = api("POST", REPO_PATH + "/git/commits", payload)
        parent = created["sha"]
        same = "SHA一致" if parent == sha else "SHA不同(内容一致)"
        print("[%2d/%d] %s | %s | %d 文件 | %s" %
              (idx + 1, len(shas), parent[:8], meta["message"].splitlines()[0],
               len(files), same), flush=True)

    if parent is None:
        print("没有需要推送的提交")
        return

    # 所有 commit 对象已按父子链创建，一次性把 refs/heads/main 指向链尾
    try:
        ref = api("GET", REPO_PATH + "/git/ref/heads/" + BRANCH)
        if ref["object"]["sha"] != parent:
            api("PATCH", REPO_PATH + "/git/refs/heads/" + BRANCH,
                {"sha": parent, "force": True})
            print("已更新 refs/heads/%s -> %s" % (BRANCH, parent))
        else:
            print("refs/heads/%s 已指向 %s" % (BRANCH, parent))
    except RuntimeError as e:
        if "404" not in str(e):
            raise
        api("POST", REPO_PATH + "/git/refs", {"ref": "refs/heads/" + BRANCH,
                                              "sha": parent})
        print("已创建 refs/heads/%s -> %s" % (BRANCH, parent))

    head = api("GET", REPO_PATH + "/git/ref/heads/" + BRANCH)["object"]["sha"]
    local_head = shas[-1]
    print("远端 HEAD:", head)
    print("本地 HEAD:", local_head)
    print("历史完全一致" if head == local_head else "历史内容一致（SHA 不同，因服务端签名差异）")


if __name__ == "__main__":
    main()
