from os import path, listdir
from json import dumps

from flask import render_template, url_for, request, redirect
from markdown import markdown
import feedparser

from app import app

# Monkey Patching SSL cert verification for feedparser
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context
# End Monkey patch

APP_ROOT, _ = path.split(path.abspath(__file__))
FS_ROOT, _ = path.split(path.abspath(APP_ROOT))
NOTES = FS_ROOT + '/notes'


def path_to_dict(folder, parent='/'):
    _, html_path = path.split(folder)
    html_path = path.join(parent, html_path)
    ret = {'text': path.basename(folder)}
    if path.isdir(path.abspath(folder)):
        ret['type'] = 'directory'
        ret['children'] = sorted([path_to_dict(path.join(folder, x), html_path) for x in listdir(path.abspath(folder))],
                                 key=lambda x: x['type'])
    else:
        ret['type'] = 'file'
        ret['data'] = {'jstree' : {'icon': url_for('static', filename='img/file2.png')}}
        ret['a_attr'] = {'href': html_path}
    return ret


def search(search_string, item=NOTES, parent='/'):
    _, html_path = path.split(item)
    html_path = path.join(parent, html_path)
    ret = {}
    result = {}
    if path.isdir(path.abspath(item)):
        for x in listdir(path.abspath(item)):
            if search(search_string, path.join(item, x), html_path):
                ret.update(search(search_string, path.join(item, x), html_path))
    else:
        try:
            with open(item) as fp:
                raw = fp.readlines()
            for lineno, line in enumerate(raw):
                if search_string.upper() in line.upper():
                    result['link'] = html_path
                    _, result['title'] = path.split(item)
                    if lineno == 0:
                        result['context'] = ''.join(raw[lineno:lineno + 3])
                    elif lineno == len(raw):
                        result['context'] = ''.join(raw[lineno - 3:lineno])
                    else:
                        result['context'] = ''.join(raw[lineno - 1:lineno + 2])
                    return {result['title']: result}
        except IOError:
            pass
    return ret


@app.route('/')
@app.route('/index/', methods=['GET', 'POST'])
def index():
    jstree = dumps(path_to_dict(NOTES))
    return render_template('index.html', title="index", filename="index", jstree=jstree)


@app.route('/browser/')
def browse_main():
    jstree = dumps(path_to_dict(NOTES))
    return render_template('browser.html', jstree=jstree, titlebar="browser", title="browser" )


@app.route('/notes/<path:urlFilePath>')
def display_notes(urlFilePath):
    jstree = dumps(path_to_dict(NOTES))
    filename = path.join(FS_ROOT, 'notes', urlFilePath)
    try:
        with open(filename) as fp:
            content = markdown(fp.read(), extensions=['fenced_code', 'codehilite'])
        return render_template("file.html", markdown=content, titlebar=urlFilePath, jstree=jstree, title=urlFilePath)
    except FileNotFoundError:
        return render_template('error.html', errorpage=filename)


@app.route('/mdtojira')
def md_to_jira():
    return render_template('md_to_jira.html')


@app.route('/mdtojira/notes/<path:urlFilePath>')
def md_to_jira_notes(urlFilePath):
    filename = path.join(FS_ROOT, 'notes', urlFilePath)
    try:
        with open(filename) as fp:
            content = fp.read()
        return render_template("md_to_jira.html", markdown=content)
    except FileNotFoundError:
        return render_template('error.html', errorpage=filename)


@app.route('/search.html')
def search_results():
    jstree = dumps(path_to_dict(NOTES))
    query = request.args.get('q')
    if not query:
        redirect(url_for('index'))
    results = search(query)
    return render_template('results.html', jstree=jstree, results=results, query=query, title=f'Search results:{query}')

@app.route('/feed')
def rss_feed():
    feed = 'https://www.nasa.gov/rss/dyn/breaking_news.rss'
    myfeed = feedparser.parse(feed)

    print(myfeed)
    return 'Hello'
