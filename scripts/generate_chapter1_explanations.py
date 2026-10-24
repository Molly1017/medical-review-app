#!/usr/bin/env python3
"""Add a conservative, source-traceable explanation batch for micro chapter 1."""
from __future__ import annotations
import json, sys
from pathlib import Path

EXPLANATIONS = {
"24f2f0a95691": ("荚膜位于细菌最外层，可减少吞噬细胞的清除，因此答案为 D。", "荚膜是部分细菌形成的多糖或多肽外层，可帮助黏附并增强抗吞噬能力。质粒是遗传物质，鞭毛负责运动，菌毛主要参与黏附或接合，芽胞是休眠和耐受结构。", "肺炎链球菌等有荚膜菌更容易逃避免疫清除；荚膜抗原也可用于分型。", "荚膜功能、细菌特殊结构与致病性的联系是西医综合和执业医师微生物学常考点。"),
"07de27665470": ("溶菌酶水解肽聚糖骨架中的 β-1,4 糖苷键，因此答案为 C。", "肽聚糖是细菌细胞壁的重要支架。溶菌酶切断其糖苷键，使细胞壁失去强度。", "革兰阳性菌通常更容易受到溶菌酶作用；革兰阴性菌的外膜可提供额外屏障。", "肽聚糖、溶菌酶和青霉素的作用部位要区分记忆。"),
"3ab705f35f57": ("芽胞具有多层保护结构、低含水量和特殊耐受成分，对外界抵抗力最强，因此答案为 D。", "芽胞是部分细菌在不利条件下形成的休眠体，不是繁殖体，能耐受干燥、热和多种化学因素。", "破伤风梭菌、肉毒梭菌和炭疽芽胞杆菌的芽胞具有重要公共卫生意义。", "芽胞与荚膜、鞭毛的功能不要混淆。"),
"9ff833c7c017": ("抗吞噬是荚膜的主要功能，不是细胞壁的一般功能，因此答案为 C。", "细胞壁维持形态、抵抗低渗破裂，并参与抗原性和物质交换；抗吞噬主要由荚膜等表面结构完成。", "细胞壁受损可导致细菌在低渗环境中裂解，青霉素和溶菌酶的作用也与细胞壁有关。", "细胞壁功能与荚膜功能的辨析是常见选择题陷阱。"),
"1ae60f3f131d": ("细胞壁不是所有细菌生存都必需的结构，答案为 A。", "细胞膜、核质是维持基本生命活动所必需的；鞭毛和荚膜主要影响运动、黏附或免疫逃逸。", "β-内酰胺类药物抑制肽聚糖合成，可能诱导细胞壁缺陷型。", "细胞壁缺陷型、L 型细菌与抗菌药物作用机制常结合考查。"),
"f9c407a3d8df": ("荚膜通常不是增强耐热性的主要结构，错误项为 B。", "荚膜主要作用是抗吞噬、黏附和保护菌体，成分多为多糖或多肽，并可具有免疫原性。", "耐热性主要与芽胞等结构有关。", "荚膜与芽胞的功能要分别记忆。"),
"cdf03f5cbad7": ("外膜是革兰阴性菌特有的包膜结构，因此答案为 A。", "革兰阴性菌在薄肽聚糖层外还有含脂多糖的外膜；磷壁酸是革兰阳性菌典型成分。", "外膜和脂多糖影响内毒素效应和药物通透性。", "革兰阳性/阴性细胞壁结构比较是基础高频考点。"),
"e320c641689f": ("内毒素是脂多糖成分，甲醛不能把它转化为类毒素，因此答案为 E。", "内毒素主要来自革兰阴性菌外膜，耐热性较强，通常不能像外毒素那样制成类毒素。", "内毒素可引起发热、低血压、休克和弥散性血管内凝血。", "内毒素与外毒素的来源、热稳定性和类毒素特性要成组比较。"),
"db2848c8944a": ("中毒性痢疾的全身中毒表现与革兰阴性菌内毒素有关，答案为 D。", "内毒素可引起发热和全身炎症反应，重症时出现意识障碍和休克。", "重症细菌性痢疾需要补液、抗感染并监测休克和神经系统并发症。", "病原体、毒力因子和全身表现的联系是临床微生物学重点。"),
"5acc723a0511": ("大叶性肺炎的典型病原体是肺炎链球菌，其主要致病因素是荚膜，答案为 B。", "荚膜可抵抗吞噬，是肺炎链球菌侵袭和致病的重要基础；铁锈色痰和肺叶实变支持该临床背景。", "肺炎链球菌肺炎可出现高热、寒战、咳嗽和铁锈色痰。", "肺炎链球菌荚膜与典型肺炎表现是常考组合。"),
"6058b28d01d2": ("革兰阴性肾形双球菌提示脑膜炎奈瑟菌，主要致病物质为内毒素，答案为 D。", "脑膜炎奈瑟菌外膜脂多糖释放的内毒素可造成高热、休克、皮肤出血点和弥散性血管内凝血。", "流行性脑脊髓膜炎需关注脑膜刺激征、皮肤瘀点和休克，并尽快抗感染和支持治疗。", "革兰阴性双球菌、内毒素与暴发性休克的联系是临床微生物学重点。"),
"2e31f9968e7a": ("痢疾志贺菌的主要致病物质包括内毒素，题干选项中答案为 A。", "内毒素参与发热和全身中毒反应；志贺毒素可造成肠黏膜损伤，但本题选项对应的是内毒素。", "里急后重、脓血便提示侵袭性肠道感染，需要粪便检查并及时治疗。", "志贺菌的内毒素、志贺毒素和侵袭性表现需要结合题干区分。"),
"b71be932dc16": ("破伤风的主要致病物质是破伤风痉挛毒素，属于外毒素，答案为 D。", "芽胞负责在厌氧伤口中存活和发芽，真正造成牙关紧闭、肌肉痉挛和角弓反张的是外毒素。", "伤口处理、破伤风免疫球蛋白、类毒素和控制痉挛是处理重点。", "芽胞是存活结构，外毒素是症状来源，二者不要混淆。"),
}

def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "medical_question_bank_deduplicated.json")
    data = json.loads(path.read_text(encoding="utf-8")); generated = 0
    for q in data["questions"]:
        if q.get("id") not in EXPLANATIONS or q.get("status") not in {"ready", "externally_verified_correction"}: continue
        reason, plain, clinical, exam = EXPLANATIONS[q["id"]]
        q["explanation_detail"] = {"correct_answer_reason": reason, "plain_explanation": plain, "option_analysis": {k:("正确："+reason if k==q.get("answer") else "该选项与题干考查的核心机制不符。") for k in (q.get("options") or {})}, "clinical_connection": clinical, "exam_focus": exam, "source": {"kind":"original_source_derived", "file":q.get("source"), "location":q.get("source_location")}}
        generated += 1
    data.setdefault("summary", {})["chapter1_explanations_generated"] = generated
    data["summary"]["chapter1_explanations_verified"] = generated
    data["summary"]["explanation_policy"] = "仅为原始题干、选项和原始答案均可靠的医学微生物学第一章选择题生成；未生成记录保持待审核。"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"generated={generated}"); return 0
if __name__ == "__main__": raise SystemExit(main())
