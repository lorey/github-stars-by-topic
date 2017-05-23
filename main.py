import datetime
import getpass
import logging
import os
import re

import numpy
from github import Github
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer

import readmereader

CACHE_PATH_READMES = 'cache'


def main():
    number_of_topics = 25

    username = input('Your Github Username:')
    password = getpass.getpass('Your Password (not stored in any way):')

    g = Github(username, password)
    g.per_page = 250  # maximum allowed value

    target_username = input('User to analyze:')

    # setup output directory
    output_directory = datetime.datetime.now().strftime("%Y-%m-%d_%H%M") + ' %s - stars by topic' % target_username
    os.mkdir(output_directory)

    logging.info('fetching stars')
    target_user = g.get_user(target_username)
    repos = target_user.get_starred()

    logging.info('extracts texts for repos (readmes, etc.)')
    texts, text_index_to_repo = extract_texts_from_repos(repos)

    vectorizer = TfidfVectorizer(max_df=0.2, min_df=1, max_features=1000, stop_words='english', norm='l2',
                                 sublinear_tf=True)
    vectors = vectorizer.fit_transform(texts)
    feature_names = vectorizer.get_feature_names()

    decomposition = NMF(n_components=number_of_topics)
    model = decomposition.fit_transform(vectors)

    # generate overview readme
    overview_readme_text = generate_overview_readme(decomposition, feature_names, target_username)
    with open(output_directory + os.sep + 'README.md', 'w') as overview_readme_file:
        overview_readme_file.write(overview_readme_text)

    # generate topic folders and readmes
    print()
    for topic_idx, topic in enumerate(decomposition.components_):
        top_feature_indices = topic.argsort()[:-11:-1]
        top_feature_names = [feature_names[i] for i in top_feature_indices]

        repo_indices_asc = model[:, topic_idx].argsort()
        repo_indices_desc = numpy.flip(repo_indices_asc, 0)

        print("Topic #%d:" % topic_idx)
        print(", ".join(top_feature_names))

        # output repos
        max_weight = model[repo_indices_desc[0], topic_idx]
        for i in repo_indices_desc:
            weight = model[i, topic_idx]
            if weight > 0.05 * max_weight:
                print(text_index_to_repo[i], weight)

        # create topic directory
        topic_directory_name = "-".join(top_feature_names[0:3])
        topic_path = output_directory + os.sep + topic_directory_name
        os.mkdir(topic_path)

        # generate readme
        topic_readme_text = "# Repositories defined by: %s\n" % ", ".join(top_feature_names[0:3])
        topic_readme_text += '\n'
        topic_readme_text += "These repositories are also defined by: %s\n" % ", ".join(top_feature_names[3:])
        topic_readme_text += '\n'
        for repo in [text_index_to_repo[i] for i in repo_indices_desc if model[i, topic_idx] > 0.1 * max_weight]:
            topic_readme_text += '- [%s](%s)\n' % (repo.full_name, repo.url)
            if repo.description:
                topic_readme_text += '  %s\n' % repo.description

        # write readme
        with open(topic_path + os.sep + 'README.md', 'w') as file:
            file.write(topic_readme_text)
        print()


def generate_overview_readme(decomposition, feature_names, username):
    text = '# %s\'s stars by topic\n' % username
    text += '\n'
    text += 'This is a list of topics contained in the stars of %s.' % username
    text += '\n'

    topic_list = []
    for topic_idx, topic in enumerate(decomposition.components_):
        top_feature_indices = topic.argsort()[:-11:-1]
        top_feature_names = [feature_names[i] for i in top_feature_indices]

        topic_name = ", ".join(top_feature_names[0:3])

        topic_directory_name = "-".join(top_feature_names[0:3])
        topic_link = topic_directory_name + os.sep + 'README.md'

        topic_list_item = '- [%s](%s)' % (topic_name, topic_link)
        topic_list.append(topic_list_item)

    topic_list.sort()  # sort alphabetically
    text += '\n'.join(topic_list)

    return text


def extract_texts_from_repos(repos):
    readmes = []
    readme_to_repo = {}  # maps readme index to repo

    for repo in repos:
        full_repo_text = get_text_for_repo(repo)
        readme_to_repo[len(readmes)] = repo
        readmes.append(full_repo_text)

    return readmes, readme_to_repo


def get_text_for_repo(repo):
    user_login, repo_name = repo.full_name.split('/')  # use full name to infer user login

    readme = readmereader.fetch_readme(user_login, repo_name, repo.id)
    readme_text = readmereader.markdown_to_text(readme)

    repo_name_clean = re.sub(r'[^A-z]+', ' ', repo_name)

    return ' '.join([str(repo.description), readme_text, repo_name_clean])


if __name__ == '__main__':
    main()
