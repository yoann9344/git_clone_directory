## Extract a github directory
Clone only a subdirectory from Github without creating or replacing the .git/ config !
If a file already exist ask if you want to replace it.

### Options
github [OPTIONS] GITHUB_DIRECTORY [PATH]

**GITHUB_DIRECTORY**

Github link to a directory, following this regex :

```regex
(https://github\.com/([^/]+)/([^/]+)/tree/([^/]+))/(.*)$
```

**PATH**

PATH='.'
    Directory where the github subfolder will be retrieved

**OPTIONS**

The options can't be group (-vd won't activate neither debug or verbose mode)

-d, --debug
    Debug mode

-v, --verbose
    Verbose mode (show each extracted file)

-y, --yes
    Say yes to all questions (will replace existing files)

-n, --no
    Say no to all questions (will not replace existing files)

### Examples
```bash
# Copy content of directory '/path/to/subfolder' from this reposistory to the current directory
# will copy nothing because the '/path/to/subfolder' does not exist in this repo
github.py https://github.com/yoann9344/git_clone_directory/tree/main/path/to/subfolder
# Copy content of directory '/plugin' from the vim-regex-syntax's repo to the ~/.vim/plugin
github.py https://github.com/Galicarnax/vim-regex-syntax/blob/master/plugin/regex.vim ~/.vim/plugin/
# Copy content of directory '/plugin' from the vim-regex-syntax's repo to the ~/.vim/plugin
# Replacing all existing files without asking with a verbose mode
github.py -v --yes https://github.com/Galicarnax/vim-regex-syntax/blob/master/plugin/regex.vim ~/.vim/plugin/
```
