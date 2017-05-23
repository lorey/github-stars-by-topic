import getpass
import logging
import os
import re
from time import sleep

import datetime
import numpy
import requests
from bs4 import BeautifulSoup
from github import Github
from markdown import markdown
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer

CACHE_PATH_READMES = 'cache'


def main():
    number_of_topics = 25

    username = input('Your Github Username:')
    password = getpass.getpass('Your Password (not stored in any way):')

    g = Github(username, password)
    g.per_page = 250

    # setup output directory
    output_directory = datetime.datetime.now().strftime("%Y-%m-%d_%H%M") + ' %s - stars by topic' % username
    os.mkdir(output_directory)

    readmes = []

    # maps readme index to repo
    readme_to_repo = {}

    logging.info('fetching stars')
    stars = g.get_user().get_starred()
    for repo in stars:
        user_login, repo_name = repo.full_name.split('/')

        readme = fetch_readme(user_login, repo_name, repo.id)
        readme_text = markdown_to_text(readme)
        repo_name_clean = re.sub(r'[^A-z]+', ' ', repo_name)

        readme_to_repo[len(readmes)] = repo
        readmes.append(' '.join([str(repo.description), readme_text, repo_name_clean]))

    vectorizer = TfidfVectorizer(max_df=0.2, min_df=1, max_features=1000, stop_words='english', norm='l2', sublinear_tf=True)
    vectors = vectorizer.fit_transform(readmes)

    decomposition = NMF(n_components=number_of_topics)
    model = decomposition.fit_transform(vectors)

    print()
    for topic_idx, topic in enumerate(decomposition.components_):
        top_feature_indices = topic.argsort()[:-11:-1]
        top_feature_names = [vectorizer.get_feature_names()[i] for i in top_feature_indices]

        repo_indices_asc = model[:, topic_idx].argsort()
        repo_indices_desc = numpy.flip(repo_indices_asc, 0)

        print("Topic #%d:" % topic_idx)
        print(", ".join(top_feature_names))

        max_weight = model[repo_indices_desc[0], topic_idx]
        for i in repo_indices_desc:
            weight = model[i, topic_idx]
            if weight > 0.05 * max_weight:
                print(readme_to_repo[i], weight)

        topic_directory_name = "-".join(top_feature_names[0:3])
        topic_path = output_directory + os.sep + topic_directory_name
        os.mkdir(topic_path)

        readme_content = "# Repositories defined by: %s\n" % ", ".join(top_feature_names[0:3])
        readme_content += '\n'
        readme_content += "These repositories are also defined by: %s\n" % ", ".join(top_feature_names[3:])
        readme_content += '\n'
        for repo in [readme_to_repo[i] for i in repo_indices_desc if model[i, topic_idx] > 0.1 * max_weight]:
            readme_content += '- [%s](%s)\n' % (repo.full_name, repo.url)
            if repo.description:
                readme_content += '  %s\n' % repo.description

        with open(topic_path + os.sep + 'README.md', 'w') as file:
            file.write(readme_content)
        print()


def fetch_readme(user_login, repo_name, repo_id):
    cache_key = str(repo_id)
    cache_file = CACHE_PATH_READMES + os.sep + cache_key

    if os.path.isfile(cache_file):
        with open(cache_file, 'r') as file:
            return file.read()

    if not os.path.isdir(CACHE_PATH_READMES):
        os.mkdir(CACHE_PATH_READMES)

    names = ['README.md', 'readme.md', 'readme.txt', 'README.rst', 'README.markdown', 'README']
    for name in names:
        sleep(1)
        url = 'https://raw.githubusercontent.com/%s/%s/master/%s' % (user_login, repo_name, name)
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
    html = markdown(markdown_string)

    # remove code snippets
    html = re.sub(r'<pre>(.*?)</pre>', ' ', html)
    html = re.sub(r'<code>(.*?)</code >', ' ', html)

    soup = BeautifulSoup(html)
    text = ''.join(soup.findAll(text=True))
    return text

if __name__ == '__main__':
    main()
