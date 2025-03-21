import json
import requests
from bs4 import BeautifulSoup
import re


def remove_symbols_and_spaces(input_string):
    pattern = re.compile(r'[\u4e00-\u9fa5a-zA-Z0-9]+')
    # 找到所有符合条件的子字符串
    matches = pattern.findall(input_string)
    # 将结果拼接成一个字符串返回
    return ''.join(matches)


def extract_before_first_space(long_title):
    # 找到第一个空格的位置
    space_index = long_title.find(' ')
    # 如果没有空格，则返回原字符串；否则返回空格前的内容
    if space_index == -1:
        return long_title
    else:
        return long_title[:space_index]

def optimize_desc_string(input_str):
    # 移除多余的空白字符和换行符
    optimized_str = input_str.strip()
    # 替换多个连续的空格为一个空格
    optimized_str = ' '.join(optimized_str.split())
    # 移除特殊字符 \u3000
    optimized_str = optimized_str.replace('\u3000', '')
    # 移除多余的换行符
    optimized_str = optimized_str.replace('\n', ' ')
    optimized_str = optimized_str.replace('©豆瓣', '')
    return optimized_str


class DouBan(object):
    def __init__(self, headers):
        self.headers = headers
        self.add_year = 1  # 由于年份可能存在差异，误差设为+-1
        self.movie_info = {}
        self.search_list = []
        self.total = -1
        self.notes = None
        self.id = None
        self.year = None

    def get_search_list_by_api(self, input_title):
        url = 'https://movie.douban.com/j/subject_suggest?q={}'.format(input_title)
        res = requests.get(url=url, headers=self.headers)
        if res.status_code not in [200, 201]:
            raise Exception(f'status_code {res.status_code}')
        if '有异常请求从你的 IP 发出，点击下方按钮继续' in res.text:
            raise Exception('有异常请求从你的 IP 发出，点击下方按钮继续（请登录豆瓣后，填写相关的User-Agent 和 Cookie）')
        self.search_list = res.json()
        self.total = len(self.search_list)

    def get_search_list_by_js(self, input_title):
        """获取搜索数据"""
        url = f'https://search.douban.com/movie/subject_search?search_text={input_title}&cat=1002'
        res = requests.get(url, headers=self.headers)
        if res.status_code not in [200, 201]:
            raise Exception(f'status_code {res.status_code}')
        if '有异常请求从你的 IP 发出，点击下方按钮继续' in res.text:
            raise Exception('有异常请求从你的 IP 发出，点击下方按钮继续（请登录豆瓣后，填写相关的User-Agent 和 Cookie）')
        # 查找第一个<script type="text/javascript">...</script>标签对内的所有内容
        script_match = re.search(r'<script\s+type="text/javascript">\s*(.*?)</script>', res.text, re.DOTALL)
        if script_match:
            script_content = script_match.group(1)
            # 从找到的第一个<script>标签的内容中提取window.__DATA__部分
            data_match = re.search(r'window\.__DATA__\s*=\s*(.*?);', script_content)
            if data_match:
                json_str = data_match.group(1)
                # 将提取到的JSON字符串转换为Python对象
                data = json.loads(json_str)
                for d in data['items']:
                    all_title_str = d['title']
                    space_index = all_title_str.find(' ')
                    title = all_title_str[0: space_index].replace('\u200e', '')
                    if title:
                        year = all_title_str[-5: -1]
                        info = {'title': title, 'year': year, 'id': d['id']}
                        self.search_list.append(info)
                # print(self.search_list)
                if self.search_list:
                    self.total = len(self.search_list)
            else:
                raise Exception("未找到window.__DATA__的数据")
        else:
            raise Exception("未找到<script>标签")

    def choice_best_from_search_list(self, input_title, year=None):
        """从搜索出的结果数据中选择一个最相似的,2种情况，3种结果 """
        new_title = remove_symbols_and_spaces(input_title)
        result_new_title_list = [remove_symbols_and_spaces(content['title']) for content in self.search_list]
        year_list = [int(y['year']) for y in self.search_list]
        adjacent_year_list = [[i + self.add_year, i, i - self.add_year] for i in year_list]
        # one_adjacent_year_list = [item for sublist in adjacent_year_list for item in sublist]
        counts = result_new_title_list.count(new_title)
        self.movie_info['搜索到的标题'] = '/'.join(result_new_title_list)

        if not year:
            if counts == 0:
                self.notes = '标题不同 选择第一个'
                self.id = self.search_list[0]['id']
                for i in range(len(self.search_list)):
                    if result_new_title_list[i] in new_title or new_title in result_new_title_list[i]:
                        self.notes = '标题不同 选择相似的一个'
                        self.id = self.search_list[i]['id']
                        self.year = self.search_list[i]['year']
                        break
            elif counts == 1:
                index = result_new_title_list.index(new_title)
                self.id = self.search_list[index]['id']
                self.year = self.search_list[index]['year']
            else:
                self.notes = f'存在{counts}个相同的标题 选择第一个'
                index = result_new_title_list.index(new_title)
                self.id = self.search_list[index]['id']
                self.year = self.search_list[index]['year']
        else:
            if counts == 0:
                self.notes = '标题不同 年份不同'
                self.id = self.search_list[0]['id']
                self.year = self.search_list[0]['year']
                for i in range(len(adjacent_year_list)):
                    if year in adjacent_year_list[i]:
                        self.id = self.search_list[i]['id']
                        self.year = self.search_list[i]['year']
                        self.notes = '标题不同'
                        break
            elif counts == 1:
                self.notes = '年份不同'
                index = result_new_title_list.index(new_title)
                self.id = self.search_list[index]['id']
                self.year = self.search_list[index]['year']
            else:
                print(self.search_list)
                self.notes = f'{counts}个相同标题 年份不同'
                index = result_new_title_list.index(new_title)
                self.id = self.search_list[index]['id']
                self.year = self.search_list[index]['year']
                for i in range(len(adjacent_year_list)):
                    if year in adjacent_year_list[i] and new_title == remove_symbols_and_spaces(self.search_list[i]['title']):
                        self.id = self.search_list[i]['id']
                        self.year = self.search_list[index]['year']
                        self.notes = ''
                        break

    def get_id_by_title(self, input_title, year=None):
        self.get_search_list_by_js(input_title)
        if self.total > 0:
            self.choice_best_from_search_list(input_title, year=year)
        else:
            raise Exception('搜索内容为空')

    def get_url_by_id(self):
        if self.id:
            return f'https://movie.douban.com/subject/{self.id}/'

    def get_html_content_by_url(self, url):
        res = requests.get(url=url, headers=self.headers, timeout=10)
        if res.status_code not in [200, 201]:
            raise Exception(f'status_code {res.status_code}')
        if '有异常请求从你的 IP 发出，点击下方按钮继续' in res.text:
            raise Exception('有异常请求从你的 IP 发出，点击下方按钮继续（请登录豆瓣后，填写相关的User-Agent 和 Cookie）')
        return res.text

    def extract_movie_info(self, html_content):
        """解析网页"""
        soup = BeautifulSoup(html_content, 'lxml')
        # 获取电影信息字段
        long_title = soup.find('span', attrs={'property': 'v:itemreviewed'}).get_text()
        self.movie_info['标题'] = extract_before_first_space(long_title)
        self.movie_info['年代'] = soup.find('span', class_='year').get_text().strip("()")
        self.movie_info['评分'] = soup.select('.ll.rating_num')[0].get_text()
        votes_tag = soup.find('span', attrs={'property': 'v:votes'})
        self.movie_info['评价数'] = votes_tag.get_text() if votes_tag else ''

        text = soup.select('#info')[0].text.strip().split('\n')
        for m in text:
            try:
                sname = m.split(':')[0].strip()
                svalue = m.split(':')[1].strip().replace(' ', '')
                self.movie_info[sname] = svalue
            except:
                pass

        try:
            desc = soup.select('.all.hidden')[0].text.strip()
        except:
            try:
                desc = soup.select('#link-report-intra')[0].text.strip()
            except:
                desc = ''
        self.movie_info['简介'] = optimize_desc_string(desc)

        awards = soup.find_all('ul', class_='award')
        # 提取每个奖项的信息
        award_list = []
        for award in awards:
            items = award.find_all('li')
            festival = items[0].get_text(strip=True)
            category = items[1].get_text(strip=True)
            person = items[2].get_text(strip=True)
            award_list.append(f"【{festival} {category} {person}】")
        self.movie_info['获奖'] = '/'.join(award_list)

    def search_by_title(self, input_title, year=None):
        """通过标题的方式，来获取id，在转换成url,最后解析成字典数据"""
        print(f'豆瓣搜索: {input_title}')
        self.movie_info['search_title'] = input_title
        try:
            self.get_id_by_title(input_title, year=year)
            url = self.get_url_by_id()
            if url:
                html_content = self.get_html_content_by_url(url)
                self.extract_movie_info(html_content)
            self.movie_info['total'] = self.total
            self.movie_info['notes'] = self.notes
        except Exception as e:
            self.movie_info['error'] = str(e)
            print(f'error: {e}')
        return self.movie_info

    def search_by_url(self, url):
        print(f'豆瓣: {url}')
        try:
            html_content = self.get_html_content_by_url(url)
            self.extract_movie_info(html_content)
        except Exception as e:
            self.movie_info['error'] = str(e)
            print(f'error: {e}')
        return self.movie_info

    def search_by_dict(self, data_dict):
        if '标题' in data_dict and data_dict['标题']:
            return data_dict
        elif 'url' in data_dict and data_dict['url']:
            return self.search_by_url(data_dict['url'])
        elif 'search_title' in data_dict:
            return self.search_by_title(data_dict['search_title'], year=data_dict['year'])
        else:
            print(f'error: 格式不正确')
            return data_dict.update({'error': '格式不正确'})
