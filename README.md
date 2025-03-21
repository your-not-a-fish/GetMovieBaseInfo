# 豆瓣电影信息查询工具
这是一个输入标题，就可以精准获取豆瓣上相关影视基本信息的工具，可以单个查询，也可以处理excel表格。匹配方法有3中形式（名称;名称+年份;url）

## 功能特点
- 支持通过电影标题搜索
- 支持通过标题+年份精确搜索
- 支持将查询结果导出到 Excel 文件
- 自动处理同名电影的情况
- 不及预期的搜索结果会给预相应的提示
- 支持电影又名（别名）的识别

## 安装依赖
pip install -r requirements.txt

需要设置请求头信息，包含 User-Agent 和 Cookie：
headers = {
    'User-Agent': '你的agent',
    'Cookie': '你的豆瓣 Cookie'
}


### 示例1：几种常规的查询方式及匹配方案
from douban import DouBan
# 创建豆瓣查询实例
douban = DouBan(headers)

# 通过标题搜索（如果存在多个同名电影，将选择第一个并给出提示notes会提示）
info1 = douban.search_by_title('罗马假日')
print(info1)

# 通过标题和年份搜索（会通过年份来精准选择）
info2 = douban.search_by_title('罗马假日', year=1987)
print(info2)

# 搜索的内容没有该名称，而是别名，提示会取消
info3 = douban.search_by_title('OK镇大决斗')
print(info3)

# 搜索的内容没有结果
info4 = douban.search_by_title('战狼大战黑金刚')
print(info4)
# {'search_title': '战狼大战黑金刚', 'total': -1, 'notes': None}

# 通过url获取信息
info5 = douban.search_by_url('https://movie.douban.com/subject/1293839/')
print(info5)


## 示例2：处理excel表格，第一列为标题，第二列为年代（可以为空），不要设置表头，处理好后会生成 example_hand.xlsx
from excel_processor import ExcelProcessor
# 创建 Excel 处理器实例
processor = ExcelProcessor('example.xlsx', headers)
# 处理 Excel 文件
processor.process()
# 程序先把excel转换成同名的json文件，抓取一个保存一个
# 如果有几个数据没抓到，再次执行即可
# 再次执行，查询过、搜索数据为空的会pass


## 注意事项

1. 使用前需要配置正确的豆瓣 Cookie
2. 当搜索结果存在多个同名电影时，系统会默认选择第一个结果并给出提示
3. 如果电影有别名，系统会在提示中说明
4. Excel 导出功能需要确保目标文件路径存在且有写入权限

## 错误处理

- 当搜索不到完全匹配的结果时，系统会返回最接近的结果
- 如果电影出现在又名中，系统会在提示中说明
- 对于多个同名电影的情况，系统会给出提示信息
