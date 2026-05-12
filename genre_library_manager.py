import json
import os
from typing import Dict, Any, List, Optional

LIBRARY_FILE = "genre_library.json"

DEFAULT_GENRES = [
    {
        "id": "xianxia",
        "name": "仙侠修真",
        "system_prompt": "你是一位专注于仙侠修真类小说的网文大神。你的文风飘逸出尘，擅长描写求仙问道的过程，强调因果循环、天地法则。在遣词造句上，多使用古风词汇。",
        "reference_text": "修真无岁月。山中方一日，世上已千年。",
        "network_prompt": "以仙侠小说的套路构建事件：法宝现世、宗门大比、秘境夺宝、心魔劫、飞升等。"
    },
    {
        "id": "sci_fi",
        "name": "硬科幻",
        "system_prompt": "你是一位硬科幻小说家。你的文风严谨冷静，注重科学逻辑的合理延展，探讨技术对人类社会、伦理以及宇宙命运的深刻影响。",
        "reference_text": "在零重力下的休眠舱里，人类的未来如同那些冰冷的指示灯一般在黑暗中闪烁。量子引擎的低鸣穿越了三千万光年的孤寂。",
        "network_prompt": "事件应包含科学发现、外星文明接触、技术伦理困境、星际战争与和平等元素。"
    },
    {
        "id": "urban_fantasy",
        "name": "都市异能",
        "system_prompt": "你是一位擅长都市异能写作的小说家。你的故事根植于现代都会的霓虹灯下，隐藏在普通人视线之外的是光怪陆离的异能力量和隐藏法则。文风轻快节奏紧凑，代入感强。",
        "reference_text": "夜幕降临在这个钢筋水泥的丛林，而真正属于他们的猎杀才刚刚开始。他推开推拉门，瞳孔在一瞬间变成了竖瞳。",
        "network_prompt": "包含觉醒异能、都市暗战、隐秘组织冲突、隐藏身份、平凡生活与超凡力量的冲撞。"
    },
    {
        "id": "suspense",
        "name": "悬疑推理",
        "system_prompt": "你是一位老练的悬疑推理小说家。描写压抑沉重，擅长营造紧张气氛，注重心理侧写。事件环环相扣，真相往往隐藏在最不经意的细节中。",
        "reference_text": "雨水冲刷着现场的痕迹，警灯在积水中闪烁刺眼的红蓝光。尸体倒在一条死胡同里，只有那双死不瞑目的眼睛看着灰蒙蒙的天空。",
        "network_prompt": "以连环案件起头，注重线索发现、嫌疑人排查、反转、最终推理揭秘的经典四幕式结构。"
    }
]

class GenreLibrary:
    def __init__(self):
        self.genres: List[Dict[str, Any]] = []
        self._load_library()

    def _load_library(self):
        if os.path.exists(LIBRARY_FILE):
            try:
                with open(LIBRARY_FILE, 'r', encoding='utf-8') as f:
                    self.genres = json.load(f)
            except Exception:
                self.genres = DEFAULT_GENRES.copy()
        else:
            self.genres = DEFAULT_GENRES.copy()
            self._save_library()

    def _save_library(self):
        try:
            with open(LIBRARY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.genres, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Could not save library:", e)

    def get_all_genres(self) -> List[Dict[str, Any]]:
        return self.genres

    def get_genre_by_id(self, genre_id: str) -> Optional[Dict[str, Any]]:
        for g in self.genres:
            if g['id'] == genre_id:
                return g
        return None

    def add_genre(self, genre_data: Dict[str, Any]):
        self.genres.append(genre_data)
        self._save_library()

    def remove_genre(self, genre_id: str):
        self.genres = [g for g in self.genres if g['id'] != genre_id]
        self._save_library()

genre_lib = GenreLibrary()
