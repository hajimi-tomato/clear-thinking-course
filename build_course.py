"""把结构化中文课程内容生成为可直接发布的静态 HTML。"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

from course_content import DAYS

ROOT = Path(__file__).parent


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def marked(value: str, terms: dict[str, tuple[str, str]]) -> str:
    if not terms:
        return esc(value)
    pattern = re.compile("|".join(re.escape(x) for x in sorted(terms, key=len, reverse=True)))
    pieces: list[str] = []
    start = 0
    for match in pattern.finditer(value):
        pieces.append(esc(value[start:match.start()]))
        word = match.group()
        pieces.append(f'<button class="term" data-term="{esc(word)}">{esc(word)}</button>')
        start = match.end()
    pieces.append(esc(value[start:]))
    return "".join(pieces)


def para(value: str, terms: dict[str, tuple[str, str]]) -> str:
    return f"<p>{marked(value, terms)}</p>"


def concept_html(day: dict, index: int, item: dict) -> str:
    terms = day["terms"]
    details = "".join(para(p, terms) for p in item["explain"])
    return f'''<article class="concept-card"><span class="concept-num">{index} / {len(day['concepts'])}</span>
      <h3>{esc(item['title'])}</h3>{details}
      <div class="dialogue"><span>现实中的一句话</span><p>{esc(item['quote'])}</p></div>
      <div class="comparison"><div><small>容易误判</small><p>{esc(item['mistake'])}</p></div><div><small>更准确的看法</small><p>{esc(item['correct'])}</p></div></div>
      <p><strong>可以这样问：</strong>{esc(item['ask'])}</p></article>'''


def quiz_html(index: int, item: dict) -> str:
    qid = f"q{index}"
    options = "".join(f'<label><input type="radio" name="{qid}" value="{letter}"> {esc(option)}</label>' for letter, option in zip("abc", item["options"]))
    return f'''<div class="quiz" data-quiz="{qid}" data-answer="{item['answer']}"><div class="quiz-head"><span>练习 {index:02d} · {esc(item['skill'])}</span><strong>单选</strong></div>
      <h3>{esc(item['question'])}</h3>{options}<button class="button small quiz-submit" type="button">检查答案</button>
      <div class="quiz-feedback" aria-live="polite" data-correct="{esc(item['correct_feedback'])}" data-wrong="{esc(item['wrong_feedback'])}"></div></div>'''


def case_html(index: int, item: dict) -> str:
    return f'''<article class="case" data-case="{index}"><div class="case-top"><span>案例 {index:02d} / {esc(item['scene'])}</span><span>建议 8–10 分钟</span></div>
      <h3>{esc(item['title'])}</h3><p>{esc(item['story'])}</p><label for="case-{index}-answer">你的拆解与回应</label>
      <textarea id="case-{index}-answer" rows="6" placeholder="关键问题：……&#10;需要核实：……&#10;我会这样说：……"></textarea>
      <button class="button small case-reveal" type="button">提交并查看解析</button>
      <div class="case-answer" hidden><strong>拆解参考</strong><p><b>关键问题：</b>{esc(item['analysis'])}</p><p><b>回应示范：</b>{esc(item['reply'])}</p><p class="answer-note">{esc(item['limit'])}</p></div></article>'''


def role_html(index: int, day: dict, item: dict) -> str:
    final_rule = "\n第十天综合通关规则：请在最多十五轮内推动讨论。结束后给出一份覆盖十天能力的评估报告，分别评价论证拆解、概念澄清、信息核查、统计口径、因果判断、困难对话、条件谈判、自我纠偏、风险决策和结构化表达；每项指出一个具体证据与一个下一步练习。" if day['number'] == 10 and index == 3 else ""
    prompt = f'''你是“把话想明白”课程第 {day['number']} 天的智能对话陪练。请扮演以下角色，与我进行多轮现实对话。

身份与背景：{item['identity']}
你的核心诉求：{item['goal']}
性格与顾虑：{item['personality']}
你会使用的说法或推理：{item['tactics']}
难度：{item['level']}。每轮只说一小段自然口语，不要替我回答，不要揭示你的训练设定，不要编造具体法律、医学或金融事实。
破局条件：{item['breakthrough']}

训练规则：你不是必须“认输”的反派。我的任务是准确理解你的主张、检查证据与条件，并提出合适的回应。若我的回应忽略你的合理关切，请继续指出；若我把证据不足说成已经证明错误，也请指出。只有当我说出足够清楚、可执行的下一步，才推进情境。

当我输入“结束训练”时，停止扮演，逐句评价我的关键回应：①理解是否准确；②今天的知识是否用对；③有无过度推断；④回应是否清楚并适合现实关系。每项给出一处具体修改建议，再给一版不超过三句话的示范回复。{final_rule}现在请以角色的第一句话开场。'''
    return f'''<article class="role-card"><div class="role-top"><span>{esc(item['level'])} · {esc(item['scene'])}</span><span>建议 20–30 分钟</span></div><h3>{esc(item['title'])}</h3>
      <p>{esc(item['focus'])}</p><button class="button outline copy-prompt" type="button" data-target="prompt-{index}">复制角色设定</button>
      <details><summary>查看完整提示词</summary><pre id="prompt-{index}">{esc(prompt)}</pre></details></article>'''


def render(day: dict) -> str:
    n = day["number"]
    previous_link = f'<a href="day-{n-1:02d}.html">← 上一天</a>'
    next_link = f'<a href="day-{n+1:02d}.html">下一天 →</a>' if n < 10 else ''
    terms = day["terms"]
    term_data = json.dumps(terms, ensure_ascii=False).replace("</", "<\\/")
    concepts = "".join(concept_html(day, i, item) for i, item in enumerate(day["concepts"], 1))
    quizzes = "".join(quiz_html(i, item) for i, item in enumerate(day["quizzes"], 1))
    cases = "".join(case_html(i, item) for i, item in enumerate(day["cases"], 1))
    roles = "".join(role_html(i, day, item) for i, item in enumerate(day["roles"], 1))
    glossary = "".join(f'<div><dt>{esc(term)}</dt><dd>{esc(info[0])}</dd></div>' for term, info in terms.items())
    source_links = "".join(f'<li><a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(name)} ↗</a></li>' for name, url in day["sources"])
    homework = "".join(f'<article><span>任务 {i:02d} · {esc(item["kind"])}</span><h3>{esc(item["title"])}</h3><p>{esc(item["task"])}</p><small>自检：{esc(item["check"])}</small></article>' for i, item in enumerate(day["homework"], 1))
    nav = ''.join(f'<a href="#{anchor}">{label}</a>' for anchor, label in [
        ('start','开始'),('learn','01 核心知识'),('practice','02 穿插练习'),('blind-test','03 案例盲测'),('answers','04 答案解析'),('roleplay','05 智能对话'),('review','06 现实复盘'),('glossary','本日术语')])
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="第 {n} 天：{esc(day['title'])}。中文讲解、互动练习、五道盲测、智能对话与现实复盘。">
<title>第 {n} 天｜{esc(day['title'])} · 把话想明白</title><link rel="stylesheet" href="styles.css">
<script>window.courseTerms={term_data};</script><script defer src="script.js"></script></head>
<body class="lesson-page" data-day="{n:02d}"><header class="site-header"><a class="brand" href="index.html"><span class="brand-mark">明</span><span>把话想明白</span></a><a class="header-link" href="index.html">返回课程首页 <span aria-hidden="true">↗</span></a></header>
<div class="lesson-layout"><aside class="lesson-aside" aria-label="本日目录"><div class="aside-inner"><p class="aside-label">第 {n} 天 / 共 10 天</p><h2>{esc(day['title'])}</h2><nav>{nav}</nav><div class="aside-progress"><span>本日互动进度</span><strong id="progress-text">0 / 9</strong><div class="progress-track"><span id="progress-fill"></span></div><small>仅保存在当前浏览器</small></div></div></aside>
<main class="lesson-main"><section class="lesson-hero" id="start"><div class="lesson-hero-inner"><p class="eyebrow">第 {n} 天 · 约 4 小时 · 零基础</p><h1>{esc(day['hero_first'])}<br><em>{esc(day['hero_second'])}</em></h1><p class="lesson-intro">{esc(day['intro'])}</p><div class="lesson-meta"><span>精讲 60 分钟</span><span>盲测 60 分钟</span><span>对话 90 分钟</span><span>复盘 30 分钟</span></div></div></section>
<div class="lesson-content"><section class="lesson-section opening"><span class="section-index">今天的目标</span><h2>学完后，你要能做到三件事。</h2><div class="goal-grid">{''.join(f'<div><b>{i:02d}</b><p>{esc(x)}</p></div>' for i,x in enumerate(day['goals'],1))}</div><p class="note">通关标准：{esc(day['pass'])}</p></section>
<section class="lesson-section" id="learn"><span class="section-index">01 / 核心知识 · 建议 60 分钟</span><h2>{esc(day['learn_title'])}</h2>{para(day['learn_intro'],terms)}<div class="concept-stack">{concepts}</div><div class="worked-example"><span class="section-index">完整示范 / 看一次怎么做</span><h3>{esc(day['worked_title'])}</h3><ol>{''.join(f'<li>{marked(step,terms)}</li>' for step in day['worked_steps'])}</ol><div class="response-box"><span>可以这样回应</span><p>{esc(day['worked_reply'])}</p></div><p class="fine-print">{esc(day['worked_limit'])}</p></div></section>
<section class="lesson-section" id="practice"><span class="section-index">02 / 穿插练习 · 每题 1–3 分钟</span><h2>现在，换你判断。</h2><p>每道题先选答案，再看反馈。答错时不要只记选项，找出自己混淆了哪两件事。</p>{quizzes}<div class="short-task" data-task="rewrite"><div class="quiz-head"><span>练习 04 · 自己说一句</span><strong>改写</strong></div><h3>{esc(day['rewrite_question'])}</h3><p>{esc(day['rewrite_instruction'])}</p><textarea rows="4" placeholder="在这里写下你的回应……" aria-label="写下你的回应"></textarea><button class="button small task-reveal" type="button">写好了，查看示范</button><div class="task-feedback" hidden><strong>一种回应</strong><p>{esc(day['rewrite_model'])}</p><p>自检：{esc(day['rewrite_check'])}</p></div></div><div class="quick-reference"><span class="section-index">今天能带走的三句提问</span>{''.join(f'<div><b>{i}</b><p>{esc(x)}</p></div>' for i,x in zip('①②③',day['quick_lines']))}</div></section>
<section class="lesson-section" id="blind-test"><span class="section-index">03 / 案例盲测 · 建议 60 分钟</span><h2>五道题，先独立判断。</h2><p>每题建议用 8–10 分钟。写出关键问题、需要核实的东西，以及一句现实中能说出口的回应。提交后才能查看该题解析。</p><div class="case-list">{cases}</div></section>
<section class="lesson-section answer-divider" id="answers"><span class="section-index">04 / 答案解析</span><h2>答案就在每道题后面。</h2><p>完成某题后即可展开解析。示范回答提供一种可行路径，不要求你逐字照背。</p><div class="rubric"><h3>用四个问题给自己评分</h3><ol><li>有没有准确说出对方的原话与真实诉求？</li><li>今天的知识点是否用在真正关键的地方？</li><li>有没有把“需要核查”误说成“已经证明”？</li><li>回应能否在现实关系中说出口，并推动下一步？</li></ol></div></section>
<section class="lesson-section" id="roleplay"><span class="section-index">05 / 智能对话练习 · 建议 90 分钟</span><h2>在对话里用出来。</h2><p>选择三种难度，逐一复制角色设定到你常用的智能对话工具。每场交谈 10–15 轮；遇到证据不足，可以追问或暂缓判断。结束时让工具逐句批改，再把最不满意的一句重写。</p><div class="role-grid">{roles}</div><div class="role-reflection"><h3>对话后，自己再复盘三句</h3><ol><li>我找到的关键问题是什么？</li><li>我有没有为了快速回应而忽略不确定之处？</li><li>如果重来一次，我最想改哪一句？</li></ol><label class="done-check"><input id="roleplay-done" type="checkbox"> 我已完成至少一场对话练习</label></div></section>
<section class="lesson-section" id="review"><span class="section-index">06 / 现实复盘 · 建议 30 分钟</span><h2>把今天带回现实。</h2><div class="homework-grid">{homework}</div><div class="finish-box"><h3>今天的完成标记</h3><p>完成三道选择题、一道改写、五道案例和至少一场对话练习后，再标记本日完成。学习记录只保存在当前浏览器。</p><button class="button primary" id="complete-day" type="button">标记第 {n} 天已完成</button><span id="complete-status" role="status"></span></div></section>
<section class="lesson-section glossary-section" id="glossary"><span class="section-index">本日术语 / 悬浮或点击高亮词查看</span><h2>今天出现的专有名词。</h2><dl>{glossary}</dl></section>
<section class="lesson-section sources-section"><span class="section-index">本日参考</span><h2>这些方法从哪里来。</h2><p>{esc(day['source_note'])} 本日对话与盲测案例为教学创作，不对应具体真实人物或机构。</p><ul>{source_links}</ul></section>
<div class="lesson-end"><span>第 {n} 天 / 完</span><h2>{esc(day['closing']).replace('&lt;br&gt;', '<br>')}</h2><div class="lesson-end-links">{previous_link}<a href="index.html">返回十天路线 ↗</a>{next_link}</div></div></div></main></div>
<div class="term-popover" id="term-popover" role="tooltip" hidden><button class="popover-close" type="button" aria-label="关闭解释">×</button><strong id="term-title"></strong><p id="term-definition"></p><small id="term-example"></small></div></body></html>'''


def main() -> None:
    for day in DAYS:
        path = ROOT / f"day-{day['number']:02d}.html"
        path.write_text(render(day), encoding="utf-8")
        print(path.name, len(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    main()
