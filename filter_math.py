import pandas as pd
df = pd.read_csv('student.csv')
print(df)
result = df[df['数学'] > 80]
result.to_csv('math_high.csv', index=False)
print(f"筛选出{len(result)}人，已保存到 math_high.csv")
