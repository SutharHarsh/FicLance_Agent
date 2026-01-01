import os
import shutil
import subprocess
import stat
from typing import Optional
import re
import tempfile
import zipfile
try:
    import requests
except ImportError:
    requests = None
import urllib.request


def clone_repo(repo_url: str) -> Optional[str]:
    """
    Clones a GitHub repository into a local './project' folder.

    Handles safe removal of the existing folder and correctly decodes
    the git output using UTF-8 to prevent UnicodeDecodeErrors on Windows.

    Args:
        repo_url: The URL of the GitHub repository to clone.

    Returns:
        The path to the cloned project folder ('./project') if successful,
        otherwise None.
    """

    # -------------------------------
    # GitHub repo configuration
    # -------------------------------
    GITHUB_REPO = repo_url
    PROJECT_PATH = "./project"

    # -------------------------------
    # Safe folder removal (handles Access Denied)
    # -------------------------------
    def remove_readonly(func, path, _):
        """Handle read-only files during shutil.rmtree"""
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def safe_remove(path):
        """Safely remove a folder even if it's locked or has readonly files"""
        if os.path.exists(path):
            print(f"Removing existing {path} ...")
            try:
                # Use onerror handler for files with read-only attributes
                shutil.rmtree(path, onerror=remove_readonly)
            except PermissionError as e:
                print(f"[Warning] Could not remove {path} with shutil.rmtree: {e}")
                print("Retrying with system command (rmdir /s /q)...")
                try:
                    # Use system rmdir for potentially locked folders (Windows-specific)
                    subprocess.run(
                        ["rmdir", "/s", "/q", path],
                        shell=True,
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except subprocess.CalledProcessError as e2:
                    print(f"[Error] Final deletion attempt failed: {e2}")

    # -------------------------------
    # Clone GitHub project
    # -------------------------------
    safe_remove(PROJECT_PATH)
    print("Cloning repo:", GITHUB_REPO)

    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", GITHUB_REPO, PROJECT_PATH],
            check=True,
            encoding="utf-8",
            capture_output=True,
            text=True,
        )

        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip())

        print(f"Successfully cloned into {PROJECT_PATH}")
        return PROJECT_PATH

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"\n[ERROR] Git clone failed: {getattr(e, 'returncode', 'N/A')}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"  Error Output:\n{e.stderr.strip()}")
        if hasattr(e, 'stdout') and e.stdout:
            print(f"  Standard Output:\n{e.stdout.strip()}")

        # Fallback: download GitHub archive ZIP if requests is available
        if requests or True:
            print("Attempting ZIP download fallback...")
            m = re.search(r"github\.com[/:]([\w-]+)/([\w.-]+)", GITHUB_REPO)
            if m:
                owner = m.group(1)
                repo = re.sub(r"\.git$", "", m.group(2))
                for branch in ["main", "master", "canary", "dev"]:
                    zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
                    print(f"Trying ZIP branch: {branch}")
                    try:
                        fd, tmp_zip = tempfile.mkstemp(suffix=".zip")
                        os.close(fd)
                        if requests:
                            with requests.get(zip_url, stream=True, timeout=30) as r:
                                r.raise_for_status()
                                with open(tmp_zip, "wb") as f:
                                    for chunk in r.iter_content(chunk_size=8192):
                                        if chunk:
                                            f.write(chunk)
                        else:
                            urllib.request.urlretrieve(zip_url, tmp_zip)
                        with zipfile.ZipFile(tmp_zip, "r") as z:
                            extract_root = tempfile.mkdtemp(prefix="repo_zip_")
                            z.extractall(extract_root)
                            root_items = os.listdir(extract_root)
                            if root_items:
                                src_dir = os.path.join(extract_root, root_items[0])
                                shutil.move(src_dir, PROJECT_PATH)
                                os.remove(tmp_zip)
                                print(f"Successfully downloaded and extracted into {PROJECT_PATH}")
                                return PROJECT_PATH
                            else:
                                raise RuntimeError("Empty ZIP archive")
                    except Exception as ez:
                        print(f"[ERROR] Zip fallback failed for {branch}: {ez}")
                        try:
                            if os.path.exists(tmp_zip):
                                os.remove(tmp_zip)
                        except:
                            pass

        return None


if __name__ == "__main__":
    # Example usage:
    repo = "https://github.com/SutharHarsh/Safar.git"
    cloned_path = clone_repo(repo)

    if cloned_path:
        print(f"\nDone. Project is located at: {cloned_path}")
    else:
        print("\nCloning operation failed.")
