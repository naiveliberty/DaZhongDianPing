import requests
from lxml import etree
import re
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import numpy
import os
from woff2tff import woff_to_ttf


class DaZhongDianPing():
    def __init__(self):
        self.url = "http://www.dianping.com/shenzhen/ch10/g117"
        # 页面 html
        self.html = None
        # 页面引用的 css 文件
        self.css = None
        self.woff_dc = dict()
        self.address_font_map = dict()
        self.shop_num_font_map = dict()
        self.tag_name_font_map = dict()
        self.referer = self.url.replace('/review_all', '')
        self.timeout = 10
        self.headers = {
              'Connection': 'keep-alive',
              'Pragma': 'no-cache',
              'Cache-Control': 'no-cache',
              'Upgrade-Insecure-Requests': '1',
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
              'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
              'Accept-Language': 'zh-CN,zh;q=0.9',
              'Cookie': ''
        }

    def get_woffs(self):
        html_res = requests.get(self.url, headers=self.headers)
        self.html = html_res.text
        result = re.search('<link rel="stylesheet" type="text/css" href="//s3plus(.*?)">', self.html, re.S)

        if result:
            css_url = 'http://s3plus' + result.group(1)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'
            }
            css_res = requests.get(css_url, headers=headers)
            print(css_url)
            self.css = css_res.text

            result = re.findall('@font-face\{font-family: "(.*?)";.*?,url\("(.*?)"\);\}', self.css)
            print(result)

            self.woff_dc = dict(result)
            for woff_url in result:
                url = 'http:' + woff_url[1]
                res = requests.get(url, headers=headers)
                filename = woff_url[1].split('/')[-1]
                filepath = f'./woff_file/{filename}'
                with open(filepath, 'wb') as f:
                    f.write(res.content)
                self.woff_dc[woff_url[0]] = filepath
            print(self.woff_dc)

    def get_woff_2_ttf(self):
        tmp_dc = self.woff_dc
        for key in tmp_dc:
            woff_path = tmp_dc[key]
            ttf_filepath = woff_path.replace('.woff', '.ttf')
            woff_to_ttf([woff_path, ttf_filepath])
            self.woff_dc[key] = ttf_filepath
        print(self.woff_dc)

    def fontConvert(self, fontPath):
        fonts = TTFont(fontPath)
        codeList = fonts.getGlyphOrder()[2:]
        im = Image.new("RGB", (1800, 1000), (255, 255, 255))
        dr = ImageDraw.Draw(im)
        font = ImageFont.truetype(font=os.path.abspath(fontPath), size=40)
        count = 18
        arrayList = numpy.array_split(codeList, count)
        for t in range(count):
            newList = [i.replace("uni", "\\u") for i in arrayList[t]]
            text = "".join(newList)
            text = text.encode('utf-8').decode('unicode_escape')
            dr.text((0, 50 * t), text, font=font, fill="#000000")
        im.save("font.jpg")
        im = Image.open("font.jpg")
        result = pytesseract.image_to_string(im, lang="chi_sim")
        result = result.replace(" ", "").replace("\n", "")
        codeList = [i.replace("uni", "&#x") + ";" for i in codeList]
        return dict(zip(codeList, list(result)))

    def get_font_map(self):
        for key in self.woff_dc:
            if 'shopNum' in key:
                self.shop_num_font_map = self.fontConvert(self.woff_dc[key])
            elif 'address' in key:
                self.address_font_map = self.fontConvert(self.woff_dc[key])
            elif 'tagName' in key:
                self.tag_name_font_map = self.fontConvert(self.woff_dc[key])

    def get_shop_info(self):
        shopNum_res = re.findall('<svgmtsi class="shopNum">(.*?)</svgmtsi>', self.html, re.S)
        for i in shopNum_res:
            self.html = re.sub('<svgmtsi class="shopNum">{}</svgmtsi>'.format(i), self.shop_num_font_map[i], self.html)

        address_res = re.findall('<svgmtsi class="address">(.*?)</svgmtsi>', self.html, re.S)
        for i in address_res:
            self.html = re.sub('<svgmtsi class="address">{}</svgmtsi>'.format(i), self.address_font_map[i], self.html)

        tagName = re.findall('<svgmtsi class="tagName">(.*?)</svgmtsi>', self.html, re.S)
        for i in tagName:
            self.html = re.sub('<svgmtsi class="tagName">{}</svgmtsi>'.format(i), self.tag_name_font_map[i], self.html)

        tree = etree.HTML(self.html)
        shop_title_list = tree.xpath('//div[@class="tit"]/a/h4/text()')
        shop_star_score = tree.xpath('//div[@class="comment"]/div/div[2]/text()')
        shop_review_nums = tree.xpath('//div[@class="comment"]/a[1]/b/text()')
        shop_mean_price = tree.xpath('//div[@class="comment"]/a[2]/b/text()')
        shop_tag = tree.xpath('//div[@class="tag-addr"]/a[1]/span/text()')
        shop_address_tag = tree.xpath('//div[@class="tag-addr"]/a[2]/span/text()')
        shop_adress_des = tree.xpath('//div[@class="tag-addr"]/span/text()')
        shop_taste_score = tree.xpath('//span[@class="comment-list"]/span[1]/b/text()')
        shop_environment_score = tree.xpath('//span[@class="comment-list"]/span[2]/b/text()')
        shop_server_score = tree.xpath('//span[@class="comment-list"]/span[3]/b/text()')
        shop_recommend_dishes = tree.xpath('//div[@class="recommend"]/a/text()')

        print(shop_title_list)
        print(shop_star_score)
        print(shop_review_nums)
        print(shop_mean_price)
        print(shop_tag)
        print(shop_address_tag)
        print(shop_adress_des)
        print(shop_taste_score)
        print(shop_environment_score)
        print(shop_server_score)
        print(shop_recommend_dishes)

    def run(self):
        self.get_woffs()
        self.get_woff_2_ttf()
        self.get_font_map()
        self.get_shop_info()


if __name__ == '__main__':
    dz = DaZhongDianPing()
    dz.run()
