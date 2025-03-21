import pandas as pd
import json
import os
from douban import DouBan
import time
import random


class ExcelProcessor:
    def __init__(self, excel_path, headers):
        self.excel_path = excel_path
        self.headers = headers
        self.waite_time = [3, 10]
        self.data_list = []
        self.json_path = os.path.splitext(excel_path)[0] + '.json'
        self.output_excel = os.path.splitext(self.excel_path)[0] + f'_hand.xlsx'

    def get_data_list(self):
        """将Excel文件转换为JSON，如果JSON已存在则跳过"""
        if os.path.exists(self.json_path):
            print(f"JSON文件 {self.json_path} 已存在，直击加载该文件，如果不要，请手动删除该文件")
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.data_list = json.load(f)
        else:
            try:
                # 尝试读取文件的前两列，并设置列名
                df = pd.read_excel(self.excel_path, usecols=[0, 1], names=['search_title', 'year'], header=None)
            except ValueError:
                # 如果第二列不存在，则只读取第一列
                df = pd.read_excel(self.excel_path, usecols=[0], names=['search_title'], header=None)

            # 如果只读取了一列，添加一个空的'year'列
            if 'year' not in df.columns:
                df['year'] = ''
            # 将DataFrame转换为字典列表，并处理可能的缺失值
            self.data_list = df.to_dict(orient='records')

            # 确保所有'year'字段不是NaN，如果是则替换为空字符串
            for entry in self.data_list:
                if pd.isna(entry.get('year')):
                    entry['year'] = ''

            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.data_list, f, ensure_ascii=False, indent=2)
            print(f"Excel文件已成功转换为JSON: {self.json_path}")

    def process_for_data(self):
        """处理JSON数据，使用DouBan类获取详细信息"""
        for i in range(len(self.data_list)):
            data = self.data_list[i]
            if '标题' in data and data['标题']:
                pass
            elif 'total' in data and int(data['total']) == 0:
                print('搜索不到内容')
                pass
            else:
                print('{}/{} {}'.format(i+1, len(self.data_list), data))
                douban = DouBan(self.headers)
                self.data_list[i] = douban.search_by_dict(data)

                try:
                    with open(self.json_path, 'w', encoding='utf-8') as f:
                        json.dump(self.data_list, f, ensure_ascii=False, indent=4)
                    print('\r休息', end='', flush=True)
                    time.sleep(random.randint(self.waite_time[0], self.waite_time[1]))
                except Exception as e:
                    print(f"处理记录时出错: {str(e)}")

    def json_to_excel(self):
        """将处理后的数据转换回Excel格式"""
        df = pd.DataFrame(self.data_list)
        df.to_excel(self.output_excel, index=False)
        print(f"数据已成功保存到Excel: {self.output_excel}")

    def process(self):
        """执行完整的处理流程"""
        print("开始处理数据...")
        # 1. Excel转JSON
        self.get_data_list()
        # 2. 处理JSON数据
        self.process_for_data()
        # 3. 转换回Excel
        self.json_to_excel()
