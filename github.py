#!/usr/bin/python
import io
import re
import sys
import tarfile
from dataclasses import dataclass
from os.path import normpath
from os.path import join as path_join
from pathlib import Path

import requests


def is_path_secure(tar_info: tarfile.TarInfo, directory: str) -> bool:
    # This check normalize the path for any directory traversal
    # then uses Path's parent attribute to check if the target
    # directory is a parent of the resulting path
    target_dir = Path(directory)
    target_file = Path(normpath(path_join(directory, tar_info.path)))
    if target_dir not in target_file.parents:
        return False

    # Same as above but for the symlink target
    if tar_info.issym() or tar_info.islnk():
        return False  # do not even consider ln
        symlink_file = Path(normpath(
            path_join(directory, tar_info.linkname)
        ))
        if target_dir not in symlink_file.parents:
            return False
    return True


def handle_answer(answer: str) -> bool:
    if answer == 'y':
        return True
    elif answer == 'Y':
        global yes_man
        yes_man = True
        return True
    elif answer == 'n':
        return False
    elif answer == 'N':
        global no_no_no_no
        no_no_no_no = True
        return False
    return None


@dataclass
class Archive:
    tar: tarfile.TarFile
    archive_url: str
    user: str
    repo_name: str
    branch: str
    path: str
    archive_path: str

    def extract(self, directory: str):
        nb_files_extracted = 0
        nb_dirs_extracted = 0
        for tarinfo in self.tar:
            archive_path_length = len(self.archive_path)
            if tarinfo.name.startswith(self.archive_path):
                # change path that will create to not create empty subdirs
                tarinfo.path = tarinfo.path[archive_path_length:]
                if not is_path_secure(tar_info=tarinfo, directory=directory):
                    continue
                if Path(f'{directory}/{tarinfo.path}').exists() and not yes_man:
                    if no_no_no_no:
                        continue
                    print('Extracting', tarinfo.name.split('/')[-1], '?')
                    validated = None
                    while validated is None:
                        validated = input(
                            'This file already exist, wanna overide it ?'
                            'y/n/Y/N (Y: yes all, N: no all) '
                        )
                        sys.stdout.write('\033[F\033[1G\033[K' * 2)
                        validated = handle_answer(validated)
                    if not validated:
                        continue

                self.tar.extract(tarinfo, path=directory)
                if tarinfo.isdir():
                    nb_dirs_extracted += 1
                elif tarinfo.isfile():
                    nb_files_extracted += 1
                if verbose:
                    print('extracted', tarinfo.name.split('/')[-1])
        print(f'{nb_files_extracted} files extracted !')
        print(f'{nb_dirs_extracted} directories extracted !')
        self.tar.close()


def get_github_archive(url: str):
    archive_url, user, repo_name, branch, path = re.search(
        r'(https://github\.com/([^/]+)/([^/]+)/(?:tree|blob)/([^/]+))/(.*)$',
        url
    ).groups()

    # replace /tree/ or /blob/ by /archive/
    archive_url = re.sub(
        r'(https://github\.com/[^/]+/[^/]+)/(tree|blob)/',
        r'\1/archive/',
        archive_url,
    )
    archive_url += '.tar.gz'
    first_dir_name = f'{repo_name}-{branch}'
    archive_path = f'{first_dir_name}/{path}/'
    if debug:
        tar = tarfile.open('test.tar.gz', 'r:gz')
    else:
        response = requests.get(archive_url)
        tar = tarfile.open(fileobj=io.BytesIO(response.content), mode='r|gz')

    archive = Archive(
        tar,
        archive_url,
        user,
        repo_name,
        branch,
        path,
        archive_path,
    )
    return archive


if __name__ == '__main__':
    # url = 'https://github.com/richardanaya/js-wasm/tree/master/examples/snake'
    # save_to_path = 'plop/'
    # debug = True
    # verbose = True
    # yes_man = False
    # no_no_no_no = False

    url = None
    save_to_path = None
    debug = False
    verbose = False
    yes_man = False
    no_no_no_no = False

    params = sys.argv[1:]
    for i, param in enumerate(params):
        if param in ['-v', '--verbose']:
            verbose = True
        elif param in ['-d', '--debug']:
            debug = True
        elif param in ['-y', '--yes']:
            yes_man = True
        elif param in ['-n', '--no']:
            no_no_no_no = True

        if param.startswith('-'):
            pass
        elif url is None:
            url = param
        elif save_to_path is None:
            save_to_path = param

    if url is None:
        print('Required parameter : url')
        exit(0)
    elif save_to_path is None:
        save_to_path = '.'
    Path(save_to_path)  # check path is valid

    if debug:
        print(f'{debug=}')
        print(f'{verbose=}')
        print(f'{yes_man=}')
        print(f'{no_no_no_no=}')

    archive = get_github_archive(url)
    archive.extract(directory=save_to_path)
    archive.tar.close()
