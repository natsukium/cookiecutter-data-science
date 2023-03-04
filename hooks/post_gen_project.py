import os
import shutil

package_manager = "{{cookiecutter.package_manager}}"


def remove(filepath: str) -> None:
    if os.path.isfile(filepath):
        os.remove(filepath)
    elif os.path.isdir(filepath):
        shutil.rmtree(filepath)


def delete_unused_files(package_manager: str) -> None:
    if package_manager != "pip":
        remove("requirements.txt")
        remove("setup.py")
        remove("test_environment.py")


delete_unused_files(package_manager)
