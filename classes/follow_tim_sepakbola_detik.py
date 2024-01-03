import re
import json
from builtins import print
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import quote_plus
from lxml import etree
from pprint import pprint

class SepakbolaDetik:
    def __init__(self):
        self.base_url = "https://sport.detik.com/sepakbola"
        self.liga_url = "https://sport.detik.com/sepakbola/[liga-path]"
        self.team_url = "https://sport.detik.com/sepakbola/profil-tim/[liga_path]/[team_path]"
        self.squad_stat_url = "https://sport.detik.com/sepakbola/profil-tim/[liga_path]/[team_path]/statistik"
        self.player_url = "https://sport.detik.com/sepakbola/profil-pemain/[team_path]/[player_path]"
        self.htmlparser = etree.HTMLParser()
        self.liga_list_xpath = '//*[@id="wid_select_team"]/option'
        self.team_list_xpath = '//*[@id="liga_team"]/li[@class="nav__item liga_team_logo"]/a'
        self.player_list_xpath = '//*[@class="profile-stats__player"]/a'
        self.player_list_xpath_widget_pattern = '//div[starts-with(@d-params,"squad|[league-id]|")]'
        self.squad_api_url = "https://sport.detik.com/sepakbola/ajax/opta"
        self.result = {
            'url': self.base_url,
            'status': 0,
            'data': []
        }

    def process(self):
        response = urlopen(self.base_url)
        self.result["url"] = response.url
        self.result["status"] = response.status
        page_type = "base"
        self.checking(response, page_type)
        tree = etree.parse(response, self.htmlparser)
        results_example = {
            'nama-liga': {
                'label' : 'Nama Liga',
                'status': 404,
                'team_list': {
                    'arsenal': {
                        'label': 'Nama Tim',
                        'status': 404,
                        'player_list':{
                            'player_name': {
                                'label': 'Nama Pemain',
                                'status': 404
                            }
                        }
                    }
                }
            }
        }

        i = 0
        for element in tree.xpath(self.liga_list_xpath):
            liga_val = element.get("value")
            liga_label = element.text
            liga_url = "{}/{}".format(response.url, liga_val)
            liga_response = urlopen(liga_url)
            page_type = "liga : "+liga_label
            res = self.checking(liga_response, page_type)
            liga_result = {
                'url': liga_response.url,
                'status': liga_response.status,
                'data': []
            }
            if not res:
                continue
            print(liga_url)
            liga_tree = etree.parse(liga_response, self.htmlparser)

            for liga_element in liga_tree.xpath(self.team_list_xpath):
                team_label = liga_element.get("dtr-ttl")
                print(team_label)
                team_url = liga_element.get("href")+"/statistik"
                team_value = team_url.rsplit('/', 2)[-2]
                print(team_url)
                team_response = urlopen(team_url)
                page_type = "liga : "+liga_label+", team : "+team_label
                res = self.checking(team_response, page_type)
                team_result = {
                    'label': team_label,
                    'url': team_response.url,
                    'status': team_response.status,
                    'data': []
                }

                if not res:
                    continue
                team_tree = etree.parse(team_response, self.htmlparser)
                # print(team_url)
                squad_widget_xpath = re.sub("\[league-id\]", liga_val, self.player_list_xpath_widget_pattern)
                print(squad_widget_xpath)
                print('AFTER TEAM TREE')
                squad_widget_element = team_tree.xpath(squad_widget_xpath).pop()
                squad_param = squad_widget_element.get("d-params")
                print(squad_param)
                print(quote_plus(squad_param))
                squad_api_url = "{}?param={}".format(self.squad_api_url, quote_plus(squad_param))
                print(squad_api_url)
                squad_api_response = urlopen(squad_api_url)
                body = squad_api_response.read().decode()
                json_body = json.loads(body)
                api_squad_tree = etree.fromstring(json_body['html'], self.htmlparser)
                print('AFTER API SQUAD TREE')

                for team_element in api_squad_tree.xpath(self.player_list_xpath):
                    print('UNDER TEAM ELEMENT')
                    # continue;
                    player_label = team_element.text
                    player_url = team_element.get("href")
                    player_value = player_url.rsplit('/', 1)[-1]
                    player_response_url = player_url
                    player_response_status = 0
                    try:
                        player_response = urlopen(player_url)
                        player_response_url = player_response.url
                        player_response_status = player_response.status
                    except HTTPError as e:
                        print(e.__dict__)
                        player_response_status = 'HTTPError'
                        print('AFTER PLAYER HTTPERROR')
                    except URLError as e:
                        print(e.__dict__)
                        player_response_status = 'URLError'
                        print('AFTER PLAYER URLERROR')
                    except UnicodeEncodeError:
                        print('AFTER PLAYER UnicodeEncodeError')
                        player_response_status = 'UnicodeEncodeError'
                    page_type = "team : "+team_label+", player : "+player_label
                    # res = self.checking(player_response, page_type)
                    # if not res:
                    #     continue
                    player_result = {
                        'label': player_label,
                        'url': player_response_url,
                        'status': player_response_status
                    }
                    team_result["data"].append({
                        player_value : player_result
                    })
                liga_result["data"].append({
                    team_value : team_result
                })
            self.result["data"].append({
                liga_val : liga_result
            })
            print(liga_val)
            print(liga_label)
            print("\n")
            i += 1

    def checking(self, response, page_type):
        if(response.status != 200):
            print('Error found:')
            print('Page Type =', page_type)
            print('URL =', response.url)
            print('Status =', response.status)

            return False
        else:
            print('Page Type =', page_type, ':OK')
            return True