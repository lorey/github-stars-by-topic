import datetime
import getpass
import logging
import os

from .utils import extract_texts_from_repos, generate_overview_readme

import github
import numpy
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer



def main() -> None:
    number_of_topics = 25

    username = input("Your Github Username: ")
    password = getpass.getpass("Your Password (not stored in any way): ")

    g = github.Github(username, password)
    g.per_page = 250  # maximum allowed value

    target_username = input("User to analyze: ")

    logging.info("fetching stars")
    target_user = g.get_user(target_username)
    repos = target_user.get_starred()

    # setup output directory
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_directory = "topics_{}_{}".format(target_username, timestamp)
    os.mkdir(output_directory)

    logging.info("extracts texts for repos (readmes, etc.)")
    texts, text_index_to_repo = extract_texts_from_repos(repos)

    # Classifying
    vectorizer = TfidfVectorizer(
        max_df=0.2,
        min_df=2,
        max_features=1000,
        stop_words="english",
        norm="l2",
        sublinear_tf=True,
    )
    vectors = vectorizer.fit_transform(texts)
    feature_names = vectorizer.get_feature_names()

    decomposition = NMF(n_components=number_of_topics)
    model = decomposition.fit_transform(vectors)

    # generate overview readme
    overview_text = generate_overview_readme(
        decomposition, feature_names, target_username
    )

    # README to get displayed by github when opening directory
    overview_filename = output_directory + os.sep + "README.md"
    with open(overview_filename, "w") as overview_file:
        overview_file.write(overview_text)

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
        topic_readme_text = "# Repositories defined by: %s\n" % ", ".join(
            top_feature_names[0:3]
        )
        topic_readme_text += "\n"
        topic_readme_text += "also defined by the following keywords: %s\n" % ", ".join(
            top_feature_names[3:]
        )
        topic_readme_text += "\n"
        for repo in [
            text_index_to_repo[i]
            for i in repo_indices_desc
            if model[i, topic_idx] > 0.1 * max_weight
        ]:
            topic_readme_text += "- [{}]({})\n".format(repo.full_name, repo.html_url)
            if repo.description:
                topic_readme_text += "  %s\n" % repo.description

        # write readme
        with open(topic_path + os.sep + "README.md", "w") as file:
            file.write(topic_readme_text)
        print()


if __name__ == "__main__":
    main()
