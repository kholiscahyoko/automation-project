from urllib.request import urlopen
from lxml import etree

class GoalID:
    def __init__(self):
        self.url = "https://www.goal.com/id"
        self.htmlparser = etree.HTMLParser()
        self.result = {
            'url': self.url,
            'data': []
        }

    def process(self):
        response = urlopen(self.url)
        tree = etree.parse(response, self.htmlparser)

        for element in tree.xpath('//section[@card-group-type="TOP_STORIES"]/ol/li[@data-type="CardComponent"]/article'):
            #media image
            media_poster = element.xpath('.//div[@class="poster-wrapper"]/a/div/img')[0]
            img_src = media_poster.get("src")
            img_srcset = media_poster.get("srcset")
            img_sizes = media_poster.get("sizes")

            #media text and article url
            media_content = element.xpath('.//div[@class="content-wrapper"]/div[@class="content-body"]')[0]
            article_title = media_content.xpath('.//a/h3/span')[0].text.strip()
            article_url = media_content.xpath('.//a')[0].get("href")
            tags_elements = media_content.xpath('.//div[@data-testid="tags-list"]/a[@data-testid="single-tag"]')
            tags = []
            for tag_element in tags_elements:
                tags.append(tag_element.text.strip())
            self.result["data"].append({
                "img_src" : img_src,
                "img_srcset" : img_srcset,
                "img_sizes" : img_sizes,
                "tags" : tags,
                "article_url" : article_url,
                "article_title" : article_title
            })

