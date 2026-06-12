#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试套件运行入口脚本
解决从tests目录运行时的模块导入问题
"""
import os
import sys

# 获取项目根目录（当前文件所在目录的上级目录）
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# 添加到sys.path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"[RunTest] 项目根目录: {project_root}")
print(f"[RunTest] Python路径: {sys.executable}")

# 运行测试套件
from tests.test_suite import TestSuite

if __name__ == "__main__":
    print("=" * 60)
    print("企业授信智能风控Agent - 多场景测试集")
    print("=" * 60)
    
    test_suite = TestSuite()
    
    # 只测试第一个企业（快速验证）
    if len(test_suite.test_cases) > 0:
        print(f"\n快速测试：运行单个企业")
        result = test_suite.run_single_test(test_suite.test_cases[0].company_name, iterations=1)
        print(f"测试完成: {result.test_case.company_name}")
    else:
        print("未找到测试用例")
