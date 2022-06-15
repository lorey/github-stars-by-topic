from __future__ import annotations

import argparse
import datetime
import getpass
import logging
import os
import sys
from shutil import get_terminal_size

from github import Github
from numpy import flip
from sklearn.decomposition import NMF  # type: ignore[import]
from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore[import]

from . import __version__
from .utils import extract_texts_from_repos, generate_overview_readme


class HelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter
):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        formatter_class=(
            lambda prog: HelpFormatter(
                prog,
                **{
                    "width": get_terminal_size(fallback=(120, 50)).columns,
                    "max_help_position": 25,
                },
            )
        ),
        description="Generate a list of your GitHub stars by topic - automatically!",
    )
    parser.add_argument(
        "-t",
        "--target-username",
        dest="target_username",
        type=str,
        metavar="ID",
        help="gh username to search",
    )
    parser.add_argument(
        "-u",
        "--username",
        metavar="ID",
        type=str,
        help="gh username to login",
    )
    parser.add_argument(
        "-p",
        "--password",
        type=str,
        help="gh password to login",
    )
    parser.add_argument("-V", "--version", action="version", version=__version__)

    return parser.parse_args()


def _main() -> None:
    args = parse_args()
    a_user, a_pass, a_target = args.username, args.password, args.target_username
    number_of_topics = 25

    username = input("Your Github Username: ") if a_user is None else a_user
    password = (
        getpass.getpass("Your Password (not stored in any way): ")
        if a_pass is None
        else a_pass
    )

    g = Github(username, password)
    g.per_page = 250  # maximum allowed value

    target_username = input("User to analyze: ") if a_target is None else a_target

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

    # Non-Negative Matrix Factorization
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
        repo_indices_desc = flip(repo_indices_asc, 0)

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


def main() -> None:
    try:
        _main()
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == "__main__":
    main()
