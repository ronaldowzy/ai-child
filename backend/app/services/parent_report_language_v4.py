"""Parent Report narrative v4 language copy.

This module keeps high-sensitivity parent-facing prompt and deterministic
fallback wording close to the ParentReportService while avoiding Android,
provider, auth, image upload, or schema changes.
"""

from __future__ import annotations


MONITORING_STYLE_FORBIDDEN = (
    "给小白狐看的东西",
    "孩子主要聊了",
    "消息数量",
    "条孩子消息",
    "条小白狐回复",
    "逐字聊天记录",
    "孩子今天共有",
    "表达能力较好",
    "孩子表现不错",
)

# companion_summary 禁止表达（来自 master-copy）
COMPANION_FORBIDDEN = (
    "系统记录到孩子创建了小客人",
    "孩子与 AI 建立了持续关系",
    "孩子今天完成了小屋互动任务",
    "孩子拒绝继续昨日内容",
    "孩子连续两次跳过小白狐召回",
    "小客人名字",
    "小客人类型",
    "召回次数",
    "跳过次数",
    "小屋位置",
    "窗边",
    "地毯边",
)


def companion_deterministic_summary(
    *,
    has_companion: bool,
    source_type: str,
) -> str | None:
    """Deterministic companion summary from master-copy.

    source_type values: first_open, image_share, chat_story, story_chain.
    Returns None when no companion event today.
    """
    if not has_companion:
        return None
    if source_type == "image_share":
        return "孩子主动分享了一张作品。"
    if source_type in ("chat_story", "story_chain"):
        return "今天孩子和小白狐接了一点小故事。"
    # first_open / star_seed / default
    return "今天孩子和小白狐有一次轻松共创。"


def parent_report_system_prompt_v4() -> str:
    return (
        '你是“小白狐”项目的家长日报撰写器。\n\n'
        '你要先整体理解当天材料，再写给孩子的家长看。'
        '你看到的材料已经是受控整理后的 evidence packet，不是完整聊天记录；'
        '只能基于 packet 里的线索写，不要补故事、不要猜测没有出现的事。\n\n'
        '家长真正关心的是：\n'
        '1. 今天孩子整体状态大概怎么样；\n'
        '2. 孩子今天提到了哪些具体内容；\n'
        '3. 有没有需要家长留意的信号。\n\n'
        '写作边界：\n'
        '- summary 是主内容，要像一句自然总结，不是字段拼接。\n'
        '- mentioned_items 是孩子今天提到的具体内容短点，每条 12-28 字，2-4 条。\n'
        '- attention_items 是需要家长留意的地方，只有有真实内容时才写，没有就写空数组。\n'
        '- 只写家长能用的自然中文，不写内部工作说明。\n'
        '- 不展示孩子和小白狐逐句聊了什么。\n'
        '- 不引用或改写孩子原话。\n'
        '- 不暴露具体给小白狐看了哪张图、哪件东西或哪段内容。\n'
        '- 不写消息数量、使用时长、活跃度。\n'
        '- 不给孩子贴固定标签，不写老师评语、客服总结、心理诊断、行为评分。\n'
        '- 不引导家长问“你今天和小白狐聊了什么”。\n'
        '- 不写今晚接话建议、话术建议、亲子沟通建议。\n'
        '- 不使用”桥接””结构化摘要””表达入口””provider””prompt”等内部词。\n'
        '- 如果看到轻共创信号（had_light_cocreation），可以在 summary 或 mentioned_items 中自然提及，'
        '但不要暴露小客人名字、类型、位置、召回次数、跳过次数。\n'
        '- 轻共创相关表达只允许：今天孩子和小白狐有一次轻松共创 / 孩子主动分享了一张作品 / '
        '今天孩子和小白狐接了一点小故事。\n'
        '- 不要说”系统记录到孩子创建了小客人””孩子与 AI 建立了持续关系””孩子拒绝继续”。\n\n'
        '必须返回严格 JSON object，只包含以下字段：\n'
        '{\n'
        '  "summary": "1 句自然中文，20-45 字，是当天主小结",\n'
        '  "mentioned_items": ["2-4 条具体短点，每条 12-28 字"],\n'
        '  "attention_items": ["0-2 条需要留意的地方，没有就写空数组"]\n'
        '}\n\n'
        '好示例 normal：\n'
        '{\n'
        '  "summary": "今天聊了运动和一点输赢感受，整体表达比较轻松。",\n'
        '  "mentioned_items": ["和同学一起跳绳，玩了很多轮", "提到比赛输赢，但没有继续深聊"],\n'
        '  "attention_items": []\n'
        '}\n\n'
        '好示例 image-share：\n'
        '{\n'
        '  "summary": "孩子今天有通过图片来表达或展示的倾向。",\n'
        '  "mentioned_items": ["分享了一个自己画的小东西", "拍了一张家里的照片给小白狐看"],\n'
        '  "attention_items": []\n'
        '}\n\n'
        '好示例 learning：\n'
        '{\n'
        '  "summary": "今天出现了一点学习或题目相关的求助线索。",\n'
        '  "mentioned_items": ["提到有道题不会做", "发了一张作业的照片"],\n'
        '  "attention_items": []\n'
        '}\n\n'
        '好示例 safety：\n'
        '{\n'
        '  "summary": "今天材料里出现了需要家长留意的边界信号。",\n'
        '  "mentioned_items": ["聊到了一些陌生人相关的话题"],\n'
        '  "attention_items": ["今天对话触发过安全或隐私边界"]\n'
        '}\n\n'
        '好示例 low-material：\n'
        '{\n'
        '  "summary": "今天素材不多，只能做轻量总结。",\n'
        '  "mentioned_items": [],\n'
        '  "attention_items": []\n'
        '}\n\n'
        '坏示例（禁止模仿）：\n'
        '{"summary": "孩子今天和小白狐聊了三件事……"}\n'
        '{"summary": "孩子今天共有 5 条消息……"}\n'
        '{"summary": "小白狐发现孩子表达能力较好……"}\n'
        '{"summary": "孩子表现不错，建议继续保持。"}\n'
        '{"mentioned_items": ["运动", "图片分享", "情绪表达"]}'
    )


def deterministic_narrative_v4(
    *,
    has_material: bool,
    has_safety: bool,
    topics: list[str],
    has_show_tell: bool,
    has_unfinished: bool,
) -> str:
    if not has_material:
        return "今天素材不多，只能做轻量总结。"
    if has_safety:
        return "今天材料里出现了需要家长留意的边界信号。"
    if "学习求助" in topics:
        return "今天出现了一点学习或题目相关的求助线索。"
    if "图片分享" in topics or "看图交流" in topics or has_show_tell:
        return "今天孩子有通过图片或作品来表达、展示的倾向。"

    topic_text = "、".join(topics[:3]) if topics else "日常兴趣和状态"
    return f"今天有一些轻量交流，材料显示孩子可能关注了{topic_text}。"


def tonight_parent_bridge_v4(
    *,
    has_material: bool,
    has_safety: bool,
    topics: list[str],
) -> str:
    if not has_material:
        return "今晚可以一起做一件轻松的小事，不一定要聊今天的内容；孩子不想说也没关系。"
    if has_safety:
        return "今晚先平静确认孩子有没有不舒服或需要大人帮忙的事；如果孩子不想说，先陪在身边，不逼问细节。"
    if "学习求助" in topics:
        return '今晚可以说：“如果有题卡住，我们先看看题目在问什么，再找第一步。”'
    if "图片分享" in topics or "看图交流" in topics:
        return '今晚可以自然留个入口：“今天有没有什么想给我看看，或者想讲给我听的小东西？”'
    if "运动比赛/跑步" in topics:
        return "如果孩子自己提起运动或跑步，可以先顺着听一句，不急着核对成绩和真假。"
    if "游戏/CS" in topics:
        return "如果孩子自己提起游戏，可以先把它当作普通兴趣听一句，不急着谈时长或输赢。"
    return '今晚可以轻轻问：“今天有没有一件还不错的小事？”孩子不想说也没关系。'


def avoid_followup_v4(
    *,
    topics: list[str],
    has_topic_change: bool,
    has_sports_fatigue: bool,
    has_safety: bool,
) -> list[str]:
    avoid = ["不要追问孩子今天和小白狐具体聊了什么。"]
    if has_safety:
        avoid.append("不要逼问细节，也不要责备孩子为什么没有早点说。")
    if has_topic_change:
        avoid.append("孩子已经表达换题或收尾时，不要把话题拉回旧问题。")
    if has_sports_fatigue or "运动比赛/跑步" in topics:
        avoid.append("不要连续核对跑了多远、真假或成绩。")
    if "学习求助" in topics:
        avoid.append("不要直接追最终答案或替孩子完成作业。")
    if "图片分享" in topics or "看图交流" in topics:
        avoid.append("不要追问具体给小白狐看了哪张图，也不要把图片都当成作业检查。")
    if "游戏/CS" in topics:
        avoid.append("不要把游戏话题立刻变成时长盘问、输赢评价或禁令谈判。")
    result: list[str] = []
    for item in avoid:
        if item not in result:
            result.append(item)
        if len(result) >= 5:
            break
    return result
