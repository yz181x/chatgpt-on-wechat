import json

class DataStorage:
    def __init__(self, filename='data_storage.json'):
        self.filename = filename
        self.data_storage = self.load_data()

    def load_data(self):
        try:
            with open(self.filename, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def add_data(self, nickname, category, title, content, user_id):
        if category not in ["SHARING", "FILE"]:
            print("无效类别，请输入 'SHARING' 或 'FILE'")
            return
        if nickname not in self.data_storage:
            self.data_storage[nickname] = []
        self.data_storage[nickname].append({"类别": category, "标题": title, "内容": content, "user_id": user_id})
        self.save_data()

    def save_data(self):
        with open(self.filename, 'w', encoding='utf-8') as file:
            json.dump(self.data_storage, file, ensure_ascii=False, indent=4)

    def retrieve_data(self, category, nickname, title):
        if nickname in self.data_storage:
            for record in self.data_storage[nickname]:
                if record["类别"] == category and record["标题"] == title:
                    return record["内容"]
        return "未找到匹配的数据"

# 使用示例
if __name__=="__main__":
    storage = DataStorage()

    # 添加数据
    storage.add_data("用户1", "SHARING", "分享标题1", "http://example.com", "user_id_1")
    storage.add_data("用户1", "FILE", "文件标题1", "/path/to/file", "user_id_2")

    # 检索数据
    print(storage.retrieve_data("SHARING", "用户1", "分享标题1"))  # 应输出 http://example.com
    print(storage.retrieve_data("FILE", "用户1", "文件标题1"))  # 应输出 /path/to/file
