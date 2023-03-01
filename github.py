#!/usr/bin/python
import io
import re
import sys
import tarfile
from dataclasses import dataclass
from inspect import cleandoc
from os.path import normpath, join as path_join
from pathlib import Path, PurePath
from typing import ClassVar

import requests


@dataclass
class Debugger:
    name: str
    active: bool = False

    def __call__(self, *args, **kwargs):
        if self.active:
            print(f"{self.name}: ", *args, **kwargs)

    def __bool__(self) -> bool:
        return self.active


debug = Debugger("DEBUG")
verbose = Debugger("VERBOSE")


def is_path_secure(tar_info: tarfile.TarInfo, directory: str) -> bool:
    # This check normalize the path for any directory traversal
    # then uses Path's parent attribute to check if the target
    # directory is a parent of the resulting path
    target_dir = Path(directory)
    joined_path = path_join(directory, tar_info.path)
    target_file = PurePath(normpath(joined_path))
    if target_dir not in target_file.parents and target_dir.parent != target_file.parent:
        debug(f"SECURE {joined_path} will write data outside {target_dir}")
        return False

    # Same as above but for the symlink target
    if tar_info.issym() or tar_info.islnk():
        debug("SECURE Is a link")
        return False  # do not even consider ln
        symlink_file = PurePath(normpath(path_join(directory, tar_info.linkname)))
        if target_dir not in symlink_file.parents:
            return False
    return True


def handle_answer(answer: str) -> bool | None:
    if answer == "y":
        return True
    elif answer == "Y":
        Archive.yes_man = True
        return True
    elif answer == "n":
        return False
    elif answer == "N":
        Archive.no_no_no_no = True
        return False
    return None


@dataclass
class Archive:
    tar: tarfile.TarFile
    archive_url: str
    user: str
    repo_name: str
    branch: str
    archive_dir: PurePath
    archive_path: PurePath
    is_file: bool
    directory: str
    no_no_no_no: ClassVar[bool] = False
    yes_man: ClassVar[bool] = False

    def extract(self, force_directory: str | None = None):
        if force_directory is not None:
            directory = force_directory
        else:
            directory = self.directory
        nb_files_extracted = 0
        nb_dirs_extracted = 0
        if only_save_tar:
            new_tar = tarfile.open(f"{self.repo_name}.tar.gz", mode="w|gz")

        for tarinfo in self.tar:
            # if self.is_file:
            #     is_in_path = self.archive_path == PurePath(tarinfo.path)
            # else:
            is_in_path = PurePath(tarinfo.path).is_relative_to(self.archive_path)
            debug(f"path ({is_in_path}) {tarinfo.path} => {self.archive_path}")
            if is_in_path:
                # change path that will be created with extract's method
                # to not create empty topdirs
                tarinfo.path = str(PurePath(tarinfo.path).relative_to(self.archive_path))
                if only_save_tar:
                    verbose("Only save tar")
                    new_tar.addfile(tarinfo, self.tar.extractfile(tarinfo))
                    continue
                elif not is_path_secure(tar_info=tarinfo, directory=directory):
                    verbose("Path not secure")
                    continue
                elif Path(f"{directory}/{tarinfo.path}").exists() and not self.yes_man:
                    if self.no_no_no_no:
                        continue
                    print("Extracting", tarinfo.name.split("/")[-1])
                    validated = None
                    while validated is None:
                        answer = input("This file already exist, wanna overide it ?" "y/n/Y/N (Y: yes all, N: no all) ")
                        # remove previous question and its answer
                        sys.stdout.write("\033[F\033[1G\033[K" * 2)
                        validated = handle_answer(answer)
                    if not validated:
                        continue

                verbose("extracted", tarinfo.name.split("/")[-1])
                self.tar.extract(tarinfo, path=directory)
                if tarinfo.isdir():
                    nb_dirs_extracted += 1
                elif tarinfo.isfile():
                    nb_files_extracted += 1
        print(f"{nb_files_extracted} files extracted !")
        print(f"{nb_dirs_extracted} directories extracted !")
        if only_save_tar:
            new_tar.close()
        self.tar.close()


def get_github_archive(url: str):
    directory = "."
    extracted_url = re.search(r"(https://github\.com/([^/]+)/([^/]+)/(tree|blob)/([^/]+))/(.*)$", url)
    if extracted_url is not None:
        archive_url, user, repo_name, is_file, branch, target_path = extracted_url.groups()
    else:
        raise ValueError("Can't extract url.")
    is_file = is_file == "blob"

    # replace /tree/ or /blob/ by /archive/
    archive_url = re.sub(
        r"(https://github\.com/[^/]+/[^/]+)/(tree|blob)/",
        r"\1/archive/",
        archive_url,
    )
    archive_url += ".tar.gz"
    first_dir_name = f"{repo_name}-{branch}"
    if is_file:
        target_dir = "/".join(target_path.split("/")[:-1]) + "/"
        if target_dir == "/":
            target_dir = "./"
        archive_path = PurePath(first_dir_name) / target_path
        archive_dir = PurePath(first_dir_name) / target_dir
    else:
        archive_path = PurePath(first_dir_name) / target_path
        archive_dir = archive_path
        directory = archive_path.parts[-1]
    if debug:
        if Path("debug.tar.gz").exists():
            tar = tarfile.open("debug.tar.gz", "r|gz")
        else:
            response = requests.get(archive_url)
            tar = tarfile.open(
                fileobj=io.BytesIO(response.content),
                mode="r|gz",
            )
            with open("debug.tar.gz", "wb+") as file:
                file.write(response.content)
    else:
        response = requests.get(archive_url)
        tar = tarfile.open(fileobj=io.BytesIO(response.content), mode="r|gz")

    archive = Archive(
        tar,
        archive_url,
        user,
        repo_name,
        branch,
        archive_dir,
        archive_path,
        is_file,
        directory,
    )
    return archive


if __name__ == "__main__":
    # url = 'https://github.com/richardanaya/js-wasm/tree/master/examples/snake'
    # save_to_path = 'plop/'
    # debug = True
    # verbose = True
    # no_no_no_no = False

    url = None
    save_to_path = None
    only_save_tar = False

    params = sys.argv[1:]
    for i, param in enumerate(params):
        if param in ["-v", "--verbose"]:
            verbose.active = True
        elif param in ["-d", "--debug"]:
            debug.active = True
        elif param in ["-y", "--yes"]:
            Archive.yes_man = True
        elif param in ["-n", "--no"]:
            Archive.no_no_no_no = True
        elif param in ["-t", "--tar"]:
            only_save_tar = True
        elif param in ["-p", "--path"]:
            directory = param
        elif param in ["-h", "--help"]:
            print(
                cleandoc(
                    """
                    github <ARGUMENTS> <github_url>

                    ARGUMENTS
                    =========
                    -v --verbose : More verbose.
                    -d --debug : Debug verbosity. Load debug.tar.gz if it exists unless dowload the archive of the link and save it in debug.tar.gz
                    -y --yes : Answer yes to all overriding questions.
                    -n --no : Answer no to all overriding questions.
                    -t --tar : download the tar extract the corresponding path to another tar without extracting it.
                    -h --help : show the help.
                    """
                )
            )
            exit(0)

        if param.startswith("-"):
            pass
        elif url is None:
            url = param

    if url is None:
        print("Required parameter : url ; use -h for --help")
        exit(0)

    archive = get_github_archive(url)
    archive.extract(save_to_path)
    archive.tar.close()
