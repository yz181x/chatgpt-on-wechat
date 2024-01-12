# encoding:utf-8

import time
import json
import os,re
import inspect

import openai
from openai import OpenAIError, APIError, APIConnectionError, APIResponseValidationError, Timeout
import requests

from bot.bot import Bot
from bot.chatgpt.chat_gpt_session import ChatGPTSession
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from common.token_bucket import TokenBucket
from config import conf, load_config

# OpenAI对话模型API (可用)
class AssistantBot(Bot):
    def __init__(self):
        super().__init__()
        # set the default api_key
        openai.api_key = conf().get("open_ai_api_key")
        if conf().get("open_ai_api_base"):
            openai.api_base = conf().get("open_ai_api_base")
        proxy = conf().get("proxy")
        if proxy:
            openai.proxy = proxy
        if conf().get("rate_limit_chatgpt"):
            self.tb4chatgpt = TokenBucket(conf().get("rate_limit_chatgpt", 20))

        self.sessions = SessionManager(ChatGPTSession, model=conf().get("model") or "gpt-3.5-turbo")
        self.args = {
            "model": conf().get("model") or "gpt-3.5-turbo",  # 对话模型的名称
            "temperature": conf().get("temperature", 0.9),  # 值在[0,1]之间，越大表示回复越具有不确定性
            # "max_tokens":4096,  # 回复最大的字符数
            "top_p": conf().get("top_p", 1),
            "frequency_penalty": conf().get("frequency_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "presence_penalty": conf().get("presence_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "request_timeout": conf().get("request_timeout", None),  # 请求超时时间，openai接口默认设置为600，对于难问题一般需要较长时间
            "timeout": conf().get("request_timeout", None),  # 重试超时时间，在这个时间内，将会自动重试
        }

        from openai import OpenAI

        self.client = OpenAI(api_key=openai.api_key)
        #self.client = OpenAI(api_key="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")
        self.assistant = self.client.beta.assistants.retrieve(assistant_id="asst_p7884ovmJojoHvsMXj3DzwgH")
        #self.thread = self.client.beta.threads.retrieve(thread_id="thread_JXFD8Tpz3KmF0H1jLTOSqrK3")
        self.thread = self.client.beta.threads.create(
            metadata={"fullname": "seven", "username": "seven yang"}
        )
                
        self.show_json(self.assistant)
        self.show_json(self.thread)

    def reply(self, query, context=None):
        reply = None
        # acquire reply content
        logger.info(f"Current location: {__file__}:{inspect.currentframe().f_lineno}")
        
        if context.type == ContextType.TEXT:
            logger.info("[CHATGPT] query={}".format(query))

            session_id = context["session_id"]
            clear_memory_commands = conf().get("clear_memory_commands", ["#清除记忆"])
            if query in clear_memory_commands:
                self.sessions.clear_session(session_id)
                reply = Reply(ReplyType.INFO, "记忆已清除")
            elif query == "#清除所有":
                self.sessions.clear_all_session()
                reply = Reply(ReplyType.INFO, "所有人记忆已清除")
            elif query == "#更新配置":
                load_config()
                reply = Reply(ReplyType.INFO, "配置已更新")
            if reply:
                return reply
            session = self.sessions.session_query(query, session_id)
            logger.debug("[CHATGPT] session query={}".format(session.messages))

            api_key = context.get("openai_api_key")
            model = context.get("gpt_model")
            new_args = None
            if model:
                new_args = self.args.copy()
                new_args["model"] = model
            # if context.get('stream'):
            #     # reply in stream
            #     return self.reply_text_stream(query, new_query, session_id)

            reply_content = self.reply_text(session, api_key, args=new_args)
            logger.debug(
                "[CHATGPT] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(
                    session.messages,
                    session_id,
                    reply_content["content"],
                    reply_content["completion_tokens"],
                )
            )
            logger.info(f"Current location: {__file__}:{inspect.currentframe().f_lineno}")
            if reply_content["completion_tokens"] == 0 and len(reply_content["content"]) > 0:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
            elif reply_content["completion_tokens"] > 0:
                self.sessions.session_reply(reply_content["content"], session_id, reply_content["total_tokens"])
                #去掉【数字†source】
                content = reply_content["content"]
                processed_content = re.sub(r"【\d+†.*】", "", content)
                reply_content["content"] = processed_content
                reply = Reply(ReplyType.TEXT, reply_content["content"])
            else:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
                logger.debug("[CHATGPT] reply {} used 0 tokens.".format(reply_content))
            return reply

        elif context.type == ContextType.IMAGE_CREATE:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply
        elif context.type == ContextType.FILE:
            context.get("msg").prepare()
            file_path = context.content
            file_name = os.path.basename(file_path)
            try:
                self.current_file = self.client.files.create(
                    file=open(file_path, "rb"), 
                    purpose="assistants",
                )
                self.show_json(self.current_file)
                response = self._reply_text_internal(query="", file_ids=[self.current_file.id])
                response_txt = f"""
我收到了你上传的文件，文件名为：{file_name}.
你可以对这个文件进行提问、摘要等操作。
"""                
                #reply = Reply(ReplyType.TEXT, response.data[0].content[0].text.value)
                reply = Reply(ReplyType.TEXT, response_txt)
            except:
                pass
            finally:
                os.remove(file_path)
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    def reply_text(self, session: ChatGPTSession, api_key=None, args=None, retry_count=0) -> dict:
        """
        call openai's ChatCompletion to get the answer
        :param session: a conversation session
        :param session_id: session id
        :param retry_count: retry count
        :return: {}
        """
        try:
            logger.info(f"Current location: {__file__}:{inspect.currentframe().f_lineno}")
            if conf().get("rate_limit_chatgpt") and not self.tb4chatgpt.get_token():
                raise openai.error.RateLimitError("RateLimitError: rate limit exceeded")
            # if api_key == None, the default openai.api_key will be used
            if args is None:
                args = self.args
            #response = openai.ChatCompletion.create(api_key=api_key, messages=session.messages, **args)
            response = self._reply_text_internal(query=session.messages[-1]['content'])
            # logger.debug("[CHATGPT] response={}".format(response))
            # logger.info("[ChatGPT] reply={}, total_tokens={}".format(response.choices[0]['message']['content'], response["usage"]["total_tokens"]))
            response = {
                "total_tokens": 100,
                "completion_tokens": 50,
                "content": response.data[0].content[0].text.value,
            }
            return response
        except Exception as e:
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            if False:
                pass
            else:
                logger.exception("[CHATGPT] Exception: {}".format(e))
                need_retry = False
                self.sessions.clear_session(session.session_id)

            if need_retry:
                logger.warn("[CHATGPT] 第{}次重试".format(retry_count + 1))
                return self.reply_text(session, api_key, args, retry_count + 1)
            else:
                return result

    def _reply_text_internal(self, query=None, file_ids=[]):
        logger.info(f"Current location: {__file__}:{inspect.currentframe().f_lineno}")
        result = self.create_message_and_run(self.assistant, self.thread, content=query, file_ids=file_ids)
        return result

    def show_json(self, obj):
        print(json.dumps(json.loads(obj.model_dump_json()), indent=4, ensure_ascii=False))

    def wait_on_run(self, run, thread):
        """等待 run 结束，返回 run 对象，和成功的结果"""
        logger.info(f"Current location: {__file__}:{inspect.currentframe().f_lineno}")
        client = self.client
        while run.status == "queued" or run.status == "in_progress":
            """还未中止"""
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id)
            print("status: " + run.status)

            # 打印调用工具的 step 详情
            if (run.status == "completed"):
                run_steps = client.beta.threads.runs.steps.list(
                    thread_id=thread.id, run_id=run.id, order="asc"
                )
                for step in run_steps.data:
                    if step.step_details.type == "tool_calls":
                        self.show_json(step.step_details)

            # 等待 1 秒
            time.sleep(0.5)

        if run.status == "requires_action":
            """需要调用函数"""
            # 可能有多个函数需要调用，所以用循环
            tool_outputs = []
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                # 调用函数
                name = tool_call.function.name
                print("调用函数：" + name + "()")
                print("参数：")
                print(tool_call.function.arguments)
                function_to_call = available_functions[name]
                arguments = json.loads(tool_call.function.arguments)
                result = function_to_call(arguments)
                print("结果：" + str(result))
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(result),
                })

            # 提交函数调用的结果
            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs,
            )

            # 递归调用，直到 run 结束
            return wait_on_run(run, thread)

        if run.status == "completed":
            """成功"""
            # 获取全部消息
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            # 最后一条消息排在第一位
            #result = messages.data[0].content[0].text.value
            result = messages
            return run, result

        # 执行失败
        return run, None

    def create_message_and_run(self, assistant, thread, content, file_ids=[]):
        """创建消息并执行"""
        logger.info(f"Current location: {__file__}:{inspect.currentframe().f_lineno}")
        client = self.client
        if len(file_ids) == 0:
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=content
            )
        else:
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=content,
                file_ids=file_ids
            )
        logger.info(f"Current location: {__file__}:{inspect.currentframe().f_lineno}")
        run = client.beta.threads.runs.create(
            assistant_id=assistant.id,
            thread_id=thread.id,
        )
        run, result = self.wait_on_run(run, thread)

        return result




if __name__ == "__main__":
    bot = AssistantBot()
    while True:
        query = input("请输入：")
        response = bot._reply_text_internal(query=query)
        print(response['content'])