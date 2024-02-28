import datetime
import hashlib
import json
import os
import re
import urllib.request
import urllib.parse
from urllib import parse
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlopen
import time
import concurrent.futures
import mysql.connector

from lxml import etree
from lxml import html

import htmlmin


class InfoPemiluNewProfilData:
    def __init__(self):
        self.mysql_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'info_pemilu',
        }
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
        self.main_data_path = './data/info_pemilu_calon/'
        self.main_data_path_profil = './data/info_pemilu_calon_profil/'
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
            response_calon_tetap = self.retry_urlopen(url=self.profil_urls[jenis_dewan],data_request=data_request,method='POST',max_retries=5,delay=10)
            print("Success! Status code:", response_calon_tetap.getcode())
            # Do something with the response...
        except HTTPError as e:
            print(f"HTTP ErrorA: {e.code} - {e.reason}")
            return None
        except Exception as e:
            print(f"ErrorA: {e}")
            return None

        response_body = response_calon_tetap.read().decode()
        tree = html.fromstring(response_body)
        matching_content = tree.find(".//div[@class='col-sm-12 col-md-12']")
        if matching_content is not None :
            min_html = re.sub(r'<!--(.*?)-->', '', htmlmin.minify(html.tostring(matching_content, encoding='unicode', method='html')), flags=re.DOTALL )
        else :
            min_html = None

        return min_html

    def clean_data(self, html_string, jenis_dewan):
        tree = html.fromstring(html_string)

        if jenis_dewan == "dpd" :
            table_class = 'table table-striped'
        else :
            table_class = 'table table-bordered'

        foto = ""

        ## RIWAYAT PEKERJAAN (array)
        riwayat_pekerjaan = []
        if(len(tree.xpath('//h3[text()="RIWAYAT PEKERJAAN"]'))>0):
            h3_riwayat_pekerjaan = tree.xpath('//h3[text()="RIWAYAT PEKERJAAN"]')[0]
            table_riwayat_pekerjaan = h3_riwayat_pekerjaan.xpath('following-sibling::table[@class="'+table_class+'"]')[0]
            headers = [th.text_content().strip() for th in table_riwayat_pekerjaan.xpath('.//thead/tr/th')]
            riwayat_pekerjaan.append(headers)

            rows = table_riwayat_pekerjaan.xpath('.//tbody/tr')
            for row in rows:
                row_data = [td.text_content().strip() for td in row.xpath('td')]
                if not all(cell == "-" for cell in row_data):
                    riwayat_pekerjaan.append(row_data)

        ## RIWAYAT PENDIDIKAN (array)
        riwayat_pendidikan = []
        if(len(tree.xpath('//h3[text()="RIWAYAT PENDIDIKAN"]'))>0):
            h3_riwayat_pendidikan = tree.xpath('//h3[text()="RIWAYAT PENDIDIKAN"]')[0]
            table_riwayat_pendidikan = h3_riwayat_pendidikan.xpath('following-sibling::table[@class="'+table_class+'"]')[0]
            headers = [th.text_content().strip() for th in table_riwayat_pendidikan.xpath('.//thead/tr/th')]
            riwayat_pendidikan.append(headers)

            rows = table_riwayat_pendidikan.xpath('.//tbody/tr')
            for row in rows:
                row_data = [td.text_content().strip() for td in row.xpath('td')]
                if not all(cell == "-" for cell in row_data):
                    riwayat_pendidikan.append(row_data)

        ## RIWAYAT KURSUS DAN DIKLAT (array)
        riwayat_kursus_diklat = []
        if(len(tree.xpath('//h3[text()="RIWAYAT KURSUS DAN DIKLAT"]'))>0):
            h3_riwayat_kursus_diklat = tree.xpath('//h3[text()="RIWAYAT KURSUS DAN DIKLAT"]')[0]
            table_riwayat_kursus_diklat = h3_riwayat_kursus_diklat.xpath('following-sibling::table[@class="'+table_class+'"]')[0]
            headers = [th.text_content().strip() for th in table_riwayat_kursus_diklat.xpath('.//thead/tr/th')]
            riwayat_kursus_diklat.append(headers)

            rows = table_riwayat_kursus_diklat.xpath('.//tbody/tr')
            for row in rows:
                row_data = [td.text_content().strip() for td in row.xpath('td')]
                if not all(cell == "-" for cell in row_data):
                    riwayat_kursus_diklat.append(row_data)

        ## RIWAYAT ORGANISASI (array)
        riwayat_organisasi = []
        if(len(tree.xpath('//h3[text()="RIWAYAT ORGANISASI"]'))>0):
            h3_riwayat_organisasi = tree.xpath('//h3[text()="RIWAYAT ORGANISASI"]')[0]
            table_riwayat_organisasi = h3_riwayat_organisasi.xpath('following-sibling::table[@class="'+table_class+'"]')[0]
            headers = [th.text_content().strip() for th in table_riwayat_organisasi.xpath('.//thead/tr/th')]
            riwayat_organisasi.append(headers)

            rows = table_riwayat_organisasi.xpath('.//tbody/tr')
            for row in rows:
                row_data = [td.text_content().strip() for td in row.xpath('td')]
                if not all(cell == "-" for cell in row_data):
                    riwayat_organisasi.append(row_data)

        ## RIWAYAT PENGHARGAAN (array)
        riwayat_penghargaan = []
        if(len(tree.xpath('//h3[text()="RIWAYAT PENGHARGAAN"]'))>0):
            h3_riwayat_penghargaan = tree.xpath('//h3[text()="RIWAYAT PENGHARGAAN"]')[0]
            table_riwayat_penghargaan = h3_riwayat_penghargaan.xpath('following-sibling::table[@class="'+table_class+'"]')[0]
            headers = [th.text_content().strip() for th in table_riwayat_penghargaan.xpath('.//thead/tr/th')]
            riwayat_penghargaan.append(headers)

            rows = table_riwayat_penghargaan.xpath('.//tbody/tr')
            for row in rows:
                row_data = [td.text_content().strip() for td in row.xpath('td')]
                if not all(cell == "-" for cell in row_data):
                    riwayat_penghargaan.append(row_data)

        data = {}
        if(jenis_dewan == "dpd") :

            ## FOTO
            if(len(tree.xpath('//img/@src'))):
                foto_src = tree.xpath('//img/@src')

                foto = urllib.parse.unquote(foto_src[0]) if len(foto_src)>0 else None

            ## DISABILITAS DPD (string)
            disabilitas = ""
            if(len(tree.xpath('//strong[text()="KETERANGAN DISABILITAS:"]'))):
                matching_disabilitas = tree.xpath('//strong[text()="KETERANGAN DISABILITAS:"]')[0]
                disabilitas = matching_disabilitas.tail.strip() if matching_disabilitas.tail else ""

            ## MOTIVASI DPD (string)
            motivasi = ""
            if(len(tree.xpath('//th[text()="MOTIVASI"]'))>0):
                matching_motivasi = tree.xpath('//th[text()="MOTIVASI"]')[0]
                motivasi = matching_motivasi.xpath('following-sibling::td/text()')[0].strip() if len(matching_motivasi) else ""

            if len(disabilitas) > 0 :
                data["disabilitas"] = disabilitas

        else :
            ## FOTO
            if(len(tree.xpath('//img'))>1):
                img_el = tree.xpath('//img')[1]
                foto = urllib.parse.unquote(img_el.attrib['src']) if len(img_el.attrib['src'])>0 else None

            # print(matching_foto)

            ## TANGGAL LAHIR (string)
            matching_tanggal_lahir = tree.xpath('//td[strong="Tanggal Lahir:"]/following-sibling::td/text()')
            tanggal_lahir = matching_tanggal_lahir[0].strip() if(len(matching_tanggal_lahir)>0) else ""

            ## TEMPAT LAHIR (string)
            matching_tempat_lahir = tree.xpath('//td[strong="Tempat Lahir:"]/following-sibling::td/text()')
            tempat_lahir = matching_tempat_lahir[0].strip() if(len(matching_tempat_lahir)>0) else ""

            ## AGAMA (string)
            matching_agama = tree.xpath('//td[strong="Agama:"]/following-sibling::td/text()')
            agama = matching_agama[0].strip() if(len(matching_agama)>0) else ""

            ## STATUS PERKAWINAN (string)
            matching_perkawinan = tree.xpath('//td[strong="Status Perkawinan:"]/following-sibling::td/text()')
            perkawinan = matching_perkawinan[0].strip() if(len(matching_perkawinan)>0) else ""

            ## DISABILITAS (string)
            matching_disabilitas = tree.xpath('//td[strong="Status Disabilitas:"]/following-sibling::td/text()')
            disabilitas = matching_disabilitas[0].strip() if(len(matching_disabilitas)>0) else ""

            ## PEKERJAAN (string)
            matching_pekerjaan = tree.xpath('//h3["PEKERJAAN"]/following-sibling::p/text()')
            pekerjaan = matching_pekerjaan[0].strip() if(len(matching_pekerjaan)>0) else ""

            ## STATUS HUKUM (string)
            matching_hukum = tree.xpath('//h3[text()="STATUS HUKUM"]/following-sibling::p[1]/text()')
            hukum = matching_hukum[0].strip() if(len(matching_hukum)>0) else ""

            ## ALAMAT (array)
            alamat = []
            if(len(tree.xpath('//h3[@class="mt-3" and text()="ALAMAT"]'))>0):
                h3_alamat = tree.xpath('//h3[@class="mt-3" and text()="ALAMAT"]')[0]
                li_elements = h3_alamat.xpath('following-sibling::li')
                alamat = [li_element.text_content().strip() for li_element in li_elements if li_element.text_content().strip().split(":")[1].strip() != "" ]

            ## PROGRAM USULAN (array)
            usulan = []
            if(len(tree.xpath('//h3[@class="mt-3" and text()="PROGRAM USULAN"]'))>0):
                h3_usulan = tree.xpath('//h3[@class="mt-3" and text()="PROGRAM USULAN"]')[0]
                li_elements = h3_usulan.xpath('following-sibling::li')
                usulan = [li_element.text_content().strip() for li_element in li_elements if li_element.text_content().strip().isdigit()]

            ## RIWAYAT PASANGAN (array)
            riwayat_pasangan = []
            if(len(tree.xpath('//h3[@class="mt-3" and text()="RIWAYAT PASANGAN"]'))>0):
                h3_riwayat_pasangan = tree.xpath('//h3[@class="mt-3" and text()="RIWAYAT PASANGAN"]')[0]
                table_riwayat_pasangan = h3_riwayat_pasangan.xpath('following-sibling::table[@class="table table-bordered"]')[0]
                headers = [th.text_content().strip() for th in table_riwayat_pasangan.xpath('.//thead/tr/th')]
                riwayat_pasangan.append(headers)

                rows = table_riwayat_pasangan.xpath('.//tbody/tr')
                for row in rows:
                    row_data = [td.text_content().strip() for td in row.xpath('td')]
                    if not all(cell == "-" for cell in row_data):
                        riwayat_pasangan.append(row_data)

            if len(tempat_lahir)> 0:
                data["tempat_lahir"] = tempat_lahir

            if len(tanggal_lahir)> 0:
                data["tanggal_lahir"] = tanggal_lahir

            if len(agama)> 0:
                data["agama"] = agama

            if len(perkawinan)> 0:
                data["perkawinan"] = perkawinan

            if len(pekerjaan)> 0:
                data["pekerjaan"] = pekerjaan

            if len(hukum)> 0:
                data["hukum"] = hukum

            if len(alamat)> 0:
                data["alamat"] = alamat

            if len(usulan)> 0:
                data["usulan"] = usulan

            if len(riwayat_pasangan)> 1:
                data["riwayat_pasangan"] = riwayat_pasangan


        if len(disabilitas) > 0:
            data["disabilitas"] = disabilitas

        if len(riwayat_pekerjaan) > 1 :
            data["riwayat_pekerjaan"] = riwayat_pekerjaan

        if len(riwayat_pendidikan) > 1 :
            data["riwayat_pendidikan"] = riwayat_pendidikan

        if len(riwayat_kursus_diklat) > 1 :
            data["riwayat_kursus_diklat"] = riwayat_kursus_diklat

        if len(riwayat_organisasi) > 1 :
            data["riwayat_organisasi"] = riwayat_organisasi

        if len(riwayat_penghargaan) > 1 :
            data["riwayat_penghargaan"] = riwayat_penghargaan


        return data, foto
    def retry_urlopen(self, url, data_request={}, method='GET', max_retries=3, delay=1):
        for attempt in range(max_retries):
            try:
                start = datetime.datetime.now()
                if(method == 'POST') :
                    response = urlopen(urllib.request.Request(
                        url,
                        data=data_request,
                        method='POST'
                    ))
                else :
                    response = urlopen(urllib.request.Request(
                        url
                    ))

                end = datetime.datetime.now()
                delta = end - start
                elapsed_seconds = round(delta.microseconds * .000001, 6)
                print(elapsed_seconds)
                # If successful, return the response
                return response
            except HTTPError as e :
                print(f"Attempt {attempt + 1} failed. HTTP ErrorB: {e.code} - {e.reason}")
                # Wait for a while before retrying
                time.sleep(delay)
            except Exception as e :
                print(f"Attempt {attempt + 1} failed. ErrorB: {e}")
                # Wait for a while before retrying
                time.sleep(delay * 3)

        # If all retries fail, raise the last encountered exception
        raise e

    def process_calon_in_loop(self, item, kode_dapil, directory_path, directory_path_profil, jenis_dewan):
        print(f"WORKER PROCESS CALON IN LOOP {kode_dapil}")
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

        save_dir = directory_path
        save_dir_profil = directory_path_profil
        kode_calon_index = len(item) - 1
        nama = item[nama_index]
        jenis_kelamin = item[jenis_kelamin_index]
        tempat_tinggal = item[tempat_tinggal_index]

        if (len(item[foto_index])) > 0:
            root_foto = html.fromstring(item[foto_index])
            foto_src = root_foto.xpath('//img/@src')
            foto = foto_src[0] if len(foto_src) > 0 else None
        else:
            foto = ""

        kode_calon = None
        id_parpol = ""
        if item[kode_calon_index].strip():
            root_kode_calon = html.fromstring(item[kode_calon_index])
            element_id_parpol = root_kode_calon.xpath(".//input[@name='id_parpol']/@value")
            id_parpol = element_id_parpol[0] if len(element_id_parpol) > 0 else None
            element_kode_calon = root_kode_calon.xpath(kode_calon_xpath)
            kode_calon = element_kode_calon[0] if len(element_kode_calon) > 0 else None


        logo_hex = None
        if (logo_index is not None):
            root_logo = html.fromstring(item[logo_index])
            logo_src = root_logo.xpath('//img/@src')
            logo = logo_src[0] if len(logo_src) > 0 else None
            logo_hex = hashlib.md5(logo.encode()).hexdigest() if len(logo_src) else None
        else:
            logo = ''

        root_nomor_urut = html.fromstring(item[nomor_urut_index])
        element_nomor_urut = root_nomor_urut.find(".//font")
        nomor_urut = element_nomor_urut.text if element_nomor_urut is not None else None

        if logo_hex is not None and len(logo_hex) > 0:
            filename = f"{kode_dapil}---{logo_hex}---{nomor_urut}"
        else:
            filename = f"{kode_dapil}---{nomor_urut}"

        json_file_path = os.path.join(save_dir, f"{filename}.json")

        if (os.path.isfile(json_file_path)):
            print(f"File '{json_file_path}' already exists, Skip")
            return

        # Establish a MySQL connection
        connection = mysql.connector.connect(**self.mysql_config)

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        try:
            # Construct and execute a SELECT query
            query = f"SELECT * FROM calons WHERE kode_dapil = %s AND foto = %s"
            query_data = (kode_dapil, foto)
            cursor.execute(query, query_data)

            # Fetch the result (assuming you expect only one row)
            result = cursor.fetchone()

            if result is not None:
                print(f"'{kode_dapil}--{nama}--{nomor_urut}' already exists in database, Skip")
                return
        finally:
            # Close the cursor and connection
            cursor.close()
            connection.close()


        if (kode_calon is not None):
            print(f"failed to check kode calon---")
            time.sleep(0.3)
            profil_body = self.get_profil(kode_calon=kode_calon, jenis_dewan=jenis_dewan, logo=logo)
            if (profil_body is not None):
                profil_data, foto_profil = self.clean_data(html_string=profil_body,
                                                    jenis_dewan=jenis_dewan)
                filename_foto_md5 = hashlib.md5(foto_profil.encode()).hexdigest()
                json_file_path_profil = os.path.join(save_dir_profil, f"{filename_foto_md5}.json")

                if (os.path.isfile(json_file_path_profil)):
                    print(f"{json_file_path_profil} already existed -- skip")
                    return

                calon_data_current = profil_data

                with open(json_file_path_profil, "w") as external_file:
                    external_file.write(json.dumps(calon_data_current))
                    external_file.close()
                print(f"File '{json_file_path_profil}' write profil data")
            else :
                kode_calon = ""


        calon_data_current = {
            "kode_dapil": kode_dapil,
            "logo": logo,
            "id_parpol": id_parpol,
            "nomor_urut": nomor_urut,
            "foto": foto,
            "nama": nama,
            "jenis_kelamin": jenis_kelamin,
            "tempat_tinggal": tempat_tinggal,
            "kode_calon": kode_calon,
        }

        # print(calon_data_current)
        # exit()

        with open(json_file_path, "w") as external_file:
            external_file.write(json.dumps(calon_data_current))
            external_file.close()
            print(f"File '{json_file_path}' write calon data")

    def process_calon(self, dapil_data, jenis_dewan = 'dpd', is_tetap = True):
        # if(dapil_data["kode_dapil"] <= '520104') :
        #     return
        kode_dapil = dapil_data["kode_dapil"] if "kode_dapil" in dapil_data else dapil_data["kode_pro"]
        if(is_tetap) :
            url_calon = self.calon_tetap_urls[jenis_dewan]
            directory_path = f"{self.main_data_path}{jenis_dewan}/dct/{kode_dapil}/"
            directory_path_profil = f"{self.main_data_path_profil}{jenis_dewan}/dct/{kode_dapil}/"

        else :
            url_calon = self.calon_sementara_urls[jenis_dewan]
            directory_path = f"{self.main_data_path}{jenis_dewan}/dcs/{kode_dapil}/"

        config = self.configs[jenis_dewan] if jenis_dewan in self.configs else self.configs["other"]

        url = url_calon + f"?{config['calon_list']}={kode_dapil}"
        try:
            print(f"TRYING TO MAKE REQUEST TO : {url}")
            response_calon = self.retry_urlopen(url=url,max_retries=10,delay=5)
        except HTTPError as e :
            print(f"HTTP ErrorC: {e.code} - {e.reason}")
            return
        except Exception as e :
            print(f"ErrorC: {e}")
            return

        print(f"Error Code : {response_calon.code}")

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        if not os.path.exists(directory_path_profil):
            os.makedirs(directory_path_profil)

        try:
            response_data = json.loads(response_calon.read().decode())["data"]
        except Exception as e :
            print(f"ErrorD: {e}")
            return

        pool = concurrent.futures.ThreadPoolExecutor(max_workers=20)

        for item in response_data :
            # self.process_calon_in_loop(item = item, kode_dapil = kode_dapil, directory_path = directory_path, directory_path_profil = directory_path_profil, jenis_dewan = jenis_dewan)
            pool.submit(self.process_calon_in_loop, item=item, kode_dapil=kode_dapil, directory_path=directory_path, directory_path_profil=directory_path_profil, jenis_dewan=jenis_dewan)

        pool.shutdown(wait=True)

    def process(self, jenis_dewan='dpd'):
        url_opt = self.dapil_opt[jenis_dewan]

        try:
            print(f"TRYING TO MAKE REQUEST TO : {url_opt}")
            response_opt = self.retry_urlopen(url=url_opt,max_retries=10,delay=10)
        except HTTPError as e:
            print(f"HTTP ErrorE: {e.code} - {e.reason}")
            return
        except Exception as e:
            print(f"ErrorE: {e}")
            return

        for item in json.loads(response_opt.read().decode())["data"] :
            # self.process_calon(item, jenis_dewan=jenis_dewan, is_tetap=False)
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
