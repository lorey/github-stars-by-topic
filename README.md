# Your GitHub stars sorted by topic/category

This is a python script that fetches your GitHub stars and uses Machine Learning (buzzword, check) to extract a given number of topics. It then generates a folder structure so you can easily browse through the topics in markdown.

The result can be viewed in the [example folder](example/).

## Usage

Just run `python3 main.py` on the command line. It will ask you for your GitHub credentials to fetch your stars and then do its job. The result will be a folder in the main directory that you can copy or save in a GitHub repository for others to browse.

## How it works

This section will give you a brief overview how the tool works.

Before starting to work, the tool asks you for your GitHub credentials to be able to use the API with [5000 instead of 60 requests per hour](https://developer.github.com/v3/#rate-limiting). It then starts to fetch the stars of the targeted user. This results in a list of repositories the user has starred.

```
starred_repos = [
    Repo(name='Totally not Jarvis'),
    Repo(name='Laravel'),
    # and so on
]
```

To apply the topic extraction later, we need to find a text describing the repo. To do this, for each starred repo the title, description, and README file is fetched and used as a text. This generates a list of texts for each starred repository. The example below shows how this would look for [my personal assistant bot called Totally not Jarvis](https://github.com/lorey/totally-not-jarvis) and [Laravel, the PHP framework](https://github.com/laravel/laravel).

```
readmes = [
    'totally not jarvis my personal assistant totally not jarvis a personal...',
    'laravel a php framework for web artisans about laravel laravel is a web...',
    # and so on
]
```

We then apply [Term Frequency Inverse Document Frequency (tf-idf)](https://en.wikipedia.org/wiki/Tf%E2%80%93idf) pre-processing on the list to extract relevant keywords for each repo. This results in a list of repos with corresponding tf-idf weights. A high tf-idf value means the term is very relevant for this document, a low value means the term is irrelevant (i.e. not existing or too common). The benefit of tf-idf values over plain term frequencies is that it results in low weights for terms that are very common. Or how [Wikipedia](https://en.wikipedia.org/wiki/Tf%E2%80%93idf) puts it:

> The tf-idf value increases proportionally to the number of times a word appears in the document, but is often offset by the frequency of the word in the corpus, which helps to adjust for the fact that some words appear more frequently in general.


|                    | php | framework | bot | web |
|--------------------|-----|-----------|-----|-----|
| Laravel            | 0.8 | 0.5       | 0   | 0.7 |
| Totally not Jarvis | 0   | 0.6       | 0.8 | 0.1 |


Afterwards, we apply [Non-Negative Matrix Factorization (NMF)](https://en.wikipedia.org/wiki/Non-negative_matrix_factorization) to extract the underlying topics defined by their most-relevant keywords. This gives us two results. Firstly, a list of topics defined by their most-important keywords (high value means more relevance for the topic):

|         | php | framework | bot | web |
|---------|-----|-----------|-----|-----|
| Topic 1 | 0.8 | 0.1       | 0   | 0.7 |
| Topic 2 | 0   | 0.8       | 0.1 | 0.1 |

The example shows two resulting topics. Topic 1 is defined by the keywords `php` and `web`. Topic 2 is defined by the keyword `framework`.

And secondly, NMF yields a list of repositories per topic:

|         | Laravel | Totally not Jarvis |
|---------|---------|--------------------|
| Topic 1 | 0.9     | 0.1                |
| Topic 2 | 0.8     | 0.7                |

We see Laravel fits into both topics. On the other hand, Totally not Jarvis just fits into Topic 2 (defined by `framework`) but not into Topic 1 (defined by `php` and `web`).
This data is then used to create folders named after the most relevant keywords. Afterwards, a readme file with the most relevant repositories for each topic is generated. You can explore the pre-generated examples in the [example folder](example/).

Further reading:
- [example for topic extraction in the scikit-learn documentation](http://scikit-learn.org/stable/auto_examples/applications/topics_extraction_with_nmf_lda.html#sphx-glr-auto-examples-applications-topics-extraction-with-nmf-lda-py).

## Dependencies

- `PyGithub` to fetch your stars. [install](http://pygithub.readthedocs.io/en/latest/introduction.html#download-and-install)
- `requests` to fetch readmes from github. [install](http://docs.python-requests.org/en/master/user/install/)
- `Markdown` to generate html from markdowns. [install](http://pythonhosted.org/Markdown/install.html)
- `BeautifulSoup`: extract text from generated html (easiest method to get plain text from markdown). [install](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-beautiful-soup)
- `scikit-learn` and the [scipy stack](https://www.scipy.org/install.html#installing-via-pip) for the machine learning algorithms (topic extraction, tf-idf vectors, etc.). [install](http://scikit-learn.org/stable/install.html)