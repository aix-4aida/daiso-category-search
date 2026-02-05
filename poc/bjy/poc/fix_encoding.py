
import os

file_path = r"c:\Users\301\pjt\Final\search\search-roca\poc\document\poc_v6_latency_benchmark_report.md"
correct_text = """### **Scenario Legend**
*   **Synonym**: 일반적인 유의어 (예: '배터리' -> '건전지')
*   **Intent-based**: 사용자의 의도를 파악해야 하는 경우 (예: '여행 샴푸 통' -> '리필 용기')
*   **Visual Description**: 시각적 묘사 (예: '그.. 뽁뽁이')
*   **Distractor**: 존재하지 않거나 오답을 유도하는 함정 (예: '아이폰 충전기' -> 'null')
*   **Context**: 특정 상황이나 맥락 (예: '비 와서', '캠핑 갈 때')
*   **Description**: 기능이나 형태 설명 (예: '옷에 핀 보풀 제거하는 기계')
*   **Specific Product**: 정확한 상품명 지칭 (예: '케이블 타이')
*   **Negative**: 부정 연산자 사용 (예: '~말고')
*   **Problem-Solution**: 문제 해결을 위한 도구 (예: '방충망 구멍 났을 때')
*   **Slang/Typo**: 은어, 오타, 발음 나는 대로 쓴 영어 (예: 'Jongee Tape')
"""

# Read existing content
with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

# Truncate after the table (remove the corrupted part) and append correct text
# Finding the line where Scenario Legend likely started or just appending
final_lines = []
found_target = False
for line in lines:
    if "Scenario Legend" in line:
        found_target = True
        break
    final_lines.append(line)

# Re-write file
with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(final_lines)
    f.write(correct_text)

print("Fixed encoding issue.")
