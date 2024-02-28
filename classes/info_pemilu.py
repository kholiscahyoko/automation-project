import hashlib
import json
import os
import re
import urllib.request
from urllib import parse
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlopen

from lxml import etree
from lxml import html

import htmlmin


class InfoPemilu:
    def __init__(self):
        self.dapil_opt = {
            'dpd' : "https://infopemilu.kpu.go.id/Pemilu/Dct_dpd/GetDapilOptions",
            'dpr' : "https://infopemilu.kpu.go.id/Pemilu/Dct_dpr/GetDapilOptions_dprri",
            'dprdp' : "https://infopemilu.kpu.go.id/Pemilu/Dct_dprprov/GetDapilOptions_dprprov",
            'dprdk' : "https://infopemilu.kpu.go.id/Pemilu/Dct_dprd/GetDapilOptions_dprdkabko"
        }
        self.calon_tetap_urls = {
            'dpd': "https://infopemilu.kpu.go.id/Pemilu/Dct_dpd/dct_dpd",
            'dpr': "https://infopemilu.kpu.go.id/Pemilu/Dct_dpr/Dct_dpr",
            'dprdp': "https://infopemilu.kpu.go.id/Pemilu/Dct_dprprov/Dct_dprprov",
            'dprdk': "https://infopemilu.kpu.go.id/Pemilu/Dct_dprd/Dct_dprdkabko"
        }
        self.calon_sementara_urls = {
            'dpd': "https://infopemilu.kpu.go.id/Pemilu/Dcs_dpd/Dcs_dpd",
            'dpr': "https://infopemilu.kpu.go.id/Pemilu/Dcs_dpr/Dcs_dpr",
            'dprdp': "https://infopemilu.kpu.go.id/Pemilu/Dcs_dprprov/Dcs_dprprov",
            'dprdk': "https://infopemilu.kpu.go.id/Pemilu/Dcs_dprd/Dcs_dprdkabko"
        }
        self.profil_urls = {
            'dpd': "https://infopemilu.kpu.go.id/Pemilu/Dct_dpd/profil",
            'dpr': "https://infopemilu.kpu.go.id/Pemilu/Dct_dpr/profile",
            'dprdp': "https://infopemilu.kpu.go.id/Pemilu/Dct_dprprov/profile",
            'dprdk': "https://infopemilu.kpu.go.id/Pemilu/Dct_dprd/profile"
        }
        self.configs = {
            'dpd' : {
                'calon_list' : "kode_pro",
                'calon_profil' : {
                    'key': 'ID_CANDIDATE',
                    'other': {
                        'pilihan_publikasi' : 'BERSEDIA'
                    }
                }
            },
            'other' : {
                'calon_list': "kode_dapil",
                'calon_profil': {
                    'key': 'id_calon_dpr',
                    'other' : {
                        'logo_partai' : '',
                        'status_publikasi' : 'Bersedia',
                        'pilihan_publikasi' : ''
                    }
                }
            }
        }
        self.main_data_path = './data/info_pemilu/'
        self.url_opt = "https://infopemilu.kpu.go.id/Pemilu/Dct_dprprov/GetDapilOptions_dprprov"
        self.result_opt = {
            'data': []
        }

    def get_profil(self, kode_calon = None, jenis_dewan = 'dpd', logo = None) :

        if jenis_dewan == 'dpd' :
            data_request = self.configs['dpd']['calon_profil']['other']
            key = self.configs['dpd']['calon_profil']['key']
        else :
            data_request = self.configs['other']['calon_profil']['other']
            key = self.configs['other']['calon_profil']['key']
            if(logo is not None) :
                data_request['logo_partai'] = re.sub('^\.\./', '-', logo)

        data_request[key] = kode_calon
        data_request = urllib.parse.urlencode(data_request).encode('utf-8')
        try:
            response_calon_tetap = urlopen(urllib.request.Request(
                self.profil_urls[jenis_dewan],
                data=data_request,
                method='POST'
            ))
        except HTTPError as e :
            print(f"HTTP Error: {e.code} - {e.reason}")
            exit()
            return None
        except Exception as e :
            print(f"Error: {e}")
            exit()
            return None

        response_body = response_calon_tetap.read().decode()
        tree = html.fromstring(response_body)
        matching_content = tree.find(".//div[@class='top-products-area mt-2']")
        if matching_content is not None :
            min_html = re.sub(r'<!--(.*?)-->', '', htmlmin.minify(html.tostring(matching_content, encoding='unicode', method='html')), flags=re.DOTALL )
        else :
            min_html = None

        return min_html

    def process_calon(self, dapil_data, jenis_dewan = 'dpd', is_tetap = True):
        if(dapil_data["kode_dapil"] <= '710602') :
        # if(dapil_data["kode_dapil"] <= '967103') :
            return
        kode_dapil = dapil_data["kode_dapil"] if "kode_dapil" in dapil_data else dapil_data["kode_pro"]
        # print(kode_dapil)
        # exit()
        if(is_tetap) :
            url_calon = self.calon_tetap_urls[jenis_dewan]
            directory_path = f"{self.main_data_path}{jenis_dewan}/dct/{kode_dapil}/"
            directory_no_calon_id_path = f"{self.main_data_path}{jenis_dewan}/no_calon_id/dct/{kode_dapil}/"

        else :
            url_calon = self.calon_sementara_urls[jenis_dewan]
            directory_path = f"{self.main_data_path}{jenis_dewan}/dcs/{kode_dapil}/"
            directory_no_calon_id_path = f"{self.main_data_path}{jenis_dewan}/no_calon_id/dcs/{kode_dapil}/"

        config = self.configs[jenis_dewan] if jenis_dewan in self.configs else self.configs["other"]

        url = url_calon + f"?{config['calon_list']}={kode_dapil}"
        # print(url)
        # exit()
        try:
            print(f"TRYING TO MAKE REQUEST TO : {url}")
            response_calon = urlopen(url)
        except HTTPError as e :
            print(f"HTTP Error: {e.code} - {e.reason}")
            return
        except Exception as e :
            print(f"Error: {e}")
            return

        print(f"Error Code : {response_calon.code}")

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        if not os.path.exists(directory_no_calon_id_path):
            os.makedirs(directory_no_calon_id_path)

        if jenis_dewan == 'dpd' :
            kode_calon_xpath = ".//input[@name='ID_CANDIDATE']/@value"
            logo_index = None
            nomor_urut_index = 1
            foto_index = 2
            nama_index = 3
            jenis_kelamin_index = 4
            tempat_tinggal_index = 5
        else :
            kode_calon_xpath = ".//input[@name='id_calon_dpr']/@value"
            logo_index = 0
            nomor_urut_index = 2
            foto_index = 3
            nama_index = 4
            jenis_kelamin_index = 5
            tempat_tinggal_index = 6

        try:
            response_data = json.loads(response_calon.read().decode())["data"]
        except Exception as e :
            print(f"Error: {e}")
            return

        for item in response_data :
            save_dir = directory_path
            kode_calon_index = len(item) - 1
            nama = item[nama_index]

            if(len(item[foto_index])) > 0 :
                root_foto = html.fromstring(item[foto_index])
                foto_src = root_foto.xpath('//img/@src')
                foto = foto_src[0] if len(foto_src)>0 else None
            else :
                foto = ""

            kode_calon = None
            id_parpol = ""
            if item[kode_calon_index].strip():
                root_kode_calon = html.fromstring(item[kode_calon_index])
                element_id_parpol = root_kode_calon.xpath(".//input[@name='id_parpol']/@value")
                id_parpol = element_id_parpol[0] if len(element_id_parpol) > 0 else None
                element_kode_calon = root_kode_calon.xpath(kode_calon_xpath)
                kode_calon = element_kode_calon[0] if len(element_kode_calon) > 0 else None

            use_ori_id_calon = True
            if(kode_calon is not None and len(kode_calon)>100) :
                kode_calon = None
            if(kode_calon is None) :
                parsed_foto = urlparse(foto)
                path_segments = parsed_foto.path.split('/')
                calon_segment_index = path_segments.index('calon') if 'calon' in path_segments else None

                if calon_segment_index is not None and calon_segment_index + 1 < len(path_segments):
                    kode_calon = path_segments[calon_segment_index + 1]
                if(kode_calon is None):
                    use_ori_id_calon = False
                    save_dir = directory_no_calon_id_path
                    if len(foto)> 0 :
                        kode_calon = re.sub('[^0-9a-zA-Z]+', '-', foto)
                    else :
                        kode_calon = re.sub('[^0-9a-zA-Z]+', '-', nama)
                    kode_calon = f"{kode_dapil}---{kode_calon if len(kode_calon) < 32 else hashlib.md5(kode_calon.encode()).hexdigest()}"

            # print(kode_calon)
            # exit()

            json_file_path = os.path.join(save_dir, f"{kode_calon}.json")

            if(os.path.isfile(json_file_path)):
                print(f"File '{json_file_path}' already exists, Skip")
                continue


            if(logo_index is not None) :
                root_logo = html.fromstring(item[logo_index])
                logo_src = root_logo.xpath('//img/@src')
                logo = logo_src[0] if len(logo_src)>0 else None
            else :
                logo = ''

            root_nomor_urut = html.fromstring(item[nomor_urut_index])
            element_nomor_urut = root_nomor_urut.find(".//font")
            nomor_urut = element_nomor_urut.text if element_nomor_urut is not None else None

            print(kode_dapil + "--" + nama)

            jenis_kelamin = item[jenis_kelamin_index]

            tempat_tinggal = item[tempat_tinggal_index]

            # data_request = {'ID_CANDIDATE': kode_calon, 'pilihan_publikasi': 'BERSEDIA'}
            # print("AFTER INIT DATA REQUEST")
            # data_request = urllib.parse.urlencode(data_request).encode('utf-8')
            # print("AFTER ENCODE DATA REQUEST")
            # request = urllib.request.Request(self.url_calon_profil, data=data_request, method='POST')
            # print("AFTER MAKE REQUEST")
            # response_calon_tetap = urlopen(request)
            # print("AFTER DO REQUEST")
            # tree = etree.parse(response_calon_tetap, self.htmlparser)
            # print("AFTER TREE PARSING")
            # matching_element = tree.xpath("//strong[text()='KETERANGAN DISABILITAS:']/following-sibling::text()")
            # # matching_element = tree.xpath("//strong")
            # # print(matching_element)
            # # exit()
            # disabilitas = None
            # if matching_element :
            #     disabilitas = matching_element[0].strip()
            #
            # # print(disabilitas)
            # # exit()
            #
            # tables = tree.findall(".//table")
            # motivasi = None
            # riwayat_pekerjaan = {}
            # riwayat_pendidikan = {}
            # riwayat_organisasi = {}
            # riwayat_kursus_diklat = {}
            # riwayat_penghargaan = {}
            # if len(tables) > 1 :
            #     # for table in tables[2:] :
            #     headers = [th.text.strip() for th in tables[2].find(".//thead/tr").findall("th")]
            #     # table_data = []
            #     for row in tables[2].find(".//tbody").findall("tr"):
            #         row_data = {}
            #         for index, cell in enumerate(row.findall("td")):
            #             row_data[headers[index]] = cell.text.strip()
            #         riwayat_pekerjaan.append(row_data)
            #
            #     headers = [th.text.strip() for th in tables[3].find(".//thead/tr").findall("th")]
            #     # table_data = []
            #     for row in tables[3].find(".//tbody").findall("tr"):
            #         row_data = {}
            #         for index, cell in enumerate(row.findall("td")):
            #             row_data[headers[index]] = cell.text.strip()
            #         riwayat_pendidikan.append(row_data)
            #
            #     headers = [th.text.strip() for th in tables[4].find(".//thead/tr").findall("th")]
            #     # table_data = []
            #     for row in tables[4].find(".//tbody").findall("tr"):
            #         row_data = {}
            #         for index, cell in enumerate(row.findall("td")):
            #             row_data[headers[index]] = cell.text.strip()
            #         riwayat_organisasi.append(row_data)
            #
            #     headers = [th.text.strip() for th in tables[5].find(".//thead/tr").findall("th")]
            #     # table_data = []
            #     for row in tables[5].find(".//tbody").findall("tr"):
            #         row_data = {}
            #         for index, cell in enumerate(row.findall("td")):
            #             row_data[headers[index]] = cell.text.strip()
            #         riwayat_kursus_diklat.append(row_data)
            #
            #     headers = [th.text.strip() for th in tables[6].find(".//thead/tr").findall("th")]
            #     # table_data = []
            #     for row in tables[6].find(".//tbody").findall("tr"):
            #         row_data = {}
            #         for index, cell in enumerate(row.findall("td")):
            #             row_data[headers[index]] = cell.text.strip()
            #         riwayat_penghargaan.append(row_data)


            # if(use_ori_id_calon) :
            #     profil_body = self.get_profil(kode_calon=kode_calon, jenis_dewan=jenis_dewan, logo=logo)
            # else :
            #     profil_body = None

            calon_data_current = {
                "kode_dapil" : kode_dapil,
                "logo" : logo,
                "id_parpol" : id_parpol,
                "nomor_urut" : nomor_urut,
                "foto" : foto,
                "nama" : nama,
                "jenis_kelamin" : jenis_kelamin,
                "tempat_tinggal" : tempat_tinggal,
                "kode_calon" : kode_calon,
                # "profil_body" : profil_body,
                # "disabilitas" : disabilitas,
                # "riwayat_pekerjaan" : riwayat_pekerjaan,
                # "riwayat_pendidikan" : riwayat_pendidikan,
                # "riwayat_organisasi" : riwayat_organisasi,
                # "riwayat_kursus_diklat" : riwayat_kursus_diklat,
                # "riwayat_penghargaan" : riwayat_penghargaan
            }

            # print(calon_data_current)
            # exit()

            with open(json_file_path, "w") as external_file:
                external_file.write(json.dumps(calon_data_current))
                external_file.close()

    def process(self, jenis_dewan='dpd'):
        url_opt = self.dapil_opt[jenis_dewan]

        try:
            print(f"TRYING TO MAKE REQUEST TO : {url_opt}")
            response_opt = urlopen(url_opt)
        except HTTPError as e:
            print(f"HTTP Error: {e.code} - {e.reason}")
            return
        except Exception as e:
            print(f"Error: {e}")
            return

        for item in json.loads(response_opt.read().decode())["data"] :
            self.process_calon(item, jenis_dewan=jenis_dewan, is_tetap=False)
            self.process_calon(item, jenis_dewan=jenis_dewan, is_tetap=True)
            self.result_opt["data"].append({
                "kode_dapil" : item["kode_dapil"] if "kode_dapil" in item else item["kode_pro"],
                "nama_dapil" : item["nama_dapil"] if "nama_dapil" in item else item["nama_wilayah"]
            })

        directory_path = f"{self.main_data_path}{jenis_dewan}/"

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        json_file_path = os.path.join(directory_path, 'dapil.json')

        with open(json_file_path, "w") as external_file:
            external_file.write(json.dumps(self.result_opt["data"]))
            external_file.close()
