# Your GitHub stars sorted by topic

This is a python script that fetches your GitHub stars and automatically extracts a given number of topics. It then generates a folder structure so you can easily browse through the topics in markdown.

The result can be viewed in [example](example/).

## Usage

Just run `python3 main.py` on the command line. It will ask you for your GitHub credentials to fetch your stars and then do its job. The result will be a folder in the main directory that you can copy or save in a GitHub repository for others to browse.

## Dependencies

- `PyGithub` ([install](http://pygithub.readthedocs.io/en/latest/introduction.html#download-and-install))to fetch your stars
- `requests` ((install)[http://docs.python-requests.org/en/master/user/install/])to fetch readmes from github
- `Markdown` ((install)[http://pythonhosted.org/Markdown/install.html])and `BeautifulSoup` ([install](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-beautiful-soup)) to extract text from markdowns
- `scikit-learn` ([install](http://scikit-learn.org/stable/install.html)) and the [scipy stack](https://www.scipy.org/install.html#installing-via-pip) for the machine learning algorithms (topic extraction, tf-idf vectors, etc.)