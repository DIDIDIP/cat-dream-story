# 고양이의 꿈 일기 · 선택지 이야기 게임 ('60 Seconds!' 스타일)
# ====================================================================
# 미션 조합
#   장르: 미니 게임  → 준비 단계 + 장면마다 선택지를 고르는 이야기 게임
#   주어: 고양이     → 주인공. 꿈에서 깨어나 아침을 맞아야 함
#   공간: 꿈속       → 수상한 문, 생선 강, 깜깜한 동굴, 구름 침대 같은 꿈 장면들
#   돌발: 버튼을 딱 세 번만 누를 수 있다
#         → 꿈속에서 고를 수 있는 선택은 딱 세 번. 남은 선택 ●●●을 보여 주고,
#           세 번을 다 쓰면 선택 버튼이 잠기고 결말이 나옴.
#           네 번째로 누르면 깜빡이며 막히고, '다시 시작'은 언제나 가능
#
# 게임 흐름
#   1) 잠들기 전 60초: 가방에 물건 2개 챙기기 (시간이 다 되면 아무거나 챙겨짐)
#   2) 꿈 장면 3개: 무작위 장면 2개 + 마지막 '알람 소리' 장면
#      선택하면 결과가 나오고 '다음 ▶'으로 넘어감. 챙긴 물건이 있어야 고를 수 있는 선택지도 있음
#   3) 결말: 용기·배부름·졸음 수치에 따라 결말과 점수가 정해짐
#
# 실행: 이 파일이 있는 폴더의 터미널에서  python -X utf8 cat_dream_story.py
# 설치: 필요 없음
# 조작: 마우스 또는 키보드 (A·B·C = 선택, 스페이스 = 다음, R = 다시 시작)

import json
import random
import tkinter as tk
from pathlib import Path

# ---------- 설정값 ----------
MAX_CHOICES = 3          # 돌발 상황: 선택은 딱 세 번
PREP_SECONDS = 60        # 잠들기 전 준비 시간
MAX_ITEMS = 2            # 가방에 넣을 수 있는 물건 수
STAT_MAX = 6             # 수치의 최댓값
START_STATS = {"courage": 1, "full": 1, "sleepy": 4}
STAT_NAMES = {"courage": "용기", "full": "배부름", "sleepy": "졸음"}

BEST_FILE = Path(__file__).resolve().parent / "work" / "cat_story_best.json"

# 챙길 수 있는 물건: 이름 → 설명
ITEMS = {
    "열쇠": "어딘가의 문을 열 수 있을지도",
    "손전등": "어두운 곳에서 쓸모 있음",
    "생선 간식": "누군가와 나눠 먹을 수 있음",
    "털실 공": "놀이 친구를 사귈 때 좋음",
    "방울": "딸랑딸랑, 멀리까지 들림",
}

# 꿈 장면 모음.
# 선택지 하나 = {"label": 버튼 글자, "need": 필요한 물건(없으면 None),
#               "effect": 수치 변화, "result": 고른 뒤 나오는 이야기}
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
# 1. 최고 점수 파일
# ====================================================================
def load_best():
    try:
        with BEST_FILE.open("r", encoding="utf-8") as file:
            best = json.load(file).get("best", 0)
        return best if isinstance(best, int) and best >= 0 else 0
    except (FileNotFoundError, json.JSONDecodeError, AttributeError):
        return 0


def save_best(score):
    BEST_FILE.parent.mkdir(exist_ok=True)
    with BEST_FILE.open("w", encoding="utf-8") as file:
        json.dump({"best": score}, file, ensure_ascii=False)


# ====================================================================
# 2. 게임 규칙 (화면과 분리)
# ====================================================================
def new_state():
    # 이번 꿈의 장면 순서: 무작위 장면 2개 + 마지막 알람 장면
    order = random.sample(RANDOM_SCENES, MAX_CHOICES - 1) + [FINAL_SCENE]
    return {"phase": "prep", "items": [], "stats": dict(START_STATS),   # dict(...) = 복사본 만들기
            "choices_left": MAX_CHOICES, "order": order, "index": 0,
            "time_left": PREP_SECONDS, "timer": None, "log": [], "blocked": 0,
            "ending": None, "best": load_best(), "new_best": False}


def current_scene():
    return SCENES[state["order"][state["index"]]]


def apply_effect(effect):
    """수치를 바꾸고, '용기 +1, 졸음 -2' 같은 설명 글을 돌려줍니다. 수치는 0~6 사이로 유지."""
    parts = []
    for key, amount in effect.items():
        stats = state["stats"]
        stats[key] = max(0, min(STAT_MAX, stats[key] + amount))
        parts.append(f"{STAT_NAMES[key]} {amount:+d}")
    return ", ".join(parts)


def decide_ending():
    """마지막 수치로 결말을 정합니다. (제목, 이야기, 점수, 성공 여부)"""
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
# 3. 그림
# ====================================================================
W, H = 660, 230


def draw_cat(x, y, awake=False):
    c, fur = canvas, "#f4a259"
    c.create_oval(x - 26, y - 40, x + 26, y + 4, fill=fur, outline="")
    c.create_polygon(x - 24, y - 28, x - 16, y - 54, x - 5, y - 36, fill=fur)
    c.create_polygon(x + 24, y - 28, x + 16, y - 54, x + 5, y - 36, fill=fur)
    c.create_line(x + 24, y - 8, x + 42, y - 30, fill=fur, width=6, capstyle="round")
    c.create_text(x, y - 24, text="• •" if awake else "ᴗ ᴗ", fill="#5a2d0c", font=("Arial", 10, "bold"))
    c.create_text(x, y - 11, text="ㅅ", fill="#5a2d0c", font=("맑은 고딕", 9, "bold"))


def draw_object(key):
    """장면마다 다른 물건을 도형으로 그립니다."""
    c = canvas
    if key == "door":
        c.create_rectangle(380, 60, 470, 200, fill="#8d6346", outline="#ffd166", width=4)
        c.create_oval(450, 128, 460, 138, fill="#ffd166", outline="")
        c.create_text(425, 48, text="✦  ✦  ✦", fill="#ffd166")
    elif key == "river":
        for i in range(4):
            y = 150 + i * 18
            c.create_line(220, y, 300, y - 8, 380, y, 460, y - 8, 540, y, 600, y - 8,
                          smooth=True, fill="#7fc8f8", width=3)
        for x in (330, 470):
            c.create_oval(x - 18, 130, x + 18, 146, fill="#dfe7ef", outline="")
            c.create_polygon(x + 16, 138, x + 30, 128, x + 30, 148, fill="#dfe7ef")
    elif key == "cave":
        c.create_arc(260, 40, 600, 380, start=0, extent=180, fill="#000000", outline="#3a3450", width=8)
        c.create_text(430, 150, text="똑…    똑…", fill="#6b6b8a", font=("맑은 고딕", 11))
    elif key == "yarn":
        c.create_oval(360, 50, 520, 210, fill="#e56b9b", outline="")
        for i in range(5):
            c.create_arc(370 + i * 8, 60 + i * 6, 510 - i * 8, 200 - i * 6, start=20 * i, extent=140,
                         style="arc", outline="#ffb3cf", width=3)
        c.create_line(380, 190, 300, 205, 220, 195, smooth=True, fill="#e56b9b", width=3)
    elif key == "dog":
        c.create_oval(360, 70, 540, 200, fill="#0d0d14", outline="")
        c.create_oval(500, 50, 580, 130, fill="#0d0d14", outline="")
        c.create_polygon(510, 60, 520, 20, 540, 58, fill="#0d0d14")
        c.create_oval(540, 78, 552, 90, fill="#ff5e5e", outline="")
        c.create_text(470, 40, text="왈!", fill="#ffffff", font=("맑은 고딕", 16, "bold"))
    elif key == "bed":
        for dx, dy, r in [(-60, 0, 40), (0, -20, 50), (60, 0, 40)]:
            c.create_oval(440 + dx - r, 150 + dy - r, 440 + dx + r, 150 + dy + r, fill="#f2eeff", outline="")
        c.create_text(440, 70, text="z z z", fill="#d8d0ff", font=("Arial", 16, "bold"))
    elif key == "alarm":
        c.create_oval(400, 60, 500, 160, fill="#ffd166", outline="#7a5c00", width=4)
        c.create_line(450, 110, 450, 78, width=4)
        c.create_line(450, 110, 474, 110, width=4)
        c.create_oval(392, 48, 420, 76, fill="#ffd166", outline="#7a5c00", width=3)
        c.create_oval(480, 48, 508, 76, fill="#ffd166", outline="#7a5c00", width=3)
        c.create_text(560, 70, text="따르릉!", fill="#ffd166", font=("맑은 고딕", 13, "bold"))


def draw():
    c = canvas
    c.delete("all")
    phase = state["phase"]
    if phase == "prep":
        c.create_rectangle(0, 0, W, H, fill="#3b3168", outline="")
        c.create_rectangle(440, 60, 580, 160, fill="#1d1640", outline="#c9b8ff", width=4)   # 창문
        c.create_oval(490, 80, 530, 120, fill="#fff5b8", outline="")
        c.create_rectangle(60, 160, 300, 200, fill="#c9b8ff", outline="")                  # 침대
        draw_cat(180, 160)
        c.create_text(W / 2, 24, text="잠들기 전 60초! 가방에 챙길 물건 2개를 고르세요",
                      fill="white", font=("맑은 고딕", 13, "bold"))
        return
    if phase == "ending":
        title, story, score, ok = state["ending"]
        c.create_rectangle(0, 0, W, H, fill="#ffe8a3" if ok else "#141020", outline="")
        if ok:
            c.create_oval(480, 150, 640, 310, fill="#ffb627", outline="")                   # 떠오르는 해
        else:
            c.create_text(540, 190, text="z  z  z", fill="#8f86c9", font=("Arial", 22, "bold"))
        draw_cat(160, 190, awake=ok)
        ink = "#7a3e00" if ok else "#ffffff"
        c.create_text(W / 2, 46, text=title, fill=ink, font=("맑은 고딕", 22, "bold"))
        c.create_text(W / 2, 84, text=story, fill=ink, font=("맑은 고딕", 11), width=520)
        c.create_text(W / 2, 124, text=f"점수 {score}" + ("  ·  최고 기록!" if state["new_best"] else ""),
                      fill=ink, font=("맑은 고딕", 13, "bold"))
        return
    key = state["order"][state["index"]]
    scene = SCENES[key]
    c.create_rectangle(0, 0, W, H, fill=scene["sky"], outline="")
    for x, y in [(30, 30), (110, 70), (200, 20), (300, 55), (590, 30), (560, 200)]:
        c.create_text(x, y, text="✦", fill="#fff5b8", font=("Arial", 8))
    draw_object(key)
    draw_cat(130, 200)
    c.create_text(16, 16, anchor="nw", text=f"{state['index'] + 1}번째 꿈 · {scene['title']}",
                  fill="white", font=("맑은 고딕", 14, "bold"))


# ====================================================================
# 4. 화면 갱신
# ====================================================================
def bar(value):
    return "■" * value + "□" * (STAT_MAX - value)


def refresh(message=None, color="#2b2257"):
    s = state["stats"]
    choices_label.config(text="남은 선택 " + "●" * state["choices_left"] + "○" * (MAX_CHOICES - state["choices_left"]))
    stats_label.config(text=f"용기 {bar(s['courage'])}   배부름 {bar(s['full'])}   졸음 {bar(s['sleepy'])}")
    bag_label.config(text="가방: " + (", ".join(state["items"]) if state["items"] else "(비어 있음)")
                     + f"   ·   최고 점수 {state['best']}")
    if message is not None:
        story_label.config(text=message, fg=color)
    diary.delete(0, "end")
    for line in state["log"]:
        diary.insert("end", line)
    diary.see("end")
    draw()


def show_phase_frame():
    """준비 단계에는 물건 버튼을, 꿈 단계에는 선택 버튼을 보여 줍니다."""
    if state["phase"] == "prep":
        dream_frame.pack_forget()
        prep_frame.pack(pady=6, before=diary_title)
    else:
        prep_frame.pack_forget()
        dream_frame.pack(pady=6, before=diary_title)


def set_choice_buttons():
    """선택 버튼 3개의 글자와 색을 지금 장면·단계에 맞게 바꿉니다."""
    phase = state["phase"]
    for i, button in enumerate(choice_buttons):
        letter = "ABC"[i]
        if phase == "ending":
            button.config(text=f"[{letter}] (꿈이 끝났어요)", bg="#d6d6d6", fg="#888888", state="normal")
            continue
        choice = current_scene()["choices"][i]
        missing = choice["need"] and choice["need"] not in state["items"]
        label = f"[{letter}] {choice['label']}" + (f"\n({choice['need']} 필요)" if choice["need"] else "")
        if missing:                                    # 물건이 없으면 누를 수 없게
            button.config(text=label, bg="#ece9f5", fg="#a8a3bd", state="disabled")
        elif phase == "result":                        # 결과를 읽는 중에는 회색으로
            button.config(text=label, bg="#e6e3ef", fg="#6b6b80", state="normal")
        else:
            button.config(text=label, bg="#efe8ff", fg="#2b2257", state="normal")
    if phase == "result":
        next_button.config(state="normal", bg="#2b2257", fg="white",
                           text="결말 보기 ▶" if state["choices_left"] == 0 else "다음 꿈으로 ▶")
    else:
        next_button.config(state="disabled", bg="#d6d6d6", fg="#888888", text="다음 ▶")


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
    for item, button in item_buttons.items():
        picked = item in items
        button.config(bg="#ffd166" if picked else "#efe8ff", relief="sunken" if picked else "raised")
    refresh(f"'{name}' {'챙겼어요' if name in items else '뺐어요'}. ({len(items)}/{MAX_ITEMS})")


def tick():
    """1초마다 남은 시간을 줄입니다. 0이 되면 남은 칸을 아무 물건으로 채우고 잠듭니다."""
    if state["phase"] != "prep":
        return
    state["time_left"] -= 1
    timer_label.config(text=f"⏱ {state['time_left']}초", fg="#e63946" if state["time_left"] <= 10 else "#2b2257")
    if state["time_left"] <= 0:
        while len(state["items"]) < MAX_ITEMS:
            state["items"].append(random.choice([i for i in ITEMS if i not in state["items"]]))
        state["log"].append("시간 끝! 허둥지둥 아무거나 가방에 넣었어요.")
        fall_asleep()
        return
    state["timer"] = window.after(1000, tick)


def fall_asleep():
    if state["phase"] != "prep":
        return
    if state["timer"]:
        window.after_cancel(state["timer"])                    # 1초 타이머 멈추기
        state["timer"] = None
    state["log"].append("가방: " + (", ".join(state["items"]) or "없음") + " → 스르르 잠들었어요.")
    state["phase"] = "scene"
    show_phase_frame()
    set_choice_buttons()
    refresh(current_scene()["text"])


# ====================================================================
# 6. 꿈 단계 (선택 → 결과 → 다음)
# ====================================================================
def flash(times=6):
    if times == 0:
        choices_label.config(fg="#2b2257")
        return
    choices_label.config(fg="#e63946" if times % 2 == 0 else "#2b2257")
    window.after(120, flash, times - 1)


def choose(i):
    phase = state["phase"]
    # ---- 돌발 상황: 선택 세 번을 다 쓴 뒤 누른 클릭 ----
    if phase == "ending" or state["choices_left"] == 0:
        state["blocked"] += 1
        state["log"].append(f"막힌 클릭 {state['blocked']}번: 꿈속 선택은 딱 세 번뿐이에요.")
        refresh("선택을 모두 썼어요! 꿈속에서는 딱 세 번만 고를 수 있어요. 다시 시작(R)을 눌러 주세요.", "#e63946")
        flash()
        return
    if phase == "result":
        next_button.flash()                                    # '다음' 버튼을 깜빡여 먼저 누르라고 알려 줌
        return
    if phase != "scene":
        return
    choice = current_scene()["choices"][i]
    if choice["need"] and choice["need"] not in state["items"]:   # 키보드로 누른 경우
        refresh(f"가방에 '{choice['need']}'이(가) 없어서 고를 수 없어요.", "#e63946")
        return
    change = apply_effect(choice["effect"])
    state["choices_left"] -= 1
    state["log"].append(f"{state['index'] + 1}번째 꿈 · {current_scene()['title']}: "
                        f"{choice['label']} → {change}")
    state["phase"] = "result"
    set_choice_buttons()
    refresh(f"{choice['result']}\n({change})", "#0f766e")


def next_scene():
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


def restart():
    if state.get("timer"):
        window.after_cancel(state["timer"])
    state.clear()
    state.update(new_state())
    for button in item_buttons.values():
        button.config(bg="#efe8ff", relief="raised")
    timer_label.config(text=f"⏱ {PREP_SECONDS}초", fg="#2b2257")
    show_phase_frame()
    refresh("고양이가 하품을 해요. 60초 안에 꿈속에 가져갈 물건을 챙겨 주세요!")
    state["timer"] = window.after(1000, tick)


# ====================================================================
# 7. 창 만들기
# ====================================================================
FONT = "맑은 고딕"
BG = "#f6f3ff"
window = tk.Tk()
window.title("고양이의 꿈 일기")
window.resizable(False, False)
window.configure(bg=BG)

canvas = tk.Canvas(window, width=W, height=H, highlightthickness=0)
canvas.pack(padx=14, pady=(14, 6))

top = tk.Frame(window, bg=BG)
top.pack(fill="x", padx=14)
choices_label = tk.Label(top, font=(FONT, 14, "bold"), fg="#2b2257", bg=BG)
choices_label.pack(side="left")
tk.Button(top, text="[R] 다시 시작", relief="flat", bg="#2b2257", fg="white", font=(FONT, 10, "bold"),
          command=restart).pack(side="right")
stats_label = tk.Label(window, font=(FONT, 10), fg="#2b2257", bg=BG, anchor="w")
stats_label.pack(fill="x", padx=14)
bag_label = tk.Label(window, font=(FONT, 10), fg="#6b5fb5", bg=BG, anchor="w")
bag_label.pack(fill="x", padx=14)

story_label = tk.Label(window, font=(FONT, 12, "bold"), bg=BG, wraplength=W, justify="left",
                       anchor="w", height=3)
story_label.pack(fill="x", padx=14, pady=(6, 0))

# 준비 단계 버튼들
prep_frame = tk.Frame(window, bg=BG)
item_buttons = {}
for name, desc in ITEMS.items():
    button = tk.Button(prep_frame, text=f"{name}\n{desc}", width=13, height=3, wraplength=100,
                       font=(FONT, 9), bg="#efe8ff", command=lambda n=name: toggle_item(n))
    button.pack(side="left", padx=2)
    item_buttons[name] = button
prep_side = tk.Frame(prep_frame, bg=BG)
prep_side.pack(side="left", padx=(8, 0))
timer_label = tk.Label(prep_side, font=(FONT, 14, "bold"), bg=BG)
timer_label.pack()
tk.Button(prep_side, text="잠들기 ▶", relief="flat", bg="#2b2257", fg="white", font=(FONT, 10, "bold"),
          command=fall_asleep).pack()

# 꿈 단계 버튼들
dream_frame = tk.Frame(window, bg=BG)
choice_buttons = []
for i in range(3):
    button = tk.Button(dream_frame, width=19, height=3, wraplength=160, relief="flat",
                       font=(FONT, 10, "bold"), command=lambda n=i: choose(n))
    button.pack(side="left", padx=3)
    choice_buttons.append(button)
next_button = tk.Button(dream_frame, width=12, height=3, relief="flat", font=(FONT, 10, "bold"),
                        command=next_scene)
next_button.pack(side="left", padx=(10, 0))

diary_title = tk.Label(window, text="꿈 일기", font=(FONT, 10, "bold"), bg=BG, anchor="w")
diary_title.pack(fill="x", padx=14)
diary = tk.Listbox(window, height=6, font=(FONT, 9), relief="flat", bg="white")
diary.pack(fill="x", padx=14, pady=(0, 14))

# 키보드: A·B·C(또는 1·2·3) = 선택, 스페이스·엔터 = 다음/잠들기, R = 다시 시작
for i, keys in enumerate([("a", "A", "1"), ("b", "B", "2"), ("c", "C", "3")]):
    for key in keys:
        window.bind(key, lambda event, n=i: choose(n))
for key in ("<space>", "<Return>"):
    window.bind(key, lambda event: fall_asleep() if state["phase"] == "prep" else next_scene())
window.bind("r", lambda event: restart())
window.bind("R", lambda event: restart())

restart()
window.mainloop()
