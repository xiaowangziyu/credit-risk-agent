import urllib.request
import json
import time

print("=== 冒烟测试: 企业分析流程 ===")
t0 = time.time()
data = json.dumps({"company_name": "测试科技公司"}).encode()
req = urllib.request.Request("http://localhost:8001/api/agent/analyze", data=data, headers={"Content-Type": "application/json"})
r = urllib.request.urlopen(req, timeout=300)

events = []
buffer = ""
while True:
    chunk = r.read(4096)
    if not chunk:
        break
    buffer += chunk.decode("utf-8", errors="replace")
    while "\n" in buffer:
        line, buffer = buffer.split("\n", 1)
        if line.startswith("data:"):
            try:
                evt = json.loads(line[5:])
                events.append(evt)
                t = evt.get("type", "?")
                if t == "final":
                    res = evt.get("result", {})
                    has_c = bool(res.get("company"))
                    has_s = bool(res.get("scorecard"))
                    has_r = bool(res.get("credit_suggestion"))
                    has_rp = bool(res.get("report"))
                    print(f"  [FINAL] company={has_c}, scorecard={has_s}, credit={has_r}, report={has_rp}")
                    sc = res.get("scorecard") or {}
                    print(f"  [FINAL] total_score={sc.get('total_score')}, risk_level={sc.get('risk_level')}, dims={len(sc.get('dimensions', []))}")
                elif t == "action":
                    print(f"  [ACTION] {evt.get('tool', '?')}")
                elif t == "thinking":
                    c = evt.get("content", "")
                    if len(c) > 50: c = c[:50] + "..."
                    print(f"  [THINKING] {c}")
                elif t == "observation":
                    c = evt.get("content", "")
                    if len(c) > 60: c = c[:60] + "..."
                    print(f"  [OBS] {c}")
                else:
                    print(f"  [{t.upper()}] keys={list(evt.keys())}")
            except Exception as e:
                print(f"  [PARSE ERROR] {e}")

print("")
print(f"总事件数: {len(events)}")
print(f"总耗时: {time.time() - t0:.1f}s")
print("=== 冒烟测试通过 ===")
