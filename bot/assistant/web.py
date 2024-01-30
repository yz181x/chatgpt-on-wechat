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
import datetime
import locale

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
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--enable-chrome-browser-cloud-management")
    options.add_argument("--ignore-ssl-errors=yes")
    options.add_argument("--ssl-protocol=any")

    drivers = []
    for init_url in init_urls:
        app.logger.debug("init url: " + init_url)
        driver = webdriver.Chrome(options=options)  
        driver.get(init_url)
        drivers.append(driver)

    return drivers

def kimi_login_with_qrcode(driver):
    app.logger.debug("kimi_login_with_qrcode")
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

def backtest_login_with_qrcode(driver):
    app.logger.debug("backtest_login_with_qrcode")
    login_button = driver.find_element(By.XPATH, '//a[@onclick="login()"]')
    if(login_button and login_button.text == "登录"):
        login_button.click()  # 点击登陆按钮
        print("请先扫码登录")

    # 设置循环以持续等待
    while True:
        try:
            # 设置显式等待，这里等待时间设置为较短的时间，例如10秒
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.XPATH, '//a[@onclick="logout()"]')))
            print("登录成功！")

            # 导航到回测页面
            time.sleep(1)
            element = driver.find_element(By.XPATH, '//li[text()="回测一下"]')
            element.click()
            break  # 成功找到元素，退出循环
        except Exception as e:
            print("还未登录成功，继续等待...")
            # print(e)
            time.sleep(3)
            continue
            # 可以在这里添加代码以检查是否存在登录失败的提示，从而决定是否继续等待或执行其他操作
    
def c_ai_login_with_qrcode(driver):
    app.logger.debug("c_ai_login_with_qrcode")
    login_button = driver.find_element(By.XPATH, '//button[text()="Log In"]')
    if(login_button and login_button.text == "Log In"):
        login_button.click()  # 点击登陆按钮
        print("请先登录")

    # 设置循环以持续等待
    while True:
        try:
            # 设置显式等待，这里等待时间设置为较短的时间，例如10秒
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.XPATH, '//a[@href="/profile?"]')))
            print("登录成功！")

            break  # 成功找到元素，退出循环
        except Exception as e:
            print("还未登录成功，继续等待...")
            # print(e)
            time.sleep(3)
            continue
            # 可以在这里添加代码以检查是否存在登录失败的提示，从而决定是否继续等待或执行其他操作

def kimi_login_with_phone(driver):
    app.logger.debug("kimi_login_with_phone")
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
    loop_nums = 120
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
            loop_nums -= 1
            if(loop_nums <= 0):
                return (False, "timeout...")
            pass

    submit.click()
    return (True, "success")

def get_response(driver, input_text, last_response):
    app.logger.debug("enter get_response")
    # 初始等待
    wait = WebDriverWait(driver, 20)
    wait.until(lambda driver: get_last_div_text(driver) != "")

    last_text = get_last_div_text(driver)

    loop_nums = 60
    while loop_nums >= 0:
        # 等待一段时间，例如 5 秒
        time.sleep(2)
        loop_nums -= 1

        # 再次获取最后一个 div 的文本内容
        new_text = get_last_div_text(driver)

        # 如果文本内容没有变化，则假定输出已完成
        if(
            new_text == last_text 
            and not new_text.endswith("停止输出") 
            and new_text != last_response
            and new_text != input_text
        ):
            #print("内容输出似乎已完成。")
            break
        else:
            app.logger.debug("new_text:" + new_text + "\nlast_test:" + last_text + "\ninput_test:" + input_text + "\nlast_response:" + last_response)
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
        driver, _, tab_handle = global_variable[function_name]
        driver.switch_to.window(tab_handle)
        return driver

    except Exception as e:
        print("switch_to_tab error: ", e)
        return None

def get_newtab(function_name):
    try:
        driver, website, _ = global_variable[function_name]
        # 打开一个新的标签页
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        driver.get(website)
        return (driver, website, driver.window_handles[-1])

    except Exception as e:
        print("switch_to_tab error: ", e)
        return None

def get_year_month_day(date_str):
    # 解析日期字符串
    date = datetime.datetime.strptime(date_str, '%Y-%m-%d')

    # 获取月份的中文名称
    locale.setlocale(locale.LC_ALL, 'zh_CN.utf8')
    month_zh = date.strftime('%B')

    # 获取月份的英文名称
    locale.setlocale(locale.LC_ALL, 'en_US.utf8')
    month_en = date.strftime('%b')

    # 返回四元组
    return (str(date.year), month_zh, month_en, str(date.day))

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
                # 'response': res,
                'content': res,
                "total_tokens": 100,
                'completion_tokens': 50,
                }
    else:
        driver.refresh()
        time.sleep(2)
        return {
                # 'response': message,
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
                # 'response': res,
                'content': res,
                "total_tokens": 100,
                'completion_tokens': 50,
                }
    else:
        driver.refresh()
        time.sleep(2)
        return {
                # 'response': message,
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
    filepath = filepath.replace("\n", "")
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
                # 'response': res,
                'content': res,
                "total_tokens": 100,
                'completion_tokens': 50,
                }
    else:
        driver.refresh()
        time.sleep(2)
        return {
                # 'response': message,
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
                # 'response': res,
                'content': res,
                "total_tokens": 100,
                'completion_tokens': 50,
                }
    else:
        driver.refresh()
        time.sleep(2)
        return {
                # 'response': message,
                'content': message,
                "total_tokens": 100,
                'completion_tokens': 50,
                }

@app.route('/backtest', methods=['POST'])
def backtest():    
    driver = switch_to_tab("backtest")
    driver.refresh()
    time.sleep(3)
    
    data = request.get_json()
    input_str = data['input_str']
    start_date = data['start_date']
    end_date = data['end_date']
    app.logger.info("get request: " + input_str + "\n回测周期: " + start_date + " - " + end_date)

    #初始化日期
    # date_input = driver.find_element(By.ID, 'trade_detail_startDate')
    # driver.execute_script("arguments[0].value = '2019-01-01';", date_input)
    # date_input = driver.find_element(By.ID, 'trade_detail_endDate')
    # driver.execute_script("arguments[0].value = '2024-01-01';", date_input)
    #初始化开始日期
    date_start = driver.find_element(By.ID, 'trade_detail_startDate')
    date_start.click()
    time.sleep(0.5)
    iframe_element = driver.find_element(By.XPATH, '//iframe[@hidefocus="true"]')
    driver.switch_to.frame(iframe_element)
    time.sleep(0.1)
    date = driver.find_elements(By.XPATH, '//input[@class="yminput"]')
    month = date[0]
    year = date[1]
    
    start_year, start_month_cn, start_month_en, start_day = get_year_month_day(start_date)

    year.click()
    time.sleep(0.1)
    year_element = driver.find_element(By.XPATH, f"//td[text()='{start_year}']")
    year_element.click()
    time.sleep(0.1)

    month.click()
    time.sleep(0.1)
    month_element = driver.find_element(By.XPATH, f"//td[contains(text(), '{start_month_cn[:2]}') or contains(text(), '{start_month_en}')]")
    month_element.click()    
    time.sleep(0.1)

    day = driver.find_element(By.XPATH, f"//td[text()='{start_day}']")
    day.click()
    time.sleep(0.1)
    
    driver.switch_to.default_content()

    #初始化结束日期
    date_end = driver.find_element(By.ID, 'trade_detail_endDate')
    date_end.click()
    time.sleep(0.5)
    iframe_element = driver.find_element(By.XPATH, '//iframe[@hidefocus="true"]')
    driver.switch_to.frame(iframe_element)
    time.sleep(0.1)
    date = driver.find_elements(By.XPATH, '//input[@class="yminput"]')
    month = date[0]
    year = date[1]

    end_year, end_month_cn, end_month_en, end_day = get_year_month_day(end_date)

    year.click()
    time.sleep(0.1)
    year_element = driver.find_element(By.XPATH, f"//td[text()='{end_year}']")
    year_element.click()
    time.sleep(0.1)

    month.click()
    time.sleep(0.1)    
    month_element = driver.find_element(By.XPATH, f"//td[contains(text(), '{end_month_cn[:2]}') or contains(text(), '{end_month_en}')]")
    month_element.click()
    time.sleep(0.1)
    
    day = driver.find_element(By.XPATH, f"//td[text()='{end_day}']")
    day.click()
    time.sleep(0.1)

    driver.switch_to.default_content()

    #初始化持有天数
    pyperclip.copy("1,2,3,4,5,10,15,20,30")   #复制内容
    input_element = driver.find_element(By.XPATH, '//div[@class="question_cycle_number"]/input[@type="text"]')
    input_element.click()  
    time.sleep(0.5)

    actions = ActionChains(driver)
    actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL) # 执行粘贴操作
    actions.perform()
    time.sleep(0.5)

    #input_element = driver.find_element(By.XPATH, '//div[@class="question_cycle_number"]/input[@type="text"]')
    #input_element.clear()  # 清除输入框中的现有内容
    #input_element.send_keys("1,2,3,4,5,10,15,20,30")  # 输入新的内容

    #输入回测条件
    pyperclip.copy(input_str)   #复制内容
    editable_div = driver.find_element(By.ID, 'question_sentence_input')
    editable_div.click()
    time.sleep(0.5)

    actions = ActionChains(driver)
    actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL) # 执行粘贴操作
    actions.perform()
    time.sleep(0.5)

    #点击开始回测
    submit = driver.find_element(By.XPATH, '//div[@class="beginbacktest fr"]')
    submit.click()
    time.sleep(5)

    #判断成功还是失败
    error_elements = driver.find_elements(By.XPATH, '//div[@class="order-successful-execution-order error"]')
    error_count = len(error_elements)

    if(error_count == 0):        
        recommend_element = driver.find_element(By.XPATH, "//td[@class='recommend']").find_element(By.XPATH, "..")
        recommend_text = recommend_element.text
        recommend_text_list = recommend_text.split(" ")[1:]

        title_element = driver.find_element(By.XPATH, '//thead[@data-v-1c2a2c3e]')
        title_text = title_element.text
        title_text_list = title_text.split(" ")
        res = dict(zip(title_text_list, recommend_text_list))
        res["回测周期"] = start_date + ' - ' + end_date
        res["测试持有天数"] = "1,2,3,4,5,10,15,20,30天"

        res = str(res)

        app.logger.info("put response: " + res)
        return {
                # 'response': res,
                'content': res,
                "total_tokens": 100,
                'completion_tokens': 50,
                }
    else:
        message = "抱歉，回测失败，请换一个条件后重试。"
        return {
                # 'response': message,
                'content': message,
                "total_tokens": 100,
                'completion_tokens': 50,
                }

@app.route('/chatGPT', methods=['POST'])
def chatGPT():
    data = request.get_json()
    input_str = data['input_str']
    app.logger.info("get request: " + input_str)
    base_file = "D:\\_work\\git\\selenium"
    finish_token = "qwertyuiopasdfghjklzxcvbnm"

    file_out_path = os.path.join(base_file, "chat_out.txt")
    with open(file_out_path, 'w', encoding="utf-8") as f:
        f.write("" + "\n")
    
    file_in_path = os.path.join(base_file, "chat_in.txt")
    with open(file_in_path, 'w', encoding="utf-8") as f:
        f.write(input_str + "\n")
        f.write(finish_token + "\n")

    timeout = time.time() + 300  # 设置5分钟超时时间
    while time.time() < timeout:
        time.sleep(1)
        with open(file_out_path, 'r', encoding="utf-8") as file:  # 替换为你的文件路径
            lines = file.readlines()

        if lines[-1].strip() == finish_token:
            response = ''.join(lines[:-1]).strip()
            app.logger.info("put response: " + response)
            return {
                    # 'response': response,
                    'content': response,
                    "total_tokens": 100,
                    'completion_tokens': 50,
                    }
    message = "失败，请稍后重试。"
    return {
            # 'response': message,
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
            init_urls = ["https://kimi.moonshot.cn/", "https://backtest.10jqka.com.cn/"]
            # init_urls = ["https://chat.openai.com", "https://beta.character.ai/", "https://www.perplexity.ai/"]
            drivers = init(init_urls)
            driver_file = drivers[0]
            driver_link = drivers[0]
            driver_search = drivers[0]
            driver_chat = drivers[0]
            driver_backtest = drivers[1]
            # driver_c_ai = drivers[0]
            time.sleep(5)

            # login...
            kimi_login_with_qrcode(driver_file)
            backtest_login_with_qrcode(driver_backtest)
            # c_ai_login_with_qrcode(driver_c_ai)

            global_variable["chat_with_file"] = (driver_file, driver_file.current_url, 0)
            global_variable["chat_with_link"] = (driver_link, driver_link.current_url, 0)
            global_variable["chat"] = (driver_chat, driver_chat.current_url, 0)
            global_variable["search"] = (driver_search, driver_search.current_url, 0)
            global_variable["backtest"] = (driver_backtest, driver_backtest.current_url, 0)
            # global_variable["c_ai"] = (driver_c_ai, driver_c_ai.current_url, 0) 

            global_variable["chat_with_file"] = get_newtab("chat_with_file")
            global_variable["chat_with_link"] = get_newtab("chat_with_link")
            global_variable["chat"] = get_newtab("chat")
            global_variable["search"] = get_newtab("search")
            global_variable["backtest"] = get_newtab("backtest")
            # global_variable["c_ai"] = get_newtab("c_ai")

            break
        except Exception as e:
            print("出现异常.", e)
            #print(driver.page_source)
            print("10s后重试...")
            time.sleep(10)
            continue

    #app.logger.setLevel(logging.INFO)
    app.run(host='0.0.0.0', port=8010, threaded=False)
