def string_with_arrows(text, pos_start, pos_end):
    """报错信息辅助方法"""

    result = ''

    # 计算获得报错位置
    idx_start = max(text.rfind('\n', 0, pos_start.idx), 0)
    idx_end = text.find('\n', idx_start + 1)
    if idx_end < 0:
        idx_end = len(text)

    line_count = pos_end.ln - pos_start.ln + 1
    for i in range(line_count):
        # Calculate line columns
        # 计算行号
        line = text[idx_start:idx_end]
        col_start = pos_start.col if i == 0 else 0
        col_end = pos_end.col if i == line_count - 1 else len(line) - 1

        # 将报错指向添加到显示结果中
        result += line + '\n'
        result += ' ' * col_start + '^' * (col_end - col_start)

        # 重新计算报错位置
        idx_start = idx_end
        idx_end = text.find('\n', idx_start + 1)
        if idx_end < 0:
            idx_end = len(text)

    return result.replace('\t', '')