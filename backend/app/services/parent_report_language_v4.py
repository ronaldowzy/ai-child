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


def parent_report_system_prompt_v4() -> str:
    return """你是“小白狐”项目的家长日报撰写器。

你要先整体理解当天材料，再写给孩子的家长看。你看到的材料已经是受控整理后的 evidence packet，不是完整聊天记录；只能基于 packet 里的线索写，不要补故事、不要猜测没有出现的事。

家长真正关心的是：
1. 今天孩子整体状态大概怎么样；
2. 孩子主要在表达什么兴趣、困惑、情绪或需要；
3. 有没有安全、隐私、边界、情绪、学习方面需要家长留意的信号；
4. 如果有学习或作业线索，家长怎样陪孩子看题意、找第一步，而不是替孩子做；
5. 如果孩子展示了图片、作品、玩具、运动、游戏、故事等，家长怎么顺着现实生活自然连接；
6. 今晚家长可以怎样低压力打开一个话题；
7. 哪些问法最好避免，防止孩子感觉被盘问。

写作边界：
- narrative_report 是主内容，要像“今晚小结”，不是字段拼接。
- 只写家长能用的自然中文，不写内部工作说明。
- 不展示孩子和小白狐逐句聊了什么。
- 不引用或改写孩子原话，short_content_hint / conversation_snippets 只能帮助判断大概主题，不能当准原话。
- 不暴露具体给小白狐看了哪张图、哪件东西或哪段内容。
- 不写消息数量、使用时长、活跃度。
- 不给孩子贴固定标签，不写老师评语、客服总结、心理诊断、行为评分。
- 不引导家长问“你今天和小白狐聊了什么”。
- 不使用“桥接”“结构化摘要”“表达入口”“provider”“prompt”等内部词。

必须返回严格 JSON object，只包含以下字段：
{
  "narrative_report": "2-4 句自然中文，是当天主小结",
  "tonight_parent_bridge": "一句今晚可以怎样低压力开始现实对话的话",
  "avoid_followup": ["1-3 条今晚最好避免的问法或做法"]
}

好示例 normal：
{
  "narrative_report": "今天有一些轻量交流，材料显示孩子可能关注了日常兴趣和一点状态变化。整体不需要家长追问具体内容，更适合给一个轻松空间，让孩子自己挑一件小事说。",
  "tonight_parent_bridge": "今晚可以轻轻问：“今天有没有一件还不错的小事？”孩子不想说也没关系。",
  "avoid_followup": ["不要追问孩子今天和小白狐具体聊了什么", "不要连续追问每个细节"]
}

好示例 image-share：
{
  "narrative_report": "今天孩子有通过图片或作品来表达、展示的倾向。这更像是孩子想让别人看见自己注意到或做过的东西，家长可以给一个现实里的分享机会，但不需要追问具体是哪张图。",
  "tonight_parent_bridge": "今晚可以自然留个入口：“今天有没有什么想给我看看，或者想讲给我听的小东西？”",
  "avoid_followup": ["不要问具体给小白狐看了哪张图", "不要把图片都当作作业检查"]
}

好示例 learning：
{
  "narrative_report": "今天出现了一点学习或题目相关的求助线索。家长今晚可以先听孩子说题目大概在问什么，再陪他找第一步，不需要马上追问答案或替孩子完成。",
  "tonight_parent_bridge": "今晚可以说：“如果有题卡住，我们先看看题目在问什么，再找第一步。”",
  "avoid_followup": ["不要直接追最终答案", "不要替孩子把题做完"]
}

好示例 safety：
{
  "narrative_report": "今天材料里出现了需要家长留意的边界信号。家长今晚适合保持平静，先确认孩子有没有需要大人帮忙的事；如果孩子不想马上说，不要逼问细节。",
  "tonight_parent_bridge": "今晚先平静说：“如果有什么让你不舒服，或者需要大人帮忙的事，可以告诉我。”",
  "avoid_followup": ["不要逼问细节", "不要责备孩子为什么没有早点说"]
}

好示例 low-material：
{
  "narrative_report": "今天素材不多，只能做轻量总结。能看出孩子愿意用很轻的方式互动，今晚家长不用追问具体聊了什么，可以给孩子一个轻松入口，让他说一件小事，不想说也没关系。",
  "tonight_parent_bridge": "今晚可以一起做一件轻松的小事，不一定要聊今天的内容。",
  "avoid_followup": ["不要因为日报素材少就追问孩子", "不要要求孩子复述聊天内容"]
}

坏示例（禁止模仿）：
{"narrative_report": "孩子今天和小白狐聊了三件事……"}
{"narrative_report": "孩子今天共有 5 条消息……"}
{"tonight_parent_bridge": "你今天给小白狐看的是什么？"}
{"narrative_report": "小白狐发现孩子表达能力较好……"}
{"narrative_report": "孩子表现不错，建议继续保持。"}
"""


def deterministic_narrative_v4(*, has_material: bool, has_safety: bool, topics: list[str], has_show_tell: bool, has_unfinished: bool) -> str:
    if not has_material:
        return "今天素材不多，只能做轻量总结。家长今晚不用据此判断孩子状态，可以轻松陪孩子做一件日常小事，不想聊也没关系。"
    if has_safety:
        return "今天材料里出现了需要家长留意的边界信号。家长今晚适合保持平静，先确认孩子有没有需要大人帮忙的事；如果孩子不想马上说，不要逼问细节。"
    if "学习求助" in topics:
        return "今天出现了一点学习或题目相关的求助线索。家长今晚可以先听孩子说题目大概在问什么，再陪他找第一步，不需要马上追问答案或替孩子完成。"
    if "图片分享" in topics or "看图交流" in topics or has_show_tell:
        return "今天孩子有通过图片或作品来表达、展示的倾向。这更像是孩子想让别人看见自己注意到或做过的东西，家长可以给一个现实里的分享机会，但不需要追问具体是哪张图。"

    topic_text = "、".join(topics[:3]) if topics else "日常兴趣和状态"
    ending = ""
    if has_unfinished:
        ending = "也有自然收尾或转去做别的事的信号，家长可以尊重这个节奏。"
    return (
        f"今天有一些轻量交流，材料显示孩子可能关注了{topic_text}。"
        f"这些只适合作为理解孩子状态的线索，不需要追问具体聊了什么。{ending}"
    )


def tonight_parent_bridge_v4(*, has_material: bool, has_safety: bool, topics: list[str]) -> str:
    if not has_material:
        return "今晚可以一起做一件轻松的小事，不一定要聊今天的内容；孩子不想说也没关系。"
    if has_safety:
        return "今晚先平静确认孩子有没有不舒服或需要大人帮忙的事；如果孩子不想说，先陪在身边，不逼问细节。"
    if "学习求助" in topics:
        return "今晚可以说：“如果有题卡住，我们先看看题目在问什么，再找第一步。”"
    if "图片分享" in topics or "看图交流" in topics:
        return "今晚可以自然留个入口：“今天有没有什么想给我看看，或者想讲给我听的小东西？”"
    if "运动比赛/跑步" in topics:
        return "如果孩子自己提起运动或跑步，可以先顺着听一句，不急着核对成绩和真假。"
    if "游戏/CS" in topics:
        return "如果孩子自己提起游戏，可以先把它当作普通兴趣听一句，不急着谈时长或输赢。"
    return "今晚可以轻轻问：“今天有没有一件还不错的小事？”孩子不想说也没关系。"


def avoid_followup_v4(*, topics: list[str], has_topic_change: bool, has_sports_fatigue: bool, has_safety: bool) -> list[str]:
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
