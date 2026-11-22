import os
import sys
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REMOTE = "origin"
BRANCH = "main"


def git(*args, capture=False):
    cmd = ["git", "-C", REPO_ROOT, *args]
    if capture:
        return subprocess.check_output(cmd, text=True).strip()
    subprocess.check_call(cmd)
    return ""


def run_update():
    print("======================================")
    print("    HacxGPT System Updater")
    print("======================================")

    # Updates only come from this checkout's own git remote. There is no
    # archive download: code that cannot be reviewed as a diff is not installed.
    if not os.path.isdir(os.path.join(REPO_ROOT, ".git")):
        print("[!] This installation is not a git checkout; automatic update is disabled.")
        print("    Clone the repository with git to receive updates.")
        sys.exit(1)

    try:
        remote_url = git("remote", "get-url", REMOTE, capture=True)
        print(f"[~] Fetching from {REMOTE} ({remote_url})...")
        git("fetch", REMOTE, BRANCH)

        target = git("rev-parse", "FETCH_HEAD", capture=True)
        current = git("rev-parse", "HEAD", capture=True)
        if current == target or not git("rev-list", f"HEAD..{target}", capture=True):
            print("[+] Already up to date.")
            return

        if git("status", "--porcelain", "--untracked-files=no", capture=True):
            print("[!] You have uncommitted local changes. Commit or stash them first.")
            sys.exit(1)

        # Show exactly what would be installed before touching anything
        print("\n[~] Incoming commits:")
        git("--no-pager", "log", "--oneline", f"HEAD..{target}")
        print("\n[~] Files changed:")
        git("--no-pager", "diff", "--stat", f"HEAD...{target}")
        print(f"\n    Full diff: git -C \"{REPO_ROOT}\" diff HEAD...{target[:12]}")

        answer = input("\nApply this update? (y/N) ").strip().lower()
        if answer != "y":
            print("[~] Update cancelled. Nothing was changed.")
            sys.exit(1)

        # Fast-forward to the exact commit that was shown above
        git("merge", "--ff-only", target)
        print("[+] Source updated.")
    except subprocess.CalledProcessError as e:
        print(f"[!] Git operation failed: {e}")
        sys.exit(1)

    print("[~] Finalizing installation...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", REPO_ROOT])
        print("[+] Package re-installed.")
    except Exception as e:
        print(f"[!] Error during dependency update: {e}")
        sys.exit(1)

    print("\n======================================")
    print("      Update Complete!")
    print("======================================")
    print("Restart HacxGPT to apply changes.")


if __name__ == "__main__":
    run_update()
