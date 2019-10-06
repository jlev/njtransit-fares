import os
from requests_html import HTML

class PageCache(object):
    def __init__(self, dirname):
        self.dirname = dirname
        if not os.path.exists(dirname):
            os.mkdir(dirname)

    def get(self, filename):
        filepath = os.path.join(self.dirname, filename)
        # gets cached page from filename
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return HTML(html=f.read())

    def set(self, filename, body):
        filepath = os.path.join(self.dirname, filename)

        with open(filepath, 'w') as f:
            f.write(body.html)