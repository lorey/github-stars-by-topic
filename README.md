# Your GitHub stars sorted by topic

This is a python script that fetches your GitHub stars and automatically extracts a given number of topics. It then generates a folder structure so you can easily browse through the topics in markdown.

The result can be viewed in the [example folder](example/).

## Usage

Just run `python3 main.py` on the command line. It will ask you for your GitHub credentials to fetch your stars and then do its job. The result will be a folder in the main directory that you can copy or save in a GitHub repository for others to browse.

## Dependencies

- `PyGithub` to fetch your stars. [install](http://pygithub.readthedocs.io/en/latest/introduction.html#download-and-install)
- `requests` to fetch readmes from github. [install](http://docs.python-requests.org/en/master/user/install/)
- `Markdown` to generate html from markdowns. [install](http://pythonhosted.org/Markdown/install.html)
- `BeautifulSoup`: extract text from generated html (easiest method to get plain text from markdown). [install](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-beautiful-soup)
- `scikit-learn` and the [scipy stack](https://www.scipy.org/install.html#installing-via-pip) for the machine learning algorithms (topic extraction, tf-idf vectors, etc.). [install](http://scikit-learn.org/stable/install.html)