from urllib.request import urlopen
from lxml import etree

class TempoCo:
    def __init__(self):
        self.url = "https://www.tempo.co"
        self.htmlparser = etree.HTMLParser()
        self.result = {
            'url': self.url,
            'data': []
        }

    def process(self, limit = 0):
        response = urlopen(self.url)
        tree = etree.parse(response, self.htmlparser)

        i = 0
        for element in tree.xpath('//div[@class="card-box ft240 margin-bottom-sm"]'):
            #media image
            media_poster = element.xpath('.//figure/a/img')[0]
            img_src = media_poster.get("src")

            #media text and article url
            media_content = element.xpath('.//article')[0]
            article_title = media_content.xpath('.//h2/a')[0].text.strip()
            article_url = media_content.xpath('.//h2/a')[0].get("href")
            article_date = media_content.xpath('.//h4')[0].text.strip()
            tags = []
            self.result["data"].append({
                "img_src" : img_src,
                "article_date" : article_date,
                "article_url" : article_url,
                "article_title" : article_title
            })
            i += 1
            if i >= limit:
                break