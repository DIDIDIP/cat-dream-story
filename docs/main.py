# 고양이의 꿈 일기 · 웹 버전 (PyScript)
# ====================================================================
# cat_dream_story.py(tkinter 버전)와 같은 게임을 브라우저에서 돌립니다.
# 바뀐 점은 "화면을 그리는 방법"뿐입니다.
#   tkinter 창·버튼  → HTML 버튼 (index.html)
#   tkinter Canvas   → SVG 그림 (글자로 된 그림 설명을 만들어 화면에 넣음)
#   window.after     → 브라우저의 setTimeout
#   work/ 폴더 파일   → 브라우저 저장소 localStorage (최고 점수)
# 게임 규칙(장면·선택지·수치·결말)은 데스크톱 버전과 똑같습니다.

import json
import random

from pyodide.ffi import create_proxy      # 파이썬 함수를 브라우저가 부를 수 있게 포장
from pyscript import document, window

# ---------- 설정값 ----------
MAX_CHOICES = 3
PREP_SECONDS = 60
MAX_ITEMS = 2
STAT_MAX = 6
START_STATS = {"courage": 1, "full": 1, "sleepy": 4}
STAT_NAMES = {"courage": "용기", "full": "배부름", "sleepy": "졸음"}
BEST_KEY = "cat-dream-story-best"

ITEMS = {
    "열쇠": "어딘가의 문을 열 수 있을지도",
    "손전등": "어두운 곳에서 쓸모 있음",
    "생선 간식": "누군가와 나눠 먹을 수 있음",
    "털실 공": "놀이 친구를 사귈 때 좋음",
    "방울": "딸랑딸랑, 멀리까지 들림",
}

SCENES = {
    "door": {
        "title": "수상한 문", "sky": "#2b2257",
        "text": "꿈속 복도 끝에 반짝이는 수상한 문이 있어요. 문틈으로 바람이 솔솔 불어와요.",
        "choices": [
            {"label": "열쇠로 문을 연다", "need": "열쇠", "effect": {"courage": 1, "sleepy": -2},
             "result": "철컥! 문 너머에서 아침 햇살 냄새가 나요. 잠이 확 달아났어요."},
            {"label": "앞발로 문을 긁는다", "need": None, "effect": {"courage": 1},
             "result": "드르륵드르륵… 문은 꿈쩍도 안 하지만 조금 용감해진 기분이에요."},
            {"label": "문 앞에서 식빵 자세로 쉰다", "need": None, "effect": {"sleepy": 2},
             "result": "따뜻한 바람에 스르르… 꿈이 더 깊어졌어요."},
        ]},
    "river": {
        "title": "생선이 헤엄치는 강", "sky": "#1f3a5f",
        "text": "은빛 생선이 헤엄치는 강이 나타났어요. 배에서 꼬르륵 소리가 나요.",
        "choices": [
            {"label": "앞발로 생선을 낚아챈다", "need": None, "effect": {"full": 2, "sleepy": 1},
             "result": "냠냠! 배는 불렀지만 졸음이 쏟아져요."},
            {"label": "생선 간식을 나눠 준다", "need": "생선 간식", "effect": {"courage": 1, "sleepy": -2},
             "result": "고마워진 물고기들이 '이쪽이 출구야!' 하고 길을 알려 줬어요."},
            {"label": "강가에 앉아 구경한다", "need": None, "effect": {"sleepy": 1},
             "result": "찰랑찰랑 물결 소리가 자장가 같아요…"},
        ]},
    "cave": {
        "title": "깜깜한 동굴", "sky": "#141020",
        "text": "앞이 하나도 안 보이는 깜깜한 동굴이에요. 어디선가 똑, 똑 물방울 소리가 나요.",
        "choices": [
            {"label": "손전등을 켠다", "need": "손전등", "effect": {"courage": 1, "sleepy": -2},
             "result": "환해졌어요! 동굴 끝에 빛나는 출구가 보여요."},
            {"label": "수염으로 더듬으며 간다", "need": None, "effect": {"courage": 1},
             "result": "수염 레이더 작동! 조심조심 동굴을 빠져나왔어요."},
            {"label": "무서워서 몸을 웅크린다", "need": None, "effect": {"courage": -1, "sleepy": 1},
             "result": "웅크리고 있다가 그만 더 깊이 잠들었어요."},
        ]},
    "yarn": {
        "title": "집채만 한 털실 공", "sky": "#3d2a5c",
        "text": "집채만 한 털실 공이 데굴데굴 굴러와요. 놀고 싶어서 꼬리가 씰룩거려요.",
        "choices": [
            {"label": "털실 공과 신나게 논다", "need": None, "effect": {"courage": 1, "sleepy": 1},
             "result": "신났지만 너무 놀아서 노곤노곤…"},
            {"label": "풀린 털실 끝을 따라간다", "need": None, "effect": {"sleepy": -1},
             "result": "털실 끝에 '기상 →' 이라고 적힌 표지판이 있었어요!"},
            {"label": "내 털실 공을 굴려 준다", "need": "털실 공", "effect": {"courage": 2, "sleepy": -1},
             "result": "작은 털실 공을 받은 큰 털실 공이 길을 비켜 줬어요. 의기양양!"},
        ]},
    "dog": {
        "title": "그림자 강아지", "sky": "#2a2a3a",
        "text": "커다란 그림자 강아지가 길을 막고 '왈!' 하고 짖어요.",
        "choices": [
            {"label": "하악! 하고 맞선다", "need": None, "effect": {"courage": 2, "sleepy": -1},
             "result": "그림자 강아지가 깜짝 놀라 도망갔어요. 심장이 두근두근, 잠이 깼어요."},
            {"label": "털실 공을 던져 준다", "need": "털실 공", "effect": {"courage": 1, "full": 1, "sleepy": -1},
             "result": "강아지가 털실을 쫓으며 꼬리를 흔들어요. 친구가 돼서 간식도 나눠 줬어요!"},
            {"label": "높은 곳으로 숨는다", "need": None, "effect": {"courage": -1, "sleepy": 1},
             "result": "숨어 있는 동안 꾸벅꾸벅 졸았어요…"},
        ]},
    "bed": {
        "title": "구름 침대", "sky": "#4a3f7a",
        "text": "폭신폭신한 구름 침대가 둥실 떠 있어요. 보기만 해도 눈꺼풀이 무거워져요.",
        "choices": [
            {"label": "구름 침대를 뛰어넘는다", "need": None, "effect": {"sleepy": -1},
             "result": "폴짝! 유혹을 이겨냈어요."},
            {"label": "꾹꾹이를 한다", "need": None, "effect": {"full": 1, "sleepy": 1},
             "result": "꾹꾹꾹… 기분은 최고인데 졸려요."},
            {"label": "그대로 눕는다", "need": None, "effect": {"sleepy": 3},
             "result": "쿨쿨… 아주 깊은 잠에 빠졌어요."},
        ]},
    "alarm": {
        "title": "멀리서 들리는 알람 소리", "sky": "#5b4a8a",
        "text": "멀리서 '따르릉…' 알람 소리가 들려요! 꿈속 마지막 선택이에요.",
        "choices": [
            {"label": "소리 나는 쪽으로 달린다", "need": None, "effect": {"sleepy": -2},
             "result": "헉헉! 소리가 점점 커져요."},
            {"label": "방울을 흔들어 대답한다", "need": "방울", "effect": {"courage": 1, "sleepy": -3},
             "result": "딸랑딸랑! 꿈과 현실이 이어졌어요."},
            {"label": "앞발로 귀를 막는다", "need": None, "effect": {"sleepy": 2},
             "result": "조용해졌어요… 그리고 다시 꿈속으로."},
        ]},
}
FINAL_SCENE = "alarm"
RANDOM_SCENES = [key for key in SCENES if key != FINAL_SCENE]

state = {}


# ====================================================================
# 1. 최고 점수 (브라우저 저장소)
# ====================================================================
def load_best():
    try:
        best = json.loads(window.localStorage.getItem(BEST_KEY) or "0")
        return best if isinstance(best, int) and best >= 0 else 0
    except Exception:          # 저장소를 쓸 수 없는 브라우저(비공개 모드 등)
        return 0


def save_best(score):
    try:
        window.localStorage.setItem(BEST_KEY, json.dumps(score))
    except Exception:
        pass


# ====================================================================
# 2. 게임 규칙 (데스크톱 버전과 같음)
# ====================================================================
def new_state():
    order = random.sample(RANDOM_SCENES, MAX_CHOICES - 1) + [FINAL_SCENE]
    return {"phase": "prep", "items": [], "stats": dict(START_STATS),
            "choices_left": MAX_CHOICES, "order": order, "index": 0,
            "time_left": PREP_SECONDS, "timer": None, "log": [], "blocked": 0,
            "ending": None, "best": load_best(), "new_best": False}


def current_scene():
    return SCENES[state["order"][state["index"]]]


def apply_effect(effect):
    parts = []
    for key, amount in effect.items():
        stats = state["stats"]
        stats[key] = max(0, min(STAT_MAX, stats[key] + amount))
        parts.append(f"{STAT_NAMES[key]} {amount:+d}")
    return ", ".join(parts)


def decide_ending():
    s = state["stats"]
    score = s["courage"] * 20 + s["full"] * 10 + (STAT_MAX - s["sleepy"]) * 15
    if s["sleepy"] <= 1 and s["courage"] >= 3:
        title, story, bonus, ok = "용감한 아침", "기지개를 쭉 켜고 번쩍 일어났어요. 오늘은 뭐든 할 수 있을 것 같아요!", 100, True
    elif s["sleepy"] <= 1:
        title, story, bonus, ok = "상쾌한 아침", "알람 소리에 눈을 떴어요. 창밖 햇살이 따뜻해요.", 60, True
    elif s["sleepy"] <= 3:
        title, story, bonus, ok = "비몽사몽 아침", "눈은 떴지만 아직 반쯤 꿈속… 하품이 멈추지 않아요.", 20, True
    elif s["courage"] == 0:
        title, story, bonus, ok = "끝나지 않는 악몽", "무서운 꿈속을 계속 헤매고 있어요. 다음엔 용기를 내 봐요.", 0, False
    else:
        title, story, bonus, ok = "끝나지 않는 꿈", "알람이 울렸지만 쿨쿨… 오늘은 지각이에요.", 0, False
    if s["full"] >= 4:
        story += " 배가 너무 불러서 입맛을 다시고 있어요."
    return title, story, score + bonus, ok


# ====================================================================
# 3. 그림 (SVG 글자로 그림을 만들어 화면에 넣습니다)
# ====================================================================
W, H = 660, 230
FONT = "Pretendard, Malgun Gothic, sans-serif"


def text(x, y, words, color, size, bold=True, anchor="middle"):
    weight = "700" if bold else "400"
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" '
            f'font-family="{FONT}" text-anchor="{anchor}" dominant-baseline="middle">{words}</text>')


def cat(x, y, awake=False):
    fur = "#f4a259"
    eyes = "• •" if awake else "ᴗ ᴗ"
    return (f'<ellipse cx="{x}" cy="{y - 18}" rx="26" ry="22" fill="{fur}"/>'
            f'<polygon points="{x - 24},{y - 28} {x - 16},{y - 54} {x - 5},{y - 36}" fill="{fur}"/>'
            f'<polygon points="{x + 24},{y - 28} {x + 16},{y - 54} {x + 5},{y - 36}" fill="{fur}"/>'
            f'<path d="M{x + 24} {y - 8} L{x + 42} {y - 30}" stroke="{fur}" stroke-width="6" stroke-linecap="round"/>'
            + text(x, y - 24, eyes, "#5a2d0c", 12) + text(x, y - 10, "ㅅ", "#5a2d0c", 11))


def stars(points):
    return "".join(text(x, y, "✦", "#fff5b8", 10, bold=False) for x, y in points)


def scene_object(key):
    if key == "door":
        return ('<rect x="380" y="60" width="90" height="140" fill="#8d6346" stroke="#ffd166" stroke-width="4"/>'
                '<circle cx="455" cy="133" r="5" fill="#ffd166"/>' + text(425, 48, "✦  ✦  ✦", "#ffd166", 12))
    if key == "river":
        waves = "".join(f'<path d="M220 {150 + i * 18} q40 -10 80 0 t80 0 t80 0 t80 0 t80 0" fill="none" '
                        f'stroke="#7fc8f8" stroke-width="3"/>' for i in range(4))
        fish = "".join(f'<ellipse cx="{x}" cy="138" rx="18" ry="8" fill="#dfe7ef"/>'
                       f'<polygon points="{x + 16},138 {x + 30},128 {x + 30},148" fill="#dfe7ef"/>' for x in (330, 470))
        return waves + fish
    if key == "cave":
        return ('<path d="M260 230 A170 170 0 0 1 600 230 Z" fill="#000" stroke="#3a3450" stroke-width="8"/>'
                + text(430, 160, "똑…    똑…", "#6b6b8a", 13, bold=False))
    if key == "yarn":
        rings = "".join(f'<circle cx="440" cy="130" r="{70 - i * 12}" fill="none" stroke="#ffb3cf" stroke-width="3" '
                        f'stroke-dasharray="{60 + i * 10} 30"/>' for i in range(5))
        return ('<circle cx="440" cy="130" r="80" fill="#e56b9b"/>' + rings
                + '<path d="M380 190 Q300 215 220 195" fill="none" stroke="#e56b9b" stroke-width="3"/>')
    if key == "dog":
        return ('<ellipse cx="450" cy="135" rx="90" ry="65" fill="#0d0d14"/>'
                '<circle cx="540" cy="90" r="40" fill="#0d0d14"/>'
                '<polygon points="510,60 520,20 540,58" fill="#0d0d14"/>'
                '<circle cx="546" cy="84" r="6" fill="#ff5e5e"/>' + text(470, 40, "왈!", "#fff", 20))
    if key == "bed":
        puffs = "".join(f'<circle cx="{440 + dx}" cy="{150 + dy}" r="{r}" fill="#f2eeff"/>'
                        for dx, dy, r in [(-60, 0, 40), (0, -20, 50), (60, 0, 40)])
        return puffs + text(440, 70, "z z z", "#d8d0ff", 20)
    if key == "alarm":
        return ('<circle cx="450" cy="110" r="50" fill="#ffd166" stroke="#7a5c00" stroke-width="4"/>'
                '<path d="M450 110 V78 M450 110 H474" stroke="#000" stroke-width="4"/>'
                '<circle cx="406" cy="62" r="14" fill="#ffd166" stroke="#7a5c00" stroke-width="3"/>'
                '<circle cx="494" cy="62" r="14" fill="#ffd166" stroke="#7a5c00" stroke-width="3"/>'
                + text(570, 70, "따르릉!", "#ffd166", 16))
    return ""


def draw():
    phase = state["phase"]
    if phase == "prep":
        body = ('<rect width="660" height="230" fill="#3b3168"/>'
                '<rect x="440" y="60" width="140" height="100" fill="#1d1640" stroke="#c9b8ff" stroke-width="4"/>'
                '<circle cx="510" cy="100" r="20" fill="#fff5b8"/>'
                '<rect x="60" y="160" width="240" height="40" fill="#c9b8ff"/>'
                + cat(180, 160) + text(330, 28, "잠들기 전 60초! 가방에 챙길 물건 2개를 고르세요", "#fff", 17))
    elif phase == "ending":
        title, story, score, ok = state["ending"]
        ink = "#7a3e00" if ok else "#ffffff"
        body = f'<rect width="660" height="230" fill="{"#ffe8a3" if ok else "#141020"}"/>'
        body += ('<circle cx="560" cy="230" r="80" fill="#ffb627"/>' if ok
                 else text(540, 190, "z  z  z", "#8f86c9", 28))
        body += cat(160, 200, awake=ok) + text(330, 46, title, ink, 28)
        body += f'<foreignObject x="70" y="66" width="520" height="44"><div xmlns="http://www.w3.org/1999/xhtml" ' \
                f'style="color:{ink};font:14px {FONT};text-align:center">{story}</div></foreignObject>'
        body += text(330, 128, f"점수 {score}" + ("  ·  최고 기록!" if state["new_best"] else ""), ink, 17)
    else:
        key = state["order"][state["index"]]
        scene = SCENES[key]
        body = (f'<rect width="660" height="230" fill="{scene["sky"]}"/>'
                + stars([(30, 30), (110, 70), (200, 20), (300, 55), (590, 30), (560, 200)])
                + scene_object(key) + cat(130, 200)
                + text(16, 24, f'{state["index"] + 1}번째 꿈 · {scene["title"]}', "#fff", 18, anchor="start"))
    document.getElementById("stage").innerHTML = (
        f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="꿈 장면 그림">{body}</svg>')


# ====================================================================
# 4. 화면 갱신
# ====================================================================
def el(name):
    return document.getElementById(name)


def bar(value):
    return "■" * value + "□" * (STAT_MAX - value)


def restart_animation(node, name):
    """같은 애니메이션을 다시 보여 주려면 클래스를 뺐다가 다시 넣어야 합니다."""
    node.classList.remove(name)
    _ = node.offsetWidth                     # 브라우저가 한 번 다시 계산하게 만들기
    node.classList.add(name)


def refresh(message=None, color="#2b2257"):
    s = state["stats"]
    el("choices").textContent = "남은 선택 " + "●" * state["choices_left"] + "○" * (MAX_CHOICES - state["choices_left"])
    el("stats").textContent = f"용기 {bar(s['courage'])}   배부름 {bar(s['full'])}   졸음 {bar(s['sleepy'])}"
    el("bag").textContent = ("가방: " + (", ".join(state["items"]) if state["items"] else "(비어 있음)")
                             + f"   ·   최고 점수 {state['best']}")
    if message is not None:
        el("story").textContent = message
        el("story").style.color = color
    diary = el("diary")
    diary.innerHTML = ""
    for line in state["log"]:
        item = document.createElement("li")
        item.textContent = line
        diary.appendChild(item)
    draw()


def show_phase_frame():
    prep = state["phase"] == "prep"
    el("prep").hidden = not prep
    el("dream").hidden = prep


def set_choice_buttons():
    phase = state["phase"]
    for i in range(3):
        button = el(f"choice-{i}")
        letter = "ABC"[i]
        button.className = "choice"
        button.disabled = False
        if phase == "ending":
            button.innerHTML = f"[{letter}] 꿈이 끝났어요"
            button.classList.add("over")
            continue
        choice = current_scene()["choices"][i]
        need = f"<small>({choice['need']} 필요)</small>" if choice["need"] else ""
        button.innerHTML = f"[{letter}] {choice['label']}{need}"
        if choice["need"] and choice["need"] not in state["items"]:
            button.disabled = True
        elif phase == "result":
            button.classList.add("waiting")
    next_button = el("next")
    if phase == "result":
        next_button.disabled = False
        next_button.textContent = "결말 보기 ▶" if state["choices_left"] == 0 else "다음 꿈으로 ▶"
    else:
        next_button.disabled = True
        next_button.textContent = "다음 ▶"


# ====================================================================
# 5. 준비 단계 (60초)
# ====================================================================
def toggle_item(name):
    if state["phase"] != "prep":
        return
    items = state["items"]
    if name in items:
        items.remove(name)
    elif len(items) >= MAX_ITEMS:
        refresh(f"가방이 꽉 찼어요! 물건은 {MAX_ITEMS}개까지예요. 넣은 물건을 다시 누르면 뺄 수 있어요.", "#e63946")
        return
    else:
        items.append(name)
    for button in el("items").children:
        button.classList.toggle("picked", button.dataset.item in items)
    refresh(f"'{name}' {'챙겼어요' if name in items else '뺐어요'}. ({len(items)}/{MAX_ITEMS})")


def set_timer_label():
    label = el("timer")
    label.textContent = f"⏱ {state['time_left']}초"
    label.classList.toggle("hurry", state["time_left"] <= 10)


def tick(*_):
    if state["phase"] != "prep":
        return
    state["time_left"] -= 1
    set_timer_label()
    if state["time_left"] <= 0:
        while len(state["items"]) < MAX_ITEMS:
            state["items"].append(random.choice([i for i in ITEMS if i not in state["items"]]))
        state["log"].append("시간 끝! 허둥지둥 아무거나 가방에 넣었어요.")
        fall_asleep()
        return
    state["timer"] = window.setTimeout(tick_proxy, 1000)


def fall_asleep(*_):
    if state["phase"] != "prep":
        return
    if state["timer"]:
        window.clearTimeout(state["timer"])
        state["timer"] = None
    state["log"].append("가방: " + (", ".join(state["items"]) or "없음") + " → 스르르 잠들었어요.")
    state["phase"] = "scene"
    show_phase_frame()
    set_choice_buttons()
    refresh(current_scene()["text"])


# ====================================================================
# 6. 꿈 단계 (선택 → 결과 → 다음)
# ====================================================================
def choose(i):
    phase = state["phase"]
    if phase == "result":
        restart_animation(el("next"), "pulse")      # 결과를 읽는 중: '다음'을 먼저 누르라고 알려 줌
        return
    # ---- 돌발 상황: 선택 세 번을 다 쓴 뒤 누른 클릭 ----
    if phase == "ending" or state["choices_left"] == 0:
        state["blocked"] += 1
        state["log"].append(f"막힌 클릭 {state['blocked']}번: 꿈속 선택은 딱 세 번뿐이에요.")
        refresh("선택을 모두 썼어요! 꿈속에서는 딱 세 번만 고를 수 있어요. 다시 시작(R)을 눌러 주세요.", "#e63946")
        restart_animation(el("choices"), "flash")
        return
    if phase != "scene":
        return
    choice = current_scene()["choices"][i]
    if choice["need"] and choice["need"] not in state["items"]:
        refresh(f"가방에 '{choice['need']}'이(가) 없어서 고를 수 없어요.", "#e63946")
        return
    change = apply_effect(choice["effect"])
    state["choices_left"] -= 1
    state["log"].append(f"{state['index'] + 1}번째 꿈 · {current_scene()['title']}: {choice['label']} → {change}")
    state["phase"] = "result"
    set_choice_buttons()
    refresh(f"{choice['result']}\n({change})", "#0f766e")


def next_scene(*_):
    if state["phase"] != "result":
        return
    if state["choices_left"] == 0:
        show_ending()
        return
    state["index"] += 1
    state["phase"] = "scene"
    set_choice_buttons()
    refresh(current_scene()["text"])


def show_ending():
    state["phase"] = "ending"
    state["ending"] = decide_ending()
    title, story, score, ok = state["ending"]
    if score > state["best"]:
        state["best"] = score
        state["new_best"] = True
        save_best(score)
    state["log"].append(f"결말: {title} (점수 {score})")
    set_choice_buttons()
    refresh(f"{title} — {story}", "#b5651d" if ok else "#6b5fb5")


def restart(*_):
    if state.get("timer"):
        window.clearTimeout(state["timer"])
    state.clear()
    state.update(new_state())
    for button in el("items").children:
        button.classList.remove("picked")
    set_timer_label()
    show_phase_frame()
    refresh("고양이가 하품을 해요. 60초 안에 꿈속에 가져갈 물건을 챙겨 주세요!")
    state["timer"] = window.setTimeout(tick_proxy, 1000)


# ====================================================================
# 7. 버튼·키보드 연결
# ====================================================================
# create_proxy: 브라우저가 나중에 불러도 사라지지 않도록 파이썬 함수를 붙잡아 둡니다.
tick_proxy = create_proxy(tick)
handlers = []        # 만든 proxy를 모아 두어 지워지지 않게 합니다.


def on(node, event, function):
    proxy = create_proxy(function)
    handlers.append(proxy)
    node.addEventListener(event, proxy)


for name, desc in ITEMS.items():
    button = document.createElement("button")
    button.dataset.item = name
    button.innerHTML = f"<b>{name}</b>{desc}"
    on(button, "click", lambda event, n=name: toggle_item(n))
    el("items").appendChild(button)

for i in range(3):
    on(el(f"choice-{i}"), "click", lambda event, n=i: choose(n))
on(el("next"), "click", next_scene)
on(el("sleep"), "click", fall_asleep)
on(el("restart"), "click", restart)

KEYS = {"a": 0, "b": 1, "c": 2, "1": 0, "2": 1, "3": 2}


def on_key(event):
    if event.ctrlKey or event.metaKey or event.altKey:
        return
    key = event.key.lower()
    if key in KEYS:
        choose(KEYS[key])
    elif key in (" ", "enter"):
        event.preventDefault()           # 스페이스로 페이지가 내려가지 않게
        if state["phase"] == "prep":
            fall_asleep()
        else:
            next_scene()
    elif key == "r":
        restart()


on(document, "keydown", on_key)

# 준비 끝: 로딩 문구를 숨기고 게임을 보여 줍니다.
el("loading").hidden = True
el("game").hidden = False
restart()
