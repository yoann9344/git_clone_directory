# Extract a github directory
Clone only a subdirectory from Github without creating or replacing the .git/ config !
If a file already exist ask if you want to replace it.

## Installation
```bash
# Requires "requests"
pip install requests
# Clone this repository somewhere
mkdir -p ~/bin/ && cd ~/bin/
git clone https://github.com/yoann9344/git_clone_directory.git && cd git_clone_directory/
# Add right to execute
chmod +x github.py
# then link github.py to your $PATH
# example link in /usr/bin with name github
ln -s ~/bin/git_clone_directory/github.py /usr/bin/github

# then to update
cd ~/bin/git_clone_directory/ && git pull && chmod +x github.py
```

## Command Line Interface
```bash
github [OPTIONS] GITHUB_DIRECTORY [PATH]
```

#### *Github_directory*

Github link to a directory, following this regex :

```regex
(https://github\.com/([^/]+)/([^/]+)/(?:tree|blob)/([^/]+))/(.*)$
```

#### *Path*

Directory where the github subfolder will be retrieved (default='.')

#### *Options*

The options can't be group (-vd won't activate neither debug or verbose mode)

-d, --debug => Debug mode

-v, --verbose => Verbose mode (show each extracted file)

-y, --yes => Say yes to all questions (will replace existing files)

-n, --no => Say no to all questions (will not replace existing files)

## Examples
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
