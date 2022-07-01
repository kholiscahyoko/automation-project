# github action reference https://github.com/actions/setup-python
#from selenium import webdriver

from urllib.request import urlopen
from lxml import etree
import json

def main():
    # url = "https://sport.detik.com/sepakbola"
    url = "https://www.goal.com/id"
    response = urlopen(url)
    htmlparser = etree.HTMLParser()
    # xpathselector = '//div[@class="berita-utama mgb-12"]/div/article[@class="list-content__item column"]'
    xpathselector = '//section[@card-group-type="TOP_STORIES"]/ol/li[@data-type="CardComponent"]/article'
    tree = etree.parse(response, htmlparser)

    result = {
        'url' : url,
        'data' : []
    }

    for element in tree.xpath(xpathselector):
        # media_image = element.xpath('.//div/div[@class="media__image"]/a/span/img')[0]
        # media_text = element.xpath('.//div/div[@class="media__text"]/h2/a')[0]
        # result["data"].append({
        #     "image_url" : media_image.get("src"),
        #     "article_url" : media_text.get("href"),
        #     "label" : media_text.text.strip()
        # })
        #img src, img srcset, img sizes, content category, content url, content label
        #media image
        media_poster = element.xpath('.//div[@class="poster-wrapper"]/a/div/img')[0]
        img_src = media_poster.get("src")
        img_srcset = media_poster.get("srcset")
        img_sizes = media_poster.get("sizes")

        #media text and article url
        media_content = element.xpath('.//div[@class="content-wrapper"]/div[@class="content-body"]')[0]
        article_title = media_content.xpath('.//a/h3/span')[0].text.strip()
        # print(article_title)
        article_url = media_content.xpath('.//a')[0].get("href")
        tags_elements = media_content.xpath('.//div[@data-testid="tags-list"]/a[@data-testid="single-tag"]')
        tags = []
        for tag_element in tags_elements:
            tags.append(tag_element.text.strip())
        result["data"].append({
            "img_src" : img_src,
            "img_srcset" : img_srcset,
            "img_sizes" : img_sizes,
            "tags" : tags,
            "article_url" : article_url,
            "article_title" : article_title
        })

    with open("./data/goal_id.json", "w") as external_file:
        print(json.dumps(result), file=external_file)
        external_file.close()

main()