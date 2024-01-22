from flask import Flask, request, send_from_directory, abort
from werkzeug.utils import secure_filename, safe_join
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import pyperclip
import configparser

import os
import time
import logging
from logging import FileHandler

# 文件所在的目录
FILES_DIRECTORY = '/home/yang/work/chatgpt-on-wechat/cached_data'
global_variable = {}

app = Flask(__name__)
#file_handler = FileHandler('web.log')
#stream_handler = logging.StreamHandler()
#app.logger.addHandler(file_handler)
#app.logger.addHandler(stream_handler)
app.logger.setLevel(logging.DEBUG)

def init(init_urls):
    # 初始化 WebDriver
    app.logger.debug("init webdriver")
    options = Options()
    #options.add_argument("--headless")
    #options.add_argument("--log-level=3")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    drivers = []
    for init_url in init_urls:
        app.logger.debug("init url: " + init_url)
        driver = webdriver.Chrome(options=options)  
        driver.get(init_url)
        drivers.append(driver)

    return drivers

def login_with_qrcode(driver):
    app.logger.debug("login_with_qrcode")
    login_button = driver.find_element(By.XPATH, '//*[@id="root"]/div/div[2]/div[2]/div/div[1]/div/div/div')
    if(login_button and login_button.text == "登录"):
        login_button.click()  # 点击登陆按钮
        print("请先扫码登录")

    # 设置循环以持续等待
    while True:
        try:
            # 设置显式等待，这里等待时间设置为较短的时间，例如10秒
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "img___pIC4p")))
            print("登录成功！")
            break  # 成功找到元素，退出循环
        except TimeoutException:
            print("还未登录成功，继续等待...")
            # 可以在这里添加代码以检查是否存在登录失败的提示，从而决定是否继续等待或执行其他操作


def login_with_phone(driver):
    app.logger.debug("login_with_phone")
    login_button = driver.find_element(By.XPATH, '//*[@id="root"]/div/div[2]/div[2]/div/div[1]/div/div/div')
    if(login_button and login_button.text == "登录"):
        login_button.click()  # 点击登陆按钮
    else:
        raise Exception("未找到登录按钮")
    login_phone_button = driver.find_element(By.XPATH, '//*[@id="root"]/div/div[2]/div[2]/div/div/div/div[2]/div/div[1]/div/div/button[2]')
    if(login_phone_button and login_phone_button.text == "手机快捷登录"):
        login_phone_button.click()  # 点击登陆按钮
    else:
        raise Exception("未找到手机快捷登录按钮")

    #输入用户名
    phone_number = login_wait_user()
    #phone_number = input("请输入手机号：")
    app.logger.debug("get phone num: " + phone_number)
    phone_input = driver.find_element(By.XPATH, '//*[@id="phone"]')
    if(phone_input):
        pyperclip.copy(phone_number)   #复制内容

        phone_input.click()
        time.sleep(0.5)

        actions = ActionChains(driver)
        actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL) # 执行粘贴操作
        actions.perform()

        #phone_input.send_keys(phone_number)
    else:
        raise Exception("未找到手机号输入框")

    checkbox = driver.find_element(By.XPATH, '//*[@id="root"]/div/div[2]/div[2]/div/div/div/div[2]/div/div[2]/div/form/label/span[1]/input')
    if(checkbox):
        checkbox.click()
    else:
        raise Exception("未找到协议勾选框")

    verification_code_sendbutton = driver.find_element(By.XPATH, '//*[@id="root"]/div/div[2]/div[2]/div/div/div/div[2]/div/div[2]/div/form/div[4]/div[2]/button/span[1]')
    if(verification_code_sendbutton):
        verification_code_sendbutton.click()
    else:
        raise Exception("未找到验证码发送按钮")
    
    #输入验证码
    verification_code = login_wait_code()
    #verification_code = input("请输入验证码：")
    app.logger.debug("get verification_code: " + verification_code)
    verification_code_input = driver.find_element(By.XPATH, '//*[@id="verify_code"]')
    if(verification_code_input):
        pyperclip.copy(verification_code)   #复制内容

        verification_code_input.click()
        time.sleep(0.5)

        actions = ActionChains(driver)
        actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL) # 执行粘贴操作
        actions.perform()

        #verification_code_input.send_keys(verification_code)
    else:
        raise Exception("未找到验证码输入框")
    
    #点击登录按钮
    login_button = driver.find_element(By.XPATH, '//*[@data-testid="msh-phonelogin-commit-button"]')  
    if(login_button):
        login_button.click()
    else:
        raise Exception("未找到登录按钮")

    # 设置循环以持续等待
    while True:
        try:
            # 设置显式等待，这里等待时间设置为较短的时间，例如10秒
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "img___pIC4p")))
            print("登录成功！")
            break  # 成功找到元素，退出循环
        except TimeoutException:
            print("还未登录成功，继续等待...")
            # 可以在这里添加代码以检查是否存在登录失败的提示，从而决定是否继续等待或执行其他操作

# 函数：获取最后一个 div 元素的文本内容
def get_last_div_text(driver):
    app.logger.debug("enter get_last_div_text.")
    divs = driver.find_elements(By.XPATH, "//div[@data-index]")
    if divs:
        return divs[-1].text
    return ""

def input_text(driver, input_str):
    app.logger.debug("input_text: " + input_str)    
    pyperclip.copy(input_str)   #复制内容

    # 找到含有 'data-slate-node' 属性的 div 元素并点击聚焦
    editable_div = driver.find_element(By.XPATH, "//div[@data-slate-node='element']")
    # driver.execute_script("arguments[0].value = '';", editable_div)
    editable_div.click()
    time.sleep(0.5)

    actions = ActionChains(driver)
    actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL) # 执行粘贴操作
    actions.perform()
    #editable_div.send_keys(input_str)

    time.sleep(0.5)
    #editable_div = driver.find_element(By.XPATH, "//div[@data-slate-node='element']")
    #editable_div.send_keys(Keys.ENTER) 
    submit = driver.find_element(By.XPATH, "//button[@data-testid='msh-chatinput-send-button']")   
    oversize = False
    while not (submit.is_displayed() and submit.is_enabled()):
        time.sleep(1)
        try:
            # 尝试定位包含错误消息的元素
            overseiz_element = driver.find_element(By.CLASS_NAME, "overSizeTip___opy7D")
            oversize = True
            message_element = driver.find_element(By.CSS_SELECTOR, "span.MuiTypography-root.MuiTypography-body2")
            return (False, message_element.text)
        except Exception as e:
            # 如果没有找到元素，则没有出现错误
            pass

    submit.click()
    return (True, "success")

def get_response(driver, input_text, last_response):
    app.logger.debug("enter get_response")
    # 初始等待
    wait = WebDriverWait(driver, 20)
    wait.until(lambda driver: get_last_div_text(driver) != "")

    last_text = get_last_div_text(driver)

    while True:
        # 等待一段时间，例如 5 秒
        time.sleep(2)

        # 再次获取最后一个 div 的文本内容
        new_text = get_last_div_text(driver)

        # 如果文本内容没有变化，则假定输出已完成
        if(
            new_text == last_text 
            and not new_text.endswith("停止输出") 
            and get_last_div_text(driver) != last_response
            and get_last_div_text(driver) != input_text
        ):
            #print("内容输出似乎已完成。")
            break
        else:
            last_text = new_text  # 更新文本内容以便下一次比较
        
        app.logger.debug("get response: " + new_text)
    return new_text

def login_init():
    config = configparser.ConfigParser()
    # 创建配置解析器
    config['kimi'] = {'user': "", 'password': ""}
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def login_wait_user():
    config = configparser.ConfigParser()
    while True:
        print("等待user中...", flush=True)
        config.read('config.ini') 
        user = config['kimi']['user'] 
        if user != "": 
            return user
        else:
            time.sleep(2)

def login_wait_code():
    config = configparser.ConfigParser()
    while True:
        print("等待password中...", flush=True)
        config.read('config.ini') 
        password = config['kimi']['password'] 
        if password != "": 
            return password 
        else:
            time.sleep(2)

def switch_to_tab(function_name):
    try:
        # 切换到新标签页
        driver, tab_index = global_variable[function_name]
        driver.switch_to.window(driver.window_handles[tab_index])
        return driver

    except Exception as e:
        print("switch_to_tab error: ", e)
        return None

@app.route('/search', methods=['POST'])
def search():
    driver = switch_to_tab("search")
    data = request.get_json()
    input_str = data['input_str']
    app.logger.info("get request: " + input_str)
    last_response = get_last_div_text(driver)
    result, message = input_text(driver, input_str)
    if (result):
        res = get_response(driver, input_str, last_response)
        app.logger.info("put response: " + res)
        return {
                'response': res,
                'content': res,
                "total_tokens": 100,
                'completion_tokens': 50,
                }
    else:
        driver.refresh()
        time.sleep(2)
        return {
                'response': message,
                'content': message,
                "total_tokens": 100,
                'completion_tokens': 50,
                }
 
@app.route('/chat_with_link', methods=['POST'])
def chat_with_link():    
    driver = switch_to_tab("chat_with_link")
    data = request.get_json()
    question = data['question']
    link = data['link']
    app.logger.info("question: " + question)
    app.logger.info("link: " + link)
    input_str = question + "\n" + link
    last_response = get_last_div_text(driver)
    result, message = input_text(driver, input_str)
    if (result):
        res = get_response(driver, input_str, last_response)
        app.logger.info("put response: " + res)
        return {
                'response': res,
                'content': res,
                "total_tokens": 100,
                'completion_tokens': 50,
                }
    else:
        driver.refresh()
        time.sleep(2)
        return {
                'response': message,
                'content': message,
                "total_tokens": 100,
                'completion_tokens': 50,
                }

@app.route('/chat_with_file', methods=['POST'])
def chat_with_file():    
    driver = switch_to_tab("chat_with_file")

    data = request.get_json()
    question = data['question']
    filepath = data['filepath']
    app.logger.info("question: " + question)
    app.logger.info("filepath: " + filepath)

    file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
    driver.execute_script("arguments[0].value = '';", file_input)
    file_input.send_keys(filepath)

    last_response = get_last_div_text(driver)
    result, message = input_text(driver, question)
    if (result):
        res = get_response(driver, question, last_response)
        app.logger.info("put response: " + res)
        return {
                'response': res,
                'content': res,
                "total_tokens": 100,
                'completion_tokens': 50,
                }
    else:
        driver.refresh()
        time.sleep(2)
        return {
                'response': message,
                'content': message,
                "total_tokens": 100,
                'completion_tokens': 50,
                }

@app.route('/chat', methods=['POST'])
def chat():    
    driver = switch_to_tab("chat")
    
    data = request.get_json()
    input_str = data['input_str']
    app.logger.info("get request: " + input_str)
    last_response = get_last_div_text(driver)
    result, message = input_text(driver, input_str)
    if (result):
        res = get_response(driver, input_str, last_response)
        app.logger.info("put response: " + res)
        return {
                'response': res,
                'content': res,
                "total_tokens": 100,
                'completion_tokens': 50,
                }
    else:
        driver.refresh()
        time.sleep(2)
        return {
                'response': message,
                'content': message,
                "total_tokens": 100,
                'completion_tokens': 50,
                }

@app.route('/cached_data/<filename>')
def download_file(filename):
    safe_path = safe_join(FILES_DIRECTORY, filename)
    if not os.path.isfile(safe_path):
        abort(404)  # 如果文件不存在，返回404错误
    return send_from_directory(FILES_DIRECTORY, filename)

@app.route('/', methods=['POST', 'GET'])
def root():
    return {'response': 'hello world'}

if __name__ == "__main__":

    login_init()
    while True:
        try:
            init_urls = ["https://kimi.moonshot.cn/"]
            drivers = init(init_urls)
            driver_kimi = drivers[0]

            time.sleep(5)
            #login_with_phone(driver)
            login_with_qrcode(driver_kimi)

            # 打开一个新的标签页
            driver_kimi.execute_script("window.open('');")

            global_variable["chat_with_link"] = (drivers[0], 0)
            global_variable["chat_with_file"] = (drivers[0], 0)
            global_variable["chat"] = (drivers[0], 0)
            global_variable["search"] = (drivers[0], 1)

            driver_search = switch_to_tab("search")
            driver_search.get("https://kimi.moonshot.cn/")

            break
        except Exception as e:
            print("出现异常.", e)
            #print(driver.page_source)
            print("10s后重试...")
            time.sleep(10)
            continue

    #app.logger.setLevel(logging.INFO)
    app.run(host='0.0.0.0', port=8010, threaded=False)
