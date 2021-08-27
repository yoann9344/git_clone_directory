#!/usr/bin/python
import io
import re
import sys
import tarfile
from dataclasses import dataclass
from os.path import normpath
from os.path import join as path_join
from pathlib import Path, PurePath

import requests


def is_path_secure(tar_info: tarfile.TarInfo, directory: str) -> bool:
    # This check normalize the path for any directory traversal
    # then uses Path's parent attribute to check if the target
    # directory is a parent of the resulting path
    target_dir = Path(directory)
    joined_path = path_join(directory, tar_info.path)
    target_file = PurePath(normpath(joined_path))
    if target_dir not in target_file.parents and target_dir.parent != target_file.parent:
        if debug:
            print(f'DEBUG SECURE {joined_path} will write data outside {target_dir}')
        return False

    # Same as above but for the symlink target
    if tar_info.issym() or tar_info.islnk():
        if debug:
            print('DEBUG SECURE Is a link')
        return False  # do not even consider ln
        symlink_file = PurePath(normpath(
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
    archive_dir: PurePath
    archive_path: PurePath
    is_file: bool

    def extract(self, directory: str):
        nb_files_extracted = 0
        nb_dirs_extracted = 0

        for tarinfo in self.tar:
            if debug:
                print(f'DEBUG path {tarinfo.path}')
            if self.is_file:
                is_in_path = self.archive_path == PurePath(tarinfo.path)
            else:
                is_in_path = self.archive_path in PurePath(tarinfo.path).parents
            if is_in_path:
                # change path that will be created with extract's method
                # to not create empty topdirs
                tarinfo.path = str(
                    PurePath(tarinfo.path).relative_to(self.archive_dir)
                )
                if not is_path_secure(tar_info=tarinfo, directory=directory):
                    continue
                if Path(f'{directory}/{tarinfo.path}').exists() and not yes_man:
                    if no_no_no_no:
                        continue
                    print('Extracting', tarinfo.name.split('/')[-1])
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

                if verbose:
                    print('extracted', tarinfo.name.split('/')[-1])
                self.tar.extract(tarinfo, path=directory)
                if tarinfo.isdir():
                    nb_dirs_extracted += 1
                elif tarinfo.isfile():
                    nb_files_extracted += 1
        print(f'{nb_files_extracted} files extracted !')
        print(f'{nb_dirs_extracted} directories extracted !')
        self.tar.close()


def get_github_archive(url: str):
    archive_url, user, repo_name, is_file, branch, target_path = re.search(
        r'(https://github\.com/([^/]+)/([^/]+)/(tree|blob)/([^/]+))/(.*)$',
        url
    ).groups()
    is_file = is_file == 'blob'

    # replace /tree/ or /blob/ by /archive/
    archive_url = re.sub(
        r'(https://github\.com/[^/]+/[^/]+)/(tree|blob)/',
        r'\1/archive/',
        archive_url,
    )
    archive_url += '.tar.gz'
    first_dir_name = f'{repo_name}-{branch}'
    if is_file:
        target_dir = '/'.join(target_path.split('/')[:-1]) + '/'
        if target_dir == '/':
            target_dir = './'
        archive_path = PurePath(first_dir_name) / target_path
        archive_dir = PurePath(first_dir_name) / target_dir
    else:
        archive_path = PurePath(first_dir_name) / target_path
        archive_dir = archive_path
    if debug:
        if Path('debug.tar.gz').exists():
            tar = tarfile.open('debug.tar.gz', 'r|gz')
        else:
            response = requests.get(archive_url)
            tar = tarfile.open(
                fileobj=io.BytesIO(response.content),
                mode='r|gz',
            )
            with open('debug.tar.gz', 'wb+') as file:
                file.write(response.content)
    else:
        response = requests.get(archive_url)
        tar = tarfile.open(fileobj=io.BytesIO(response.content), mode='r|gz')

    if only_save_tar:
        with open(f'{repo_name}.tar.gz', 'wb+') as file:
            file.write(response.content)
        tar.close()
        exit(0)

    archive = Archive(
        tar,
        archive_url,
        user,
        repo_name,
        branch,
        archive_dir,
        archive_path,
        is_file,
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
    only_save_tar = False

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
        elif param in ['-t', '--tar']:
            only_save_tar = True

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
    PurePath(save_to_path)  # check path is valid

    if debug:
        print(f'{debug=}')
        print(f'{verbose=}')
        print(f'{yes_man=}')
        print(f'{no_no_no_no=}')

    archive = get_github_archive(url)
    archive.extract(directory=save_to_path)
    archive.tar.close()
