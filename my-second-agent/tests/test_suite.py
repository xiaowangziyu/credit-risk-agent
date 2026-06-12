import json
import os
import sys
import time
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目根目录到模块搜索路径（支持从tests目录运行脚本）
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
print(f"[TestSuite] 项目根目录已添加: {_project_root}")

from tools.search_company import company_search_tool
from agent.react_agent import ReActAgent


class TestCase:
    """测试用例类"""
    def __init__(self, company_name: str, risk_level: str, expected_outcome: str, test_notes: str = ""):
        self.company_name = company_name
        self.risk_level = risk_level
        self.expected_outcome = expected_outcome
        self.test_notes = test_notes


class TestResult:
    """测试结果类"""
    def __init__(self, test_case: TestCase):
        self.test_case = test_case
        self.run_times: List[float] = []
        self.scores: List[int] = []
        self.risk_levels: List[str] = []
        self.tool_sequences: List[List[str]] = []
        self.rule_results: List[bool] = []
        self.credit_amounts: List[int] = []
        self.outcomes: List[str] = []

    def add_run(self, duration: float, score: int, risk_level: str, 
                tool_sequence: List[str], rule_result: bool, 
                credit_amount: int, outcome: str):
        self.run_times.append(duration)
        self.scores.append(score)
        self.risk_levels.append(risk_level)
        self.tool_sequences.append(tool_sequence)
        self.rule_results.append(rule_result)
        self.credit_amounts.append(credit_amount)
        self.outcomes.append(outcome)


class TestSuite:
    """测试套件类"""
    
    def __init__(self, test_cases_path: str = None):
        self.test_cases: List[TestCase] = []
        self.test_results: Dict[str, TestResult] = {}
        self.test_cases_path = test_cases_path or os.path.join(
            os.path.dirname(__file__), "test_cases.json"
        )
        self.load_test_cases()

    def load_test_cases(self):
        """加载测试用例"""
        if os.path.exists(self.test_cases_path):
            with open(self.test_cases_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for case_data in data.get("test_cases", []):
                    self.test_cases.append(TestCase(
                        company_name=case_data["company_name"],
                        risk_level=case_data["risk_level"],
                        expected_outcome=case_data["expected_outcome"],
                        test_notes=case_data.get("test_notes", "")
                    ))

    def add_test_case(self, company_name: str, risk_level: str, 
                      expected_outcome: str, test_notes: str = ""):
        """添加测试用例"""
        self.test_cases.append(TestCase(company_name, risk_level, expected_outcome, test_notes))

    async def _run_single_test_async(self, company_name: str) -> dict:
        """异步运行单个企业的一次测试"""
        agent = ReActAgent()
        thinking_history = []
        tool_sequence = []
        final_result = None
        step_count = 0
        
        try:
            step_count = 0
            async for step in agent.run_full_analysis(company_name):
                if step is None:
                    print(f"  [测试] 警告: 收到 None step")
                    continue
                step_count += 1
                thinking_history.append(step)
                
                if not isinstance(step, dict):
                    print(f"  [测试] 警告: step {step_count} 不是 dict 类型: {type(step)}")
                    continue
                    
                step_type = step.get("type", "unknown")
                if step_type == "action":
                    tool_sequence.append(step.get("tool", ""))
                
                if step_type == "final":
                    final_result = step.get("result", {})
        except Exception as e:
            print(f"  [测试] 异步迭代异常: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print(f"  [测试] 总共执行了 {step_count} 个步骤")
        
        # 安全获取结果，防止空值
        if final_result is None:
            print(f"  [警告] 未获取到最终结果，已调用工具: {tool_sequence}")
            return {
                "score": 0,
                "risk_level": "未知",
                "credit_amount": 0,
                "status": "error",
                "rule_passed": False,
                "tool_sequence": tool_sequence
            }
        
        print(f"  [测试] final_result keys: {final_result.keys() if final_result else 'None'}")
        scorecard = final_result.get("scorecard") if final_result else None
        credit_suggestion = final_result.get("credit_suggestion") if final_result else None
        
        print(f"  [测试] scorecard: {scorecard}")
        print(f"  [测试] credit_suggestion: {credit_suggestion}")
        
        return {
            "score": scorecard.get("total_score", 0) if scorecard else 0,
            "risk_level": scorecard.get("risk_level", "未知") if scorecard else "未知",
            "credit_amount": self._parse_credit_amount(credit_suggestion.get("suggested_amount", "0")) if credit_suggestion else 0,
            "status": final_result.get("status", "unknown") if final_result else "unknown",
            "rule_passed": (final_result.get("rule_check") or {}).get("passed", True) if final_result.get("rule_check") else True,
            "tool_sequence": tool_sequence
        }
    
    def run_single_test(self, company_name: str, iterations: int = 3) -> TestResult:
        """运行单个企业的测试"""
        import asyncio
        
        test_case = next((c for c in self.test_cases if c.company_name == company_name), None)
        
        if not test_case:
            test_case = TestCase(company_name, "unknown", "unknown")
        
        result = TestResult(test_case)
        
        for i in range(iterations):
            print(f"  第 {i+1}/{iterations} 次测试...")
            start_time = time.time()
            
            try:
                # 异步运行分析
                test_data = asyncio.run(self._run_single_test_async(company_name))
                
                end_time = time.time()
                duration = end_time - start_time
                
                outcome = "通过" if test_data["status"] == "completed" else ("拒绝" if test_data["status"] == "rejected" else "未知")
                
                result.add_run(
                    duration=duration,
                    score=test_data["score"],
                    risk_level=test_data["risk_level"],
                    tool_sequence=test_data["tool_sequence"],
                    rule_result=test_data["rule_passed"],
                    credit_amount=test_data["credit_amount"],
                    outcome=outcome
                )
                
                print(f"    评分: {test_data['score']}, 风险等级: {test_data['risk_level']}, 耗时: {duration:.2f}秒")
                
            except Exception as e:
                print(f"    测试失败: {str(e)}")
                end_time = time.time()
                result.add_run(
                    duration=end_time - start_time,
                    score=0,
                    risk_level="错误",
                    tool_sequence=[],
                    rule_result=False,
                    credit_amount=0,
                    outcome="错误"
                )
        
        self.test_results[company_name] = result
        return result
    
    def _parse_credit_amount(self, amount_str: str) -> int:
        """解析授信额度字符串为数字"""
        if not amount_str:
            return 0
        try:
            # 匹配数字部分
            match = re.search(r'(\d+(?:\.\d+)?)', str(amount_str))
            if match:
                return int(float(match.group(1)))
            return 0
        except:
            return 0

    def run_all_tests(self, iterations: int = 3):
        """运行所有测试用例"""
        print(f"开始运行测试套件，共 {len(self.test_cases)} 个测试用例，每个用例运行 {iterations} 次...")
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"\n[{i}/{len(self.test_cases)}] 测试企业: {test_case.company_name} (风险级别: {test_case.risk_level})")
            self.run_single_test(test_case.company_name, iterations)
        
        print("\n测试完成！")

    def calculate_metrics(self) -> Dict[str, Any]:
        """计算评估指标"""
        metrics = {
            "overall": {},
            "by_risk_level": {
                "low": {},
                "medium": {},
                "high": {}
            }
        }
        
        all_scores = []
        all_durations = []
        all_tool_sequences = []
        all_rule_results = []
        
        for company_name, result in self.test_results.items():
            risk_level = result.test_case.risk_level
            
            # 收集数据
            all_scores.extend(result.scores)
            all_durations.extend(result.run_times)
            all_tool_sequences.extend(result.tool_sequences)
            all_rule_results.extend(result.rule_results)
            
            # 计算单个企业指标
            if len(result.scores) >= 2:
                score_std = statistics.stdev(result.scores)
            else:
                score_std = 0
            
            risk_level_consistency = len(set(result.risk_levels)) == 1
            rule_result_consistency = len(set(result.rule_results)) == 1
            
            # 工具调用一致性
            tool_seq_strs = [",".join(seq) for seq in result.tool_sequences]
            tool_consistency = len(set(tool_seq_strs)) == 1
            
            # 按风险级别统计
            if risk_level not in metrics["by_risk_level"]:
                metrics["by_risk_level"][risk_level] = {
                    "scores": [],
                    "durations": [],
                    "count": 0,
                    "avg_score_std": 0,
                    "risk_level_consistency_rate": 0,
                    "tool_consistency_rate": 0,
                    "rule_consistency_rate": 0
                }
            
            metrics["by_risk_level"][risk_level]["scores"].extend(result.scores)
            metrics["by_risk_level"][risk_level]["durations"].extend(result.run_times)
            metrics["by_risk_level"][risk_level]["count"] += 1
            metrics["by_risk_level"][risk_level]["avg_score_std"] += score_std
            metrics["by_risk_level"][risk_level]["risk_level_consistency_rate"] += 1 if risk_level_consistency else 0
            metrics["by_risk_level"][risk_level]["tool_consistency_rate"] += 1 if tool_consistency else 0
            metrics["by_risk_level"][risk_level]["rule_consistency_rate"] += 1 if rule_result_consistency else 0
        
        # 计算总体指标
        if all_scores:
            metrics["overall"] = {
                "total_runs": len(all_scores),
                "avg_score": statistics.mean(all_scores),
                "score_std": statistics.stdev(all_scores) if len(all_scores) > 1 else 0,
                "min_score": min(all_scores),
                "max_score": max(all_scores),
                "avg_duration": statistics.mean(all_durations),
                "min_duration": min(all_durations),
                "max_duration": max(all_durations),
                "duration_std": statistics.stdev(all_durations) if len(all_durations) > 1 else 0
            }
        else:
            metrics["overall"] = {
                "total_runs": 0,
                "avg_score": 0,
                "score_std": 0,
                "min_score": 0,
                "max_score": 0,
                "avg_duration": 0,
                "min_duration": 0,
                "max_duration": 0,
                "duration_std": 0
            }
        
        # 计算各风险级别指标
        for risk_level, data in metrics["by_risk_level"].items():
            count = data["count"]
            if count > 0:
                data["avg_score"] = statistics.mean(data["scores"]) if data["scores"] else 0
                data["score_std"] = statistics.stdev(data["scores"]) if len(data["scores"]) > 1 else 0
                data["avg_duration"] = statistics.mean(data["durations"]) if data["durations"] else 0
                data["avg_score_std"] /= count
                data["risk_level_consistency_rate"] = (data["risk_level_consistency_rate"] / count) * 100
                data["tool_consistency_rate"] = (data["tool_consistency_rate"] / count) * 100
                data["rule_consistency_rate"] = (data["rule_consistency_rate"] / count) * 100
        
        return metrics

    def generate_report(self, output_path: Optional[str] = None) -> str:
        """生成评估报告"""
        metrics = self.calculate_metrics()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
# 企业授信智能风控Agent评估报告

生成时间: {timestamp}

## 一、测试概况

- 测试用例总数: {len(self.test_cases)}
- 每个企业测试次数: {len(next(iter(self.test_results.values())).scores) if self.test_results else 0}
- 低风险企业: {sum(1 for c in self.test_cases if c.risk_level == 'low')}
- 中风险企业: {sum(1 for c in self.test_cases if c.risk_level == 'medium')}
- 高风险企业: {sum(1 for c in self.test_cases if c.risk_level == 'high')}

## 二、输出准确性

### 2.1 评分统计

| 指标 | 值 |
|------|-----|
| 平均评分 | {metrics['overall']['avg_score']:.2f} |
| 评分标准差 | {metrics['overall']['score_std']:.2f} |
| 最低评分 | {metrics['overall']['min_score']} |
| 最高评分 | {metrics['overall']['max_score']} |

### 2.2 各风险级别评分分布

| 风险级别 | 企业数 | 平均评分 | 评分标准差 |
|---------|--------|---------|-----------|
| 低风险 | {metrics['by_risk_level']['low']['count']} | {metrics['by_risk_level']['low']['avg_score']:.2f} | {metrics['by_risk_level']['low']['score_std']:.2f} |
| 中风险 | {metrics['by_risk_level']['medium']['count']} | {metrics['by_risk_level']['medium']['avg_score']:.2f} | {metrics['by_risk_level']['medium']['score_std']:.2f} |
| 高风险 | {metrics['by_risk_level']['high']['count']} | {metrics['by_risk_level']['high']['avg_score']:.2f} | {metrics['by_risk_level']['high']['score_std']:.2f} |

### 2.3 风险等级稳定性

| 风险级别 | 风险等级一致率 |
|---------|--------------|
| 低风险 | {metrics['by_risk_level']['low']['risk_level_consistency_rate']:.1f}% |
| 中风险 | {metrics['by_risk_level']['medium']['risk_level_consistency_rate']:.1f}% |
| 高风险 | {metrics['by_risk_level']['high']['risk_level_consistency_rate']:.1f}% |

## 三、响应时长

| 指标 | 值 |
|------|-----|
| 平均响应时间 | {metrics['overall']['avg_duration']:.2f} 秒 |
| 最短响应时间 | {metrics['overall']['min_duration']:.2f} 秒 |
| 最长响应时间 | {metrics['overall']['max_duration']:.2f} 秒 |
| 响应时间标准差 | {metrics['overall']['duration_std']:.2f} 秒 |

### 各风险级别响应时长

| 风险级别 | 平均响应时间 |
|---------|-------------|
| 低风险 | {metrics['by_risk_level']['low']['avg_duration']:.2f} 秒 |
| 中风险 | {metrics['by_risk_level']['medium']['avg_duration']:.2f} 秒 |
| 高风险 | {metrics['by_risk_level']['high']['avg_duration']:.2f} 秒 |

## 四、决策一致性

### 4.1 工具调用一致性

| 风险级别 | 工具调用一致率 |
|---------|--------------|
| 低风险 | {metrics['by_risk_level']['low']['tool_consistency_rate']:.1f}% |
| 中风险 | {metrics['by_risk_level']['medium']['tool_consistency_rate']:.1f}% |
| 高风险 | {metrics['by_risk_level']['high']['tool_consistency_rate']:.1f}% |

### 4.2 规则校验一致性

| 风险级别 | 规则校验一致率 |
|---------|--------------|
| 低风险 | {metrics['by_risk_level']['low']['rule_consistency_rate']:.1f}% |
| 中风险 | {metrics['by_risk_level']['medium']['rule_consistency_rate']:.1f}% |
| 高风险 | {metrics['by_risk_level']['high']['rule_consistency_rate']:.1f}% |

## 五、详细测试结果

"""
        
        for company_name, result in self.test_results.items():
            case = result.test_case
            report += f"""### {company_name}

| 项目 | 值 |
|------|-----|
| 期望风险级别 | {case.risk_level} |
| 期望结果 | {case.expected_outcome} |
| 平均评分 | {statistics.mean(result.scores) if result.scores else 0:.1f} |
| 评分范围 | {min(result.scores) if result.scores else 0} - {max(result.scores) if result.scores else 0} |
| 平均响应时间 | {statistics.mean(result.run_times) if result.run_times else 0:.2f} 秒 |
| 风险等级一致性 | {'一致' if len(set(result.risk_levels)) == 1 else '不一致'} |
| 实际风险等级 | {', '.join(set(result.risk_levels))} |
\n"""
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"报告已保存到: {output_path}")
        
        return report

    def export_results(self, output_path: str):
        """导出测试结果为JSON格式"""
        results_data = {
            "generated_at": datetime.now().isoformat(),
            "test_cases_count": len(self.test_cases),
            "results": {}
        }
        
        for company_name, result in self.test_results.items():
            results_data["results"][company_name] = {
                "risk_level": result.test_case.risk_level,
                "expected_outcome": result.test_case.expected_outcome,
                "scores": result.scores,
                "risk_levels": result.risk_levels,
                "run_times": result.run_times,
                "tool_sequences": result.tool_sequences,
                "rule_results": result.rule_results,
                "credit_amounts": result.credit_amounts,
                "outcomes": result.outcomes
            }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        
        print(f"测试结果已导出到: {output_path}")


if __name__ == "__main__":
    # 运行测试套件
    test_suite = TestSuite()
    
    print("=" * 60)
    print("企业授信智能风控Agent - 多场景测试集")
    print("=" * 60)
    
    # 运行测试
    test_suite.run_all_tests(iterations=3)
    
    # 生成报告
    report = test_suite.generate_report()
    print("\n" + "=" * 60)
    print("评估报告摘要")
    print("=" * 60)
    
    # 保存报告
    report_path = os.path.join(os.path.dirname(__file__), "evaluation_report.md")
    test_suite.generate_report(report_path)
    
    # 导出详细结果
    results_path = os.path.join(os.path.dirname(__file__), "test_results.json")
    test_suite.export_results(results_path)
    
    print("\n测试完成！报告和结果已保存。")