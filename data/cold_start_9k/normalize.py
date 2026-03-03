import json
import os
import re

# 配置输入和输出文件名
input_file = 'train_all.json'
output_file = 'train_all_normalized.json'

def normalize_content(content):
    # 1. 清理现有的 <image> 标签、末尾的横杠 "-" 以及首尾空白
    # 先把 <image> 拿掉，最后再统一加
    clean_content = content.replace('<image>', '').strip()
    
    # 移除末尾可能残留的 "-" (针对多选题之前可能有的格式)
    while clean_content.endswith('-'):
        clean_content = clean_content[:-1].strip()

    # 2. 判断是否为多选题 (MCQ) 并定位选项位置
    # 判定标准：
    # A) 明确包含 "Options:" 字符串
    # B) 包含类似 "\nA. " 或 "\nA) " 或 " A. " 的选项标记 (当缺少 Options 标签时)
    
    has_options_label = "Options:" in clean_content
    
    # 正则解释：
    # (?:\n|^)  : 匹配换行符或字符串开头
    # \s* : 允许有一些空白
    # A[\.\)]   : 匹配 "A." 或 "A)"
    # \s        : 后面必须跟一个空白字符
    # 目的：找到选项 "A" 开始的位置
    option_pattern = r'(?:\n|^)\s*A[\.\)]\s'
    match_a = re.search(option_pattern, clean_content)
    
    is_mcq = has_options_label or bool(match_a)
    
    final_content = clean_content

    if is_mcq:
        # --- 处理多选题 ---
        
        # 步骤 A: 如果缺少 "Options:" 但检测到了选项 "A."，则插入 "Options:"
        if not has_options_label and match_a:
            start_index = match_a.start()
            # 分割文本：问题部分 vs 选项部分
            question_part = clean_content[:start_index].strip()
            options_part = clean_content[start_index:].strip() # 这里的 options_part 应该是从 A. 开始
            
            # 重新拼接，强制加上 Options:
            # 注意：options_part 通常带有换行符，如果没有我们最好加一个
            if not options_part.startswith('\n'):
                options_part = '\n' + options_part
                
            final_content = f"{question_part}\nOptions:{options_part}"
        
        # 步骤 B: 检查并添加 "Question:" 前缀
        if not final_content.startswith("Question:"):
            # 有些可能以 "Question" 开头但没冒号，这里统一处理：如果没有明确的 "Question:" 就加上
            # 为了防止出现 "Question: Question ...", 先检查一下
            if final_content.startswith("Question") and not final_content.startswith("Question:"):
                 # 如果是 "Question What is...", 变成 "Question: What is..."
                 final_content = "Question: " + final_content[8:].strip()
            elif not final_content.startswith("Question:"):
                 final_content = "Question: " + final_content

        # 步骤 C: 添加多选题专用的后缀 "\n<image>"
        final_content = f"{final_content}\n<image>"
        
    else:
        # --- 处理非多选题 ---
        
        # 步骤 A: 检查并添加 "Question:" 前缀
        if not final_content.startswith("Question:"):
             if final_content.startswith("Question") and not final_content.startswith("Question:"):
                 final_content = "Question: " + final_content[8:].strip()
             elif not final_content.startswith("Question:"):
                 final_content = "Question: " + final_content
        
        # 步骤 B: 添加普通题目后缀 "\n<image>"
        final_content = f"{final_content}\n<image>"

    return final_content

def main():
    if not os.path.exists(input_file):
        print(f"错误: 找不到文件 {input_file}")
        return

    print(f"正在读取 {input_file} ...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取 JSON 失败: {e}")
        return

    count = 0
    mcq_count = 0
    
    # 遍历所有数据
    for item in data:
        if 'messages' in item:
            for msg in item['messages']:
                if msg['role'] == 'user':
                    original_content = msg['content']
                    new_content = normalize_content(original_content)
                    
                    if new_content != original_content:
                        msg['content'] = new_content
                        count += 1
                        
                    if "\n-\n<image>" in new_content:
                        mcq_count += 1

    print(f"处理完成。")
    print(f"共修改了 {count} 条数据。")
    print(f"其中检测并格式化为多选题 (MCQ) 的约有 {mcq_count} 条。")
    
    # 保存结果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"已保存到 {output_file}")

if __name__ == "__main__":
    main()