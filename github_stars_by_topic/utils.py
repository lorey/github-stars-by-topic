from . import readmereader
import re
import os

def generate_overview_readme(decomposition, feature_names: list[str], username: str):
    text = "# %s's stars by topic\n" % username
    text += "\n"
    text += (
        "This is a list of topics covered by the starred repositories of %s." % username
    )
    text += "\n"

    topic_list = []
    for topic_idx, topic in enumerate(decomposition.components_):
        top_feature_indices = topic.argsort()[:-11:-1]
        top_feature_names = [feature_names[i] for i in top_feature_indices]

        topic_name = ", ".join(top_feature_names[0:3])

        topic_directory_name = "-".join(top_feature_names[0:3])
        topic_link = topic_directory_name + os.sep + "README.md"

        topic_list_item = "- [{}]({})".format(topic_name, topic_link)
        topic_list.append(topic_list_item)

    topic_list.sort()  # sort alphabetically
    text += "\n".join(topic_list)

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
    repo_login, repo_name = repo.full_name.split(
        "/"
    )  # use full name to infer user login

    # readme = readmereader.fetch_readme(user_login, repo_name, repo.id)
    readme = readmereader.fetch_readme(repo)
    readme_text = readmereader.markdown_to_text(readme)

    repo_name_clean = re.sub(r"[^A-z]+", " ", repo_name)

    texts = [
        str(repo.description),
        str(repo.description),
        str(repo.description),  # use description 3x to increase weight
        str(repo.language),
        readme_text,
        repo_name_clean,
    ]
    return " ".join(texts)
