import json

class DataStorage:
    def __init__(self, datafile='data_storage.json', threadfile='thread_storage.json'):
        self.datafile = datafile
        self.data_storage = self.load_data()

        self.threadfile = threadfile
        self.thread_storage = self.load_thread()

    def load_data(self):
        try:
            with open(self.datafile, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def load_thread(self):
        try:
            with open(self.threadfile, 'r', encoding='utf-8') as file:
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

    def add_thread(self, nickname, assistant_id, thread_id):
        if nickname not in self.thread_storage:
            self.thread_storage[nickname] = []
        self.thread_storage[nickname].append({"assistant_id": assistant_id, "thread_id": thread_id})
        self.save_thread()

    def save_data(self):
        with open(self.datafile, 'w', encoding='utf-8') as file:
            json.dump(self.data_storage, file, ensure_ascii=False, indent=4)

    def save_thread(self):
        with open(self.threadfile, 'w', encoding='utf-8') as file:
            json.dump(self.thread_storage, file, ensure_ascii=False, indent=4)

    def retrieve_data(self, category, nickname, title):
        if nickname in self.data_storage:
            for record in self.data_storage[nickname]:
                if record["类别"] == category and record["标题"] == title:
                    return record["内容"]
        return "未找到匹配的数据"

    def retrieve_thread(self, nickname):
        if nickname in self.thread_storage:
            for record in self.thread_storage[nickname]:
                return record["thread_id"]
        return None

# 使用示例
if __name__=="__main__":
    storage = DataStorage()

    # 添加数据
    storage.add_data("用户1", "SHARING", "分享标题1", "http://example.com", "user_id_1")
    storage.add_data("用户1", "FILE", "文件标题1", "/path/to/file", "user_id_2")
    storage.add_thread("用户2", "assistant_id_1", "thread_id_1")

    # 检索数据
    print(storage.retrieve_data("SHARING", "用户1", "分享标题1"))  # 应输出 http://example.com
    print(storage.retrieve_data("FILE", "用户1", "文件标题1"))  # 应输出 /path/to/file
    print(storage.retrieve_thread("用户1"))  # 应输出 未找到匹配的数据
