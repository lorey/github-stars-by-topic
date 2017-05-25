import os
import re
import github
from time import sleep

import logging
import requests
from bs4 import BeautifulSoup
from markdown import markdown

from main import CACHE_PATH_READMES


def fetch_readme(repo):
    cache_key = str(repo.id)
    cache_file = CACHE_PATH_READMES + os.sep + cache_key

    # check if file is cached
    if os.path.isfile(cache_file):
        with open(cache_file, 'r') as file:
            return file.read()

    # create cache folder
    if not os.path.isdir(CACHE_PATH_READMES):
        os.mkdir(CACHE_PATH_READMES)

    try:
        readme = repo.get_readme()
    except github.GithubException:
        # Readme wasn't found
        logging.warning('no readme found for: ' + repo.full_name)
        return ''

    return readme.content


def markdown_to_text(markdown_string):
    # md -> html -> text since BeautifulSoup can extract text cleanly
    html = markdown(markdown_string)

    # remove code snippets
    html = re.sub(r'<pre>(.*?)</pre>', ' ', html)
    html = re.sub(r'<code>(.*?)</code >', ' ', html)

    # extract text
    soup = BeautifulSoup(html, "html.parser")
    text = ''.join(soup.findAll(text=True))

    return text
