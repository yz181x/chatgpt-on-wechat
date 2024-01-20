import re

def extract_elements(s):
    pattern = r'^(.*?)：\[(.*?)\](.*?)」\n-.*-\n(.*)$'
    #pattern = r'^(.*?)：\[(.*?)\]'
    match = re.match(pattern, s, re.DOTALL)
    if match:
        nickname = match.group(1)
        link_type = match.group(2)
        title = match.group(3).strip()
        query = match.group(4).strip()
        return nickname, link_type, title, query
    else:
        return None

s = '楊喆：[链接]听说这届年轻人早就开始存钱了？」\n- - - - - - - - - - - - - - -\n这篇文章的主要内容是什么？'
result = extract_elements(s)

# 保存结果并打印
print(result)

