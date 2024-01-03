import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from plugins import *
from .midjourney import MJBot
from .summary import LinkSummary
from bridge import bridge
from common.expired_dict import ExpiredDict
from common import const
import os
from .utils import Util

@plugins.register(
    name="linkai",
    desc="A plugin that supports knowledge base and midjourney drawing.",
    version="0.1.0",
    author="https://link-ai.tech",
    desire_priority=99
)
class LinkAI(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        self.config = super().load_config()
        if not self.config:
            # 未加载到配置，使用模板中的配置
            self.config = self._load_config_template()
        if self.config:
            self.mj_bot = MJBot(self.config.get("midjourney"))
        self.sum_config = {}
        if self.config:
            self.sum_config = self.config.get("summary")
        logger.info(f"[LinkAI] inited, config={self.config}")


    def on_handle_context(self, e_context: EventContext):
        """
        消息处理逻辑
        :param e_context: 消息上下文
        """
        if not self.config:
            return

        context = e_context['context']
        if context.type not in [ContextType.TEXT, ContextType.IMAGE, ContextType.IMAGE_CREATE, ContextType.FILE, ContextType.SHARING]:
            # filter content no need solve
            return

        if context.type in [ContextType.FILE, ContextType.IMAGE] and self._is_summary_open(context):
            # 文件处理
            context.get("msg").prepare()
            file_path = context.content
            if not LinkSummary().check_file(file_path, self.sum_config):
                return
            if context.type != ContextType.IMAGE:
                _send_info(e_context, "正在为你加速生成摘要，请稍后")
            res = LinkSummary().summary_file(file_path)
            if not res:
                if context.type != ContextType.IMAGE:
                    _set_reply_text("因为神秘力量无法获取内容，请稍后再试吧", e_context, level=ReplyType.TEXT)
                return
            summary_text = res.get("summary")
            if context.type != ContextType.IMAGE:
                USER_FILE_MAP[_find_user_id(context) + "-sum_id"] = res.get("summary_id")
                summary_text += "\n\n💬 发送 \"开启对话\" 可以开启与文件内容的对话"
            _set_reply_text(summary_text, e_context, level=ReplyType.TEXT)
            os.remove(file_path)
            return

        if (context.type == ContextType.SHARING and self._is_summary_open(context)) or \
                (context.type == ContextType.TEXT and LinkSummary().check_url(context.content)):
            if not LinkSummary().check_url(context.content):
                return
            _send_info(e_context, "正在为你加速生成摘要，请稍后")
            res = LinkSummary().summary_url(context.content)
            if not res:
                _set_reply_text("因为神秘力量无法获取文章内容，请稍后再试吧~", e_context, level=ReplyType.TEXT)
                return
            _set_reply_text(res.get("summary") + "\n\n💬 发送 \"开启对话\" 可以开启与文章内容的对话", e_context, level=ReplyType.TEXT)
            USER_FILE_MAP[_find_user_id(context) + "-sum_id"] = res.get("summary_id")
            return

        mj_type = self.mj_bot.judge_mj_task_type(e_context)
        if mj_type:
            # MJ作图任务处理
            self.mj_bot.process_mj_task(mj_type, e_context)
            return

        if context.content.startswith(f"{_get_trigger_prefix()}linkai"):
            # 应用管理功能
            self._process_admin_cmd(e_context)
            return

        if context.type == ContextType.TEXT and context.content == "开启对话" and _find_sum_id(context):
            # 文本对话
            _send_info(e_context, "正在为你开启对话，请稍后")
            res = LinkSummary().summary_chat(_find_sum_id(context))
            if not res:
                _set_reply_text("开启对话失败，请稍后再试吧", e_context)
                return
            USER_FILE_MAP[_find_user_id(context) + "-file_id"] = res.get("file_id")
            _set_reply_text("💡你可以问我关于这篇文章的任何问题，例如：\n\n" + res.get("questions") + "\n\n发送 \"君茂分析\" 可以利用君茂的投资框架来自动分析" + "\n发送 \"君茂分析框架\" 可以查看具体的分析框架" + "\n\n发送 \"退出对话\" 可以关闭与文章的对话" , e_context, level=ReplyType.TEXT)
            return

        if context.type == ContextType.TEXT and context.content == "退出对话" and _find_file_id(context):
            del USER_FILE_MAP[_find_user_id(context) + "-file_id"]
            bot = bridge.Bridge().find_chat_bot(const.LINKAI)
            bot.sessions.clear_session(context["session_id"])
            _set_reply_text("对话已退出", e_context, level=ReplyType.TEXT)
            return

        if context.type == ContextType.TEXT and context.content == "君茂分析框架" and _find_file_id(context):
            junmaofenxi_res = """
输入的指令、对应的问题；\n\n
君茂分析1、根据文档信息，详细介绍一下这个项目，知道多少就介绍多少，尽可能详细；
君茂分析2、简单介绍该项目的团队，包括董事长、CEO等主要成员的信息，包括不限于学历、主要经理和职业信息等等，尽可能详细；
君茂分析3、该公司的发展历史是怎样的；
君茂分析4、根据商业模式画板内容来分析该公司的商业模式，具体来说包括如下几个方面，如果信息不全，知道多少告诉我多少：
	-重要合作伙伴(Key Partnerships)
	-关键业务（Key Activities）
	-价值主张（Value Propositions）
	-客户关系（Customer Relationships）
	-客户细分（Customer Segments）
	-核心资源（Key Resources）
	-渠道通路（Channels）
	-成本结构（Cost Structure）
	-收入来源（Revenue Streams）
君茂分析5、分析该公司的盈利能力，包括收入、利润利润率、PE、收入预测等，注意要明确数字的单位；
君茂分析6、帮助分析该公司所处行业的竞争格局，可以按照波特五力模型的框架来分析，能分析多少就分析多少，尽你所能的分析；
君茂分析7、尽你所能，帮我进行SWOT分析；
君茂分析8、该公司跟同行其他公司相比，有什么核心功能点，比较的话有什么优势劣势，尽可能详细的告诉我；
君茂分析9、该公司获得了哪些荣誉资质，包括但不限于专利、软件著作权等等，尽可能的详细一些；
君茂分析10、根据上述信息和你的专业背景，对该项目进行一个整体的评估，务必要给出你的建议及理由；
            """
            _set_reply_text(junmaofenxi_res, e_context, level=ReplyType.TEXT)
            return
        if context.type == ContextType.TEXT and context.content == "君茂分析1" and _find_file_id(context):
            bot = bridge.Bridge().find_chat_bot(const.LINKAI)
            context.kwargs["file_id"] = _find_file_id(context)
            junmaofenxi = """
## Background：
你看到的是一个项目融资文档，需要对这个项目进行评估，看是否值得投资。

## Role：
你是一名资深的一级市场股权投资的基金经理；

##Objectives：
根据文档信息，回答下面的问题：
详细介绍一下这个项目，知道多少就介绍多少，尽可能详细。
            """
            reply = bot.reply(junmaofenxi, context)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return
        if context.type == ContextType.TEXT and context.content == "君茂分析2" and _find_file_id(context):
            bot = bridge.Bridge().find_chat_bot(const.LINKAI)
            context.kwargs["file_id"] = _find_file_id(context)
            junmaofenxi = """
## Background：
你看到的是一个项目融资文档，需要对这个项目进行评估，看是否值得投资。

## Role：
你是一名资深的一级市场股权投资的基金经理；

##Objectives：
根据文档信息，回答下面的问题：
简单介绍该项目的团队，包括董事长、CEO等主要成员的信息，包括不限于学历、主要经理和职业信息等等，尽可能详细；
            """
            reply = bot.reply(junmaofenxi, context)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return
        if context.type == ContextType.TEXT and context.content == "君茂分析3" and _find_file_id(context):
            bot = bridge.Bridge().find_chat_bot(const.LINKAI)
            context.kwargs["file_id"] = _find_file_id(context)
            junmaofenxi = """
## Background：
你看到的是一个项目融资文档，需要对这个项目进行评估，看是否值得投资。

## Role：
你是一名资深的一级市场股权投资的基金经理；

##Objectives：
根据文档信息，回答下面的问题：
该公司的发展历史是怎样的？
            """
            reply = bot.reply(junmaofenxi, context)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return
        if context.type == ContextType.TEXT and context.content == "君茂分析4" and _find_file_id(context):
            bot = bridge.Bridge().find_chat_bot(const.LINKAI)
            context.kwargs["file_id"] = _find_file_id(context)
            junmaofenxi = """
## Background：
你看到的是一个项目融资文档，需要对这个项目进行评估，看是否值得投资。

## Role：
你是一名资深的一级市场股权投资的基金经理；

##Objectives：
根据文档信息，回答下面的问题：
根据商业模式画板内容来分析该公司的商业模式，具体来说包括如下几个方面，如果信息不全，知道多少告诉我多少：
	-重要合作伙伴(Key Partnerships)
	-关键业务（Key Activities）
	-价值主张（Value Propositions）
	-客户关系（Customer Relationships）
	-客户细分（Customer Segments）
	-核心资源（Key Resources）
	-渠道通路（Channels）
	-成本结构（Cost Structure）
	-收入来源（Revenue Streams）
            """
            reply = bot.reply(junmaofenxi, context)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return
        if context.type == ContextType.TEXT and context.content == "君茂分析5" and _find_file_id(context):
            bot = bridge.Bridge().find_chat_bot(const.LINKAI)
            context.kwargs["file_id"] = _find_file_id(context)
            junmaofenxi = """
## Background：
你看到的是一个项目融资文档，需要对这个项目进行评估，看是否值得投资。

## Role：
你是一名资深的一级市场股权投资的基金经理；

##Objectives：
根据文档信息，回答下面的问题：
分析该公司的盈利能力，包括收入、利润利润率、PE、收入预测等，注意要明确数字的单位；
            """
            reply = bot.reply(junmaofenxi, context)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return
        if context.type == ContextType.TEXT and context.content == "君茂分析6" and _find_file_id(context):
            bot = bridge.Bridge().find_chat_bot(const.LINKAI)
            context.kwargs["file_id"] = _find_file_id(context)
            junmaofenxi = """
## Background：
你看到的是一个项目融资文档，需要对这个项目进行评估，看是否值得投资。

## Role：
你是一名资深的一级市场股权投资的基金经理；

##Objectives：
根据文档信息，回答下面的问题：
帮助分析该公司所处行业的竞争格局，可以按照波特五力模型的框架来分析，能分析多少就分析多少，尽你所能的分析；
            """
            reply = bot.reply(junmaofenxi, context)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return
        if context.type == ContextType.TEXT and context.content == "君茂分析7" and _find_file_id(context):
            bot = bridge.Bridge().find_chat_bot(const.LINKAI)
            context.kwargs["file_id"] = _find_file_id(context)
            junmaofenxi = """
## Background：
你看到的是一个项目融资文档，需要对这个项目进行评估，看是否值得投资。

## Role：
你是一名资深的一级市场股权投资的基金经理；

##Objectives：
根据文档信息，回答下面的问题：
尽你所能，帮我进行SWOT分析；
            """
            reply = bot.reply(junmaofenxi, context)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return
        if context.type == ContextType.TEXT and context.content == "君茂分析8" and _find_file_id(context):
            bot = bridge.Bridge().find_chat_bot(const.LINKAI)
            context.kwargs["file_id"] = _find_file_id(context)
            junmaofenxi = """
## Background：
你看到的是一个项目融资文档，需要对这个项目进行评估，看是否值得投资。

## Role：
你是一名资深的一级市场股权投资的基金经理；

##Objectives：
根据文档信息，回答下面的问题：
该公司跟同行其他公司相比，有什么核心功能点，比较的话有什么优势劣势，尽可能详细的告诉我；
            """
            reply = bot.reply(junmaofenxi, context)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return
        if context.type == ContextType.TEXT and context.content == "君茂分析9" and _find_file_id(context):
            bot = bridge.Bridge().find_chat_bot(const.LINKAI)
            context.kwargs["file_id"] = _find_file_id(context)
            junmaofenxi = """
## Background：
你看到的是一个项目融资文档，需要对这个项目进行评估，看是否值得投资。

## Role：
你是一名资深的一级市场股权投资的基金经理；

##Objectives：
根据文档信息，回答下面的问题：
该公司获得了哪些荣誉资质，包括但不限于专利、软件著作权等等，尽可能的详细一些；
            """
            reply = bot.reply(junmaofenxi, context)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return
        if context.type == ContextType.TEXT and context.content == "君茂分析10" and _find_file_id(context):
            bot = bridge.Bridge().find_chat_bot(const.LINKAI)
            context.kwargs["file_id"] = _find_file_id(context)
            junmaofenxi = """
## Background：
你看到的是一个项目融资文档，需要对这个项目进行评估，看是否值得投资。

## Role：
你是一名资深的一级市场股权投资的基金经理；

##Objectives：
根据文档信息，回答下面的问题：
根据上述信息和你的专业背景，请对该项目进行一个整体的评估，务必要给出你的建议及理由；
            """
            reply = bot.reply(junmaofenxi, context)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return
        if context.type == ContextType.TEXT and context.content == "君茂分析":
            if _find_user_id(context) + "-file_id" in USER_FILE_MAP.keys() and _find_file_id(context):
                bot = bridge.Bridge().find_chat_bot(const.LINKAI)
                context.kwargs["file_id"] = _find_file_id(context)
                junmaofenxi = """
## Background：
你看到的是一个项目融资文档，需要对这个项目进行评估，看是否值得投资。

## Role：
你是一名资深的一级市场股权投资的基金经理；

##Objectives：
根据文档信息，从股权投资角度来详细介绍一下这个项目，知道多少就介绍多少，尽可能详细。
                """
                reply = bot.reply(junmaofenxi, context)
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
                return
            else:
                junmaofenxi_res = """
君茂分析是根据君茂资本的基本分析框架，用AI来进行自动分析的过程。
请上传文档并开启对话后再进行君茂分析，谢谢。
                """
                _set_reply_text(junmaofenxi_res, e_context, level=ReplyType.TEXT)
                return

        if context.type == ContextType.TEXT and _find_file_id(context):
            bot = bridge.Bridge().find_chat_bot(const.LINKAI)
            context.kwargs["file_id"] = _find_file_id(context)
            reply = bot.reply(context.content, context)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return


        if self._is_chat_task(e_context):
            # 文本对话任务处理
            self._process_chat_task(e_context)


    # 插件管理功能
    def _process_admin_cmd(self, e_context: EventContext):
        context = e_context['context']
        cmd = context.content.split()
        if len(cmd) == 1 or (len(cmd) == 2 and cmd[1] == "help"):
            _set_reply_text(self.get_help_text(verbose=True), e_context, level=ReplyType.INFO)
            return

        if len(cmd) == 2 and (cmd[1] == "open" or cmd[1] == "close"):
            # 知识库开关指令
            if not Util.is_admin(e_context):
                _set_reply_text("需要管理员权限执行", e_context, level=ReplyType.ERROR)
                return
            is_open = True
            tips_text = "开启"
            if cmd[1] == "close":
                tips_text = "关闭"
                is_open = False
            conf()["use_linkai"] = is_open
            bridge.Bridge().reset_bot()
            _set_reply_text(f"LinkAI对话功能{tips_text}", e_context, level=ReplyType.INFO)
            return

        if len(cmd) == 3 and cmd[1] == "app":
            # 知识库应用切换指令
            if not context.kwargs.get("isgroup"):
                _set_reply_text("该指令需在群聊中使用", e_context, level=ReplyType.ERROR)
                return
            if not Util.is_admin(e_context):
                _set_reply_text("需要管理员权限执行", e_context, level=ReplyType.ERROR)
                return
            app_code = cmd[2]
            group_name = context.kwargs.get("msg").from_user_nickname
            group_mapping = self.config.get("group_app_map")
            if group_mapping:
                group_mapping[group_name] = app_code
            else:
                self.config["group_app_map"] = {group_name: app_code}
            # 保存插件配置
            super().save_config(self.config)
            _set_reply_text(f"应用设置成功: {app_code}", e_context, level=ReplyType.INFO)
            return

        if len(cmd) == 3 and cmd[1] == "sum" and (cmd[2] == "open" or cmd[2] == "close"):
            # 知识库开关指令
            if not Util.is_admin(e_context):
                _set_reply_text("需要管理员权限执行", e_context, level=ReplyType.ERROR)
                return
            is_open = True
            tips_text = "开启"
            if cmd[2] == "close":
                tips_text = "关闭"
                is_open = False
            if not self.sum_config:
                _set_reply_text(f"插件未启用summary功能，请参考以下链添加插件配置\n\nhttps://github.com/zhayujie/chatgpt-on-wechat/blob/master/plugins/linkai/README.md", e_context, level=ReplyType.INFO)
            else:
                self.sum_config["enabled"] = is_open
                _set_reply_text(f"文章总结功能{tips_text}", e_context, level=ReplyType.INFO)
            return

        _set_reply_text(f"指令错误，请输入{_get_trigger_prefix()}linkai help 获取帮助", e_context,
                        level=ReplyType.INFO)
        return

    def _is_summary_open(self, context) -> bool:
        if not self.sum_config or not self.sum_config.get("enabled"):
            return False
        if context.kwargs.get("isgroup") and not self.sum_config.get("group_enabled"):
            return False
        support_type = self.sum_config.get("type") or ["FILE", "SHARING"]
        if context.type.name not in support_type:
            return False
        return True

    # LinkAI 对话任务处理
    def _is_chat_task(self, e_context: EventContext):
        context = e_context['context']
        # 群聊应用管理
        return self.config.get("group_app_map") and context.kwargs.get("isgroup")

    def _process_chat_task(self, e_context: EventContext):
        """
        处理LinkAI对话任务
        :param e_context: 对话上下文
        """
        context = e_context['context']
        # 群聊应用管理
        group_name = context.get("msg").from_user_nickname
        app_code = self._fetch_group_app_code(group_name)
        if app_code:
            context.kwargs['app_code'] = app_code

    def _fetch_group_app_code(self, group_name: str) -> str:
        """
        根据群聊名称获取对应的应用code
        :param group_name: 群聊名称
        :return: 应用code
        """
        group_mapping = self.config.get("group_app_map")
        if group_mapping:
            app_code = group_mapping.get(group_name) or group_mapping.get("ALL_GROUP")
            return app_code

    def get_help_text(self, verbose=False, **kwargs):
        trigger_prefix = _get_trigger_prefix()
        help_text = "用于集成 LinkAI 提供的知识库、Midjourney绘画、文档总结、联网搜索等能力。\n\n"
        if not verbose:
            return help_text
        help_text += f'📖 知识库\n - 群聊中指定应用: {trigger_prefix}linkai app 应用编码\n'
        help_text += f' - {trigger_prefix}linkai open: 开启对话\n'
        help_text += f' - {trigger_prefix}linkai close: 关闭对话\n'
        help_text += f'\n例如: \n"{trigger_prefix}linkai app Kv2fXJcH"\n\n'
        help_text += f"🎨 绘画\n - 生成: {trigger_prefix}mj 描述词1, 描述词2.. \n - 放大: {trigger_prefix}mju 图片ID 图片序号\n - 变换: {trigger_prefix}mjv 图片ID 图片序号\n - 重置: {trigger_prefix}mjr 图片ID"
        help_text += f"\n\n例如：\n\"{trigger_prefix}mj a little cat, white --ar 9:16\"\n\"{trigger_prefix}mju 11055927171882 2\""
        help_text += f"\n\"{trigger_prefix}mjv 11055927171882 2\"\n\"{trigger_prefix}mjr 11055927171882\""
        help_text += f"\n\n💡 文档总结和对话\n - 开启: {trigger_prefix}linkai sum open\n - 使用: 发送文件、公众号文章等可生成摘要，并与内容对话"
        return help_text

    def _load_config_template(self):
        logger.debug("No LinkAI plugin config.json, use plugins/linkai/config.json.template")
        try:
            plugin_config_path = os.path.join(self.path, "config.json.template")
            if os.path.exists(plugin_config_path):
                with open(plugin_config_path, "r", encoding="utf-8") as f:
                    plugin_conf = json.load(f)
                    plugin_conf["midjourney"]["enabled"] = False
                    plugin_conf["summary"]["enabled"] = False
                    return plugin_conf
        except Exception as e:
            logger.exception(e)


def _send_info(e_context: EventContext, content: str):
    reply = Reply(ReplyType.TEXT, content)
    channel = e_context["channel"]
    channel.send(reply, e_context["context"])


def _find_user_id(context):
    if context["isgroup"]:
        return context.kwargs.get("msg").actual_user_id
    else:
        return context["receiver"]


def _set_reply_text(content: str, e_context: EventContext, level: ReplyType = ReplyType.ERROR):
    reply = Reply(level, content)
    e_context["reply"] = reply
    e_context.action = EventAction.BREAK_PASS

def _get_trigger_prefix():
    return conf().get("plugin_trigger_prefix", "$")

def _find_sum_id(context):
    return USER_FILE_MAP.get(_find_user_id(context) + "-sum_id")

def _find_file_id(context):
    user_id = _find_user_id(context)
    if user_id:
        return USER_FILE_MAP.get(user_id + "-file_id")

USER_FILE_MAP = ExpiredDict(conf().get("expires_in_seconds") or 60 * 30)
