import requests
import re
import time
from lxml import etree
import random


class DaZhongDianPing:
    def __init__(self, shop_review_url, user_cookie):
        # 商家评论详情页 url
        self.url = shop_review_url
        # 商家评论详情页源码
        self.html = str()
        # 页面字体大小
        self.font_size = 14
        # 页面引用的 css 文件
        self.css = str()
        # 商家地址使用的 svg 文件
        self.address_svg = str()
        # 商家电话使用的 svg 文件
        self.tell_svg = str()
        # 商家评论使用的 svg 文件
        self.review_svg = str()

        # 字体码表，key 为 class 名称，value 为对应的汉字
        self.address_font_map = dict()
        self.tell_font_map = dict()
        self.review_font_map = dict()

        # 商家评论的最大页码数
        self.max_pages = 0
        self.timeout = 10
        self.headers = {
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': self.url.replace('/review_all', ''),
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cookie': user_cookie
        }

    def get_svg_html(self):
        """
        获取商家详情页 svg 文件
        :return:
        """
        # 获取商家评论页内容
        index_res = requests.get(self.url, headers=self.headers, timeout=self.timeout)
        self.html = index_res.text
        if '验证中心' in index_res.text:
            print('遇到验证码，程序退出！')
            exit()

        # 提取最大页数
        tree = etree.HTML(self.html)
        self.max_pages = int(tree.xpath('//div[@class="reviews-pages"]/a/text()')[-2])

        # 正则匹配 css 文件 url
        result = re.search('<link rel="stylesheet" type="text/css" href="(//s3plus.*?)">', self.html, re.S)
        if result:
            css_url = 'http:' + result.group(1)
            headers = {
                'Proxy-Connection': 'keep-alive',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            css_res = requests.get(css_url, headers=headers)
            print(f'css_url:{css_url}')
            self.css = css_res.text

            # 正则匹配商家地址使用的 svg 文件 url
            result = re.search('bb\[class.*?background-image: url\((.*?)\);', self.css, re.S)
            address_svg_url = 'http:' + result.group(1)
            self.address_svg = requests.get(address_svg_url, headers=headers).text
            print(f'address_svg_url:{address_svg_url}')

            # 正则匹配商家电话号码使用的 svg 文件 url
            result = re.search('cc\[class.*?background-image: url\((.*?)\);', self.css, re.S)
            tell_svg_url = 'http:' + result.group(1)
            self.tell_svg = requests.get(tell_svg_url, headers=headers).text
            print(f'tell_svg_url:{tell_svg_url}')

            # 正则匹配评论使用的 svg 文件 url
            result = re.search('svgmtsi\[class.*?background-image: url\((.*?)\);', self.css, re.S)
            review_svg_url = 'http:' + result.group(1)
            self.review_svg = requests.get(review_svg_url, headers=headers).text
            print(f'review_svg_url:{review_svg_url}')

    def get_font_map(self):
        # <bb class="xxx.*?"></bb>              地址 css 样式
        # <cc class="xxx.*?"></cc>              电话 css 样式
        # <svgmtsi class="xxx.*?"></svgmtsi>    评论 css 样式
        # xxx 每天都会发生变化，所以动态匹配对应的前缀

        # 地址 css 前缀
        bb_result = re.search('<bb class="(.*?)"></bb>', self.html, re.S)
        address_prefix = bb_result.group(1)[:2]

        # 电话 css 前缀
        cc_result = re.search('<cc class="(.*?)"></cc>', self.html, re.S)
        tell_prefix = cc_result.group(1)[:2]

        # 评论 css 前缀
        svgmtsi_result = re.search('<svgmtsi class="(.*?)"></svgmtsi>', self.html, re.S)
        review_prefix = svgmtsi_result.group(1)[:2]

        """
        
        :return:
        """

        # 匹配 css 文件中格式为 .(css前缀.*?){background:(.*?)px (.*?)px;} ，获得所有 css 加密字符的 css 样式
        address_class_list = re.findall('\.(%s.*?){background:(.*?)px (.*?)px;}' % address_prefix, self.css, re.S)
        tell_class_list = re.findall('\.(%s.*?){background:(.*?)px (.*?)px;}' % tell_prefix, self.css, re.S)
        review_class_list = re.findall('\.(%s.*?){background:(.*?)px (.*?)px;}' % review_prefix, self.css, re.S)

        """
        匹配评论 svg 文件中格式为 <path id="(\d+)" d="M0 (\d+) H600"/> 的字段
        其中 id 的值对应 xlink:href="#(\d+)" 的值
        d="M0 (\d+) H600" 的值对应 background中 y轴的偏移量
        
        匹配评论 svg 文件中格式为 <textPath xlink:href="#(\d+)" textLength=".*?">(.*?)</textPath> 的字段
        (\d+) 对应为 css id 选择器，对应上面 <path> 中的 id
        (.*?) 对应一串中文字符串，
        还原后的字符 = 中文字符串[css 样式上中 x 的绝对值 / 字体大小]
        """
        review_svg_id_y_list = re.findall('<path id="(\d+)" d="M0 (\d+) H600"/>', self.review_svg, re.S)
        review_svg_id_fonts_dc = dict(
            re.findall('<textPath xlink:href="#(\d+)" textLength=".*?">(.*?)</textPath>', self.review_svg, re.S))
        self.review_font_map = self.review_class_to_font(review_class_list, review_svg_id_y_list,
                                                         review_svg_id_fonts_dc)

        address_svg_y_words_list = re.findall('<text x="0" y="(\d+)">(.*?)</text>', self.address_svg, re.S)
        self.address_font_map = self.address_class_to_font(address_class_list, address_svg_y_words_list)

        tell_svg_result = re.search('<text x="(.*?)" y=".*?">(.*?)</text>', self.tell_svg, re.S)
        tell_x_list = tell_svg_result.group(1).split(' ')
        tell_words_str = tell_svg_result.group(2)
        tell_svg_x_words_list = list(zip(tell_x_list, list(tell_words_str)))
        self.tell_font_map = self.tell_class_to_num(tell_class_list, tell_svg_x_words_list)

        print(self.address_font_map)
        print(self.review_font_map)
        print(self.tell_font_map)

    def address_class_to_font(self, class_list, y_words_list):
        tmp_dc = dict()
        for class_name, class_x, class_y in class_list:
            for text_y, words in y_words_list:
                if int(text_y) >= abs(int(float(class_y))):
                    index = abs(int(float(class_x))) // self.font_size
                    tmp_dc[class_name] = words[index]
                    break
        return tmp_dc

    def review_class_to_font(self, class_list, id_y_list, words_dc):
        tmp_dc = dict()
        for class_name, class_x, class_y in class_list:
            for class_id, y in id_y_list:
                if int(y) >= abs(int(float(class_y))):
                    word_index = abs(int(float(class_x))) // self.font_size
                    tmp_dc[class_name] = words_dc[class_id][int(word_index)]
                    break
        return tmp_dc

    def tell_class_to_num(self, class_list, x_word_list):
        tmp_dc = dict()
        for class_name, class_x, class_y in class_list:
            for x, word in x_word_list:
                if int(x) >= abs(int(float(class_x))):
                    tmp_dc[class_name] = word
                    break
        return tmp_dc

    def get_shop_info(self):
        # 将 self.html 商铺地址加密的 class 样式替换成对应的中文字符
        address_class_set = re.findall('<bb class="(.*?)"></bb>', self.html, re.S)
        for class_name in address_class_set:
            self.html = re.sub('<bb class="{}"></bb>'.format(class_name), self.address_font_map[class_name], self.html)

        # 将 self.html 电话号码加密的 class 样式替换成对应的数字
        tell_class_set = re.findall('<cc class="(.*?)"></cc>', self.html, re.S)
        for class_name in tell_class_set:
            self.html = re.sub('<cc class="{}"></cc>'.format(class_name), self.tell_font_map[class_name], self.html)

        tree = etree.HTML(self.html)
        shop_address = tree.xpath('//div[@class="address-info"]/text()')[0].replace('&nbsp;', '').replace('\n',
                                                                                                          '').replace(
            ' ', '')
        shop_tell = tree.xpath('//div[@class="phone-info"]/text()')[0].replace('&nbsp;', '').replace('\n', '').replace(
            ' ', '')
        print(f'地址：{shop_address}\n电话：{shop_tell}')

    def get_info(self):
        # 将 self.html 评论区域加密的 class 样式替换成对应的中文字符
        review_class_set = re.findall('<svgmtsi class="(.*?)"></svgmtsi>', self.html, re.S)
        for class_name in review_class_set:
            self.html = re.sub('<svgmtsi class="{}"></svgmtsi>'.format(class_name), self.review_font_map[class_name],
                               self.html)

        tree = etree.HTML(self.html)
        for i in tree.xpath('//div[@class="main-review"]'):
            user_name = i.xpath('./div[@class="dper-info"]/a/text()')[0].strip()
            star = int(
                re.search('sml-rank-stars sml-str(\d+) star', i.xpath('./div[@class="review-rank"]/span[1]/@class')[0],
                          re.S).group(1)) / 10
            evaluation_list = [i.strip() for i in
                               i.xpath('./div[@class="review-rank"]/span[@class="score"]/span/text()')]
            if len(evaluation_list) > 3:
                consumption_per_person = evaluation_list[-1].replace('人均：', '')
                evaluation_list = evaluation_list[:3]
            else:
                consumption_per_person = '无'
            review = i.xpath('string(./div[@class="review-words Hide"])').replace('收起评价', '').strip().replace(' ',
                                                                                                              '').replace(
                '⃣', '.').replace('\n', '')
            images_list = i.xpath('./div[@class="review-pictures"]/ul/li[@class="item"]/a/img/@data-big')
            review_time = i.xpath('./div[@class="misc-info clearfix"]/span[@class="time"]/text()')[0].strip()
            print('-------------------------------------')
            print(f'用户：{user_name}')
            print(f'星评：{star}')
            print(f'多维分数：{evaluation_list}')
            print(f'人均：{consumption_per_person}')
            print(f'评论：{review}')
            print(f'图片：{images_list}')
            print(f'评论时间：{review_time}')

    def run(self):
        self.get_svg_html()
        self.get_font_map()
        self.get_shop_info()
        self.get_info()


if __name__ == '__main__':
    url = 'http://www.dianping.com/shop/G9TSD2JvdLtA7fdm/review_all'
    user_cookie = ''
    dz = DaZhongDianPing(url, user_cookie)
    dz.run()
