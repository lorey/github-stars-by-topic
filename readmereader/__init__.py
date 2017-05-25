import os
import re
from time import sleep

import logging
import requests
from bs4 import BeautifulSoup
from markdown import markdown

from main import CACHE_PATH_READMES


def fetch_readme(user_login, repo_name, repo_id):
    cache_key = str(repo_id)
    cache_file = CACHE_PATH_READMES + os.sep + cache_key

    # check if file is cached
    if os.path.isfile(cache_file):
        with open(cache_file, 'r') as file:
            return file.read()

    # create cache folder
    if not os.path.isdir(CACHE_PATH_READMES):
        os.mkdir(CACHE_PATH_READMES)

    potential_readme_names = [
        'README.md',  # list should end here
        'readme.md',
        'Readme.md',  # WHY?
        'readme.txt',
        'README.rst',  # todo cannot actually parse this
        'README.markdown',
        'README'
    ]

    for readme_name in potential_readme_names:
        url = 'https://raw.githubusercontent.com/%s/%s/master/%s' % (user_login, repo_name, readme_name)
        response = requests.get(url)
        if response.status_code == 200:
            # write to cache
            try:
                readme_content = response.content.decode('utf-8')
            except UnicodeDecodeError:
                logging.exception('not unicode for: %s/%s' % (user_login, repo_name))
                return ''

            with open(cache_file, 'w') as file:
                file.write(readme_content)
            return readme_content
        elif response.status_code != 404:
            raise RuntimeError(response.status_code)

    logging.warning('no readme found for: %s/%s' % (user_login, repo_name))
    return ''


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
