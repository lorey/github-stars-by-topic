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

    # setup output directory
    output_directory = datetime.datetime.now().strftime("%Y-%m-%d_%H%M") + ' %s - stars by topic' % username
    os.mkdir(output_directory)

    readmes = []

    # maps readme index to repo
    readme_to_repo = {}

    logging.info('fetching stars')
    stars = g.get_user().get_starred()
    for repo in stars:
        user_login, repo_name = repo.full_name.split('/')  # use full name to infer user login

        readme = readmereader.fetch_readme(user_login, repo_name, repo.id)
        readme_text = readmereader.markdown_to_text(readme)
        repo_name_clean = re.sub(r'[^A-z]+', ' ', repo_name)

        full_repo_text = ' '.join([str(repo.description), readme_text, repo_name_clean])
        readme_to_repo[len(readmes)] = repo
        readmes.append(full_repo_text)

    vectorizer = TfidfVectorizer(max_df=0.2, min_df=1, max_features=1000, stop_words='english', norm='l2',
                                 sublinear_tf=True)
    vectors = vectorizer.fit_transform(readmes)

    decomposition = NMF(n_components=number_of_topics)
    model = decomposition.fit_transform(vectors)

    # generate overall readme
    index_readme_text = '# %s\'s stars by topic\n' % username
    index_readme_text += '\n'
    index_readme_text += 'This is a list of topics contained in the stars of %s.' % username
    index_readme_text += '\n'

    topic_list = []
    for topic_idx, topic in enumerate(decomposition.components_):
        top_feature_indices = topic.argsort()[:-11:-1]
        top_feature_names = [vectorizer.get_feature_names()[i] for i in top_feature_indices]

        topic_name = ", ".join(top_feature_names[0:3])

        topic_directory_name = "-".join(top_feature_names[0:3])
        topic_link = topic_directory_name + os.sep + 'README.md'

        topic_list_item = '- [%s](%s)' % (topic_name, topic_link)
        topic_list.append(topic_list_item)

    topic_list.sort()  # sort alphabetically
    index_readme_text += '\n'.join(topic_list)
    with open(output_directory + os.sep + 'README.md', 'w') as index_readme_file:
        index_readme_file.write(index_readme_text)

    print()
    for topic_idx, topic in enumerate(decomposition.components_):
        top_feature_indices = topic.argsort()[:-11:-1]
        top_feature_names = [vectorizer.get_feature_names()[i] for i in top_feature_indices]

        repo_indices_asc = model[:, topic_idx].argsort()
        repo_indices_desc = numpy.flip(repo_indices_asc, 0)

        print("Topic #%d:" % topic_idx)
        print(", ".join(top_feature_names))

        # output repos
        max_weight = model[repo_indices_desc[0], topic_idx]
        for i in repo_indices_desc:
            weight = model[i, topic_idx]
            if weight > 0.05 * max_weight:
                print(readme_to_repo[i], weight)

        # create topic directory
        topic_directory_name = "-".join(top_feature_names[0:3])
        topic_path = output_directory + os.sep + topic_directory_name
        os.mkdir(topic_path)

        # generate readme
        topic_readme_text = "# Repositories defined by: %s\n" % ", ".join(top_feature_names[0:3])
        topic_readme_text += '\n'
        topic_readme_text += "These repositories are also defined by: %s\n" % ", ".join(top_feature_names[3:])
        topic_readme_text += '\n'
        for repo in [readme_to_repo[i] for i in repo_indices_desc if model[i, topic_idx] > 0.1 * max_weight]:
            topic_readme_text += '- [%s](%s)\n' % (repo.full_name, repo.url)
            if repo.description:
                topic_readme_text += '  %s\n' % repo.description

        # write readme
        with open(topic_path + os.sep + 'README.md', 'w') as file:
            file.write(topic_readme_text)
        print()

if __name__ == '__main__':
    main()
