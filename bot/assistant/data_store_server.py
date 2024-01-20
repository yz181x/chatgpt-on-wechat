from flask import Flask, send_from_directory, abort
from werkzeug.utils import secure_filename, safe_join
import os

app = Flask(__name__)

# 文件所在的目录
FILES_DIRECTORY = '/home/seven/work/chatgpt-on-wechat/cached_data'

@app.route('/cached_data/<filename>')
def download_file(filename):
    safe_path = safe_join(FILES_DIRECTORY, filename)
    if not os.path.isfile(safe_path):
        abort(404)  # 如果文件不存在，返回404错误
    return send_from_directory(FILES_DIRECTORY, filename)

if __name__ == "__main__":
    app.run(debug=True)
