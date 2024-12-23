
from mutil_agents.memory.review_state import ReviewState
from mutil_agents.agent import graph


if __name__ == "__main__":
 # test
    content = "《国家基本药物目录（2018年版）》于2020年11月1日起施行并建立了动态调整机制，与一致性评价实现联动。通过不一致性评价的品种优先纳入目录，未通过不一致性评价的品种将逐步被调出目录。对纳入国家基本药物目录的品种，不再统一设置评价时限要求。"
   #  content = "本品与 R-CHOP 联用治疗 MYC 和 BCL2 表达阳性的既往未经治疗的 DLBCL 患者时， 用药前应进行血常规检查，相关指标满足以下条件方可开始用药：中性粒细胞绝对值≥1.5× 109 /L，血小板计数≥90×109 /L，血红蛋白≥90g/L。用药期间需定期检测血常规（通常为每周 一次）。建议在第 2~6 周期的每周期第 1 天给药前 72 小时内进行血常规检查，并达到以下 标准：  中性粒细胞≥1.5×109 /L，即正常或≤1 级  血小板≥75×109 /L，即正常或≤1 级  血红蛋白≥80 g/L，即正常或≤2 级 如果上述指标任一项未达到标准，建议推迟西达本胺联合 R-CHOP 治疗，并给予对症 支持治疗，建议延迟期内每 3~4 天重复血常规检查。 在下一周期开始用药前若存在 3 级非血液学毒性（除外恶心、呕吐、秃头症），需延迟 联合治疗至毒性恢复至正常或≤1 级时开始原剂量用药或对环磷酰胺、阿霉素、长春新碱中 1 种或多种药物降低 1 个剂量水平用药（由临床医生根据毒性类型和药品说明书确定）。若 不良反应在经对症治疗且延迟下一周期治疗超过 14 天仍未恢复至上述标准，则建议结束联 合治疗。"
    # Create a sample ReviewState object
    sample_review_state = ReviewState()
    sample_review_state["content"] = content
    result = graph.invoke(sample_review_state)
    print(result)
