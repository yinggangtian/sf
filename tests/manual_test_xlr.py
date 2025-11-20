
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from backend.ai_agents.xlr.liuren.engine import PaipanEngine
from backend.ai_agents.xlr.liuren.utils import KnowledgeBase
from backend.ai_agents.xlr.schemas import QiguaInfo
from backend.shared.db.models.knowledge import Gong, Shou, Qin, DiZhi

# Mock KnowledgeBase data
def get_mock_kb():
    kb = KnowledgeBase()
    
    # Mock Gong
    gongs = [
        Gong(position=1, name="大安", wuxing="木"),
        Gong(position=2, name="留连", wuxing="火"), # Updated wuxing from XLR.md
        Gong(position=3, name="速喜", wuxing="火"),
        Gong(position=4, name="赤口", wuxing="金"),
        Gong(position=5, name="小吉", wuxing="水"),
        Gong(position=6, name="空亡", wuxing="土"),
    ]
    kb.load_gong_data(gongs)
    
    # Mock Shou
    shous = [
        Shou(position=1, name="青龙", wuxing="木"),
        Shou(position=2, name="朱雀", wuxing="火"),
        Shou(position=3, name="勾陈", wuxing="土"),
        Shou(position=4, name="腾蛇", wuxing="火"),
        Shou(position=5, name="白虎", wuxing="金"),
        Shou(position=6, name="玄武", wuxing="水"),
    ]
    kb.load_shou_data(shous)
    
    # Mock Qin
    qins = [
        Qin(name="父母", relationship="生我"),
        Qin(name="兄弟", relationship="同"),
        Qin(name="官鬼", relationship="克我"),
        Qin(name="妻财", relationship="我克"),
        Qin(name="子孙", relationship="我生"),
    ]
    kb.load_qin_data(qins)
    
    # Mock DiZhi
    dizhis = [
        DiZhi(name="子", wuxing="水"),
        DiZhi(name="丑", wuxing="土"),
        DiZhi(name="寅", wuxing="木"),
        DiZhi(name="卯", wuxing="木"),
        DiZhi(name="辰", wuxing="土"),
        DiZhi(name="巳", wuxing="火"),
        DiZhi(name="午", wuxing="火"),
        DiZhi(name="未", wuxing="土"),
        DiZhi(name="申", wuxing="金"),
        DiZhi(name="酉", wuxing="金"),
        DiZhi(name="戌", wuxing="土"),
        DiZhi(name="亥", wuxing="水"),
    ]
    kb.load_dizhi_data(dizhis)
    
    # Mock Wuxing Relations
    relations = {
        "金": {"木": "克", "水": "生", "火": "克我", "土": "生我", "金": "同"},
        "木": {"火": "生", "土": "克", "金": "克我", "水": "生我", "木": "同"},
        "水": {"木": "生", "火": "克", "土": "克我", "金": "生我", "水": "同"},
        "火": {"土": "生", "金": "克", "水": "克我", "木": "生我", "火": "同"},
        "土": {"金": "生", "水": "克", "木": "克我", "火": "生我", "土": "同"},
    }
    kb.load_wuxing_relations(relations)
    
    return kb

def test_paipan():
    kb = get_mock_kb()
    engine = PaipanEngine(kb)
    
    # Test Case: 1, 2. Time: Hai (22:00)
    num1 = 1
    num2 = 2
    dt = datetime(2025, 11, 20, 22, 0, 0) # Hai hour
    
    luogong = engine.calculate_luogong(num1, num2)
    print(f"Luogong: {luogong}") # Expected: 2
    
    shichen_info = engine.get_shichen_info(dt)
    print(f"Shichen: {shichen_info['dizhi']}") # Expected: 亥
    
    qigua_info = QiguaInfo(
        number1=num1,
        number2=num2,
        qigua_time=dt,
        luogong=luogong,
        shichen_info=shichen_info,
        ti_gong=num1,
        yong_gong=num2
    )
    
    result = engine.generate_paipan(qigua_info)
    
    print("\n--- Paipan Result ---")
    liugong = result.paipan_data["liugong"]
    liushou = result.paipan_data["liushou"]
    liuqin = result.paipan_data["liuqin"]
    
    for i in range(1, 7):
        gong = liugong[f"gong_{i}"]
        shou = liushou.get(f"shou_{i}")
        qin = liuqin.get(f"qin_{i}")
        
        dizhi = gong["dizhi_info"]["name"]
        shou_name = shou["name"] if shou else "None"
        qin_name = qin["name"] if qin else "None"
        
        print(f"Pos {i} ({gong['name']}): Dizhi={dizhi}, Shou={shou_name}, Qin={qin_name}")

if __name__ == "__main__":
    test_paipan()
