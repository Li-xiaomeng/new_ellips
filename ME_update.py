# -*- coding: utf-8 -*-

import re

def function_copy(function_file_path, libTT_file_path):
    try:
        # 打开源文件并读取内容
        with open(function_file_path, 'r') as src_file:
            content = src_file.read()
        
        # 打开目标文件，追加内容
        with open(libTT_file_path, 'a') as dst_file:
            dst_file.write('\n' + content)  # 在追加内容前添加一个换行符，避免直接连接
        
        print("内容已从 {} 复制到 {}".format(function_file_path, libTT_file_path))
    except IOError:
        print("文件 {} 未找到，请检查路径是否正确".format(function_file_path))
    except IOError as e:
        print("读取或写入文件时发生错误: {}".format(e))

def global_var_copy(global_file_path, libTT_file_path):
    # 读取源文件内容
    with open(global_file_path, 'r') as src:
        source_content = src.read()
    
    # 读取目标文件内容
    with open(libTT_file_path, 'r') as tgt:
        target_lines = tgt.readlines()
    
    # 找到最后一个 #include 语句的位置
    last_include_index = -1
    for i, line in enumerate(target_lines):
        if line.strip().startswith('#include'):
            last_include_index = i
    
    # 插入源文件内容到最后一个 #include 语句之后
    if last_include_index != -1:
        insertion_index = last_include_index + 1
    else:
        insertion_index = 0  # 如果没有找到 #include，插入到文件开头

    new_content = (
        target_lines[:insertion_index] + ['\n'] + [source_content] + ['\n'] + target_lines[insertion_index:]
    )
    
    # 写回目标文件
    with open(libTT_file_path, 'w') as tgt:
        tgt.writelines(new_content)

def special_copy(file_mapping, dest_file):
    try:
        # 打开目标文件以读取内容
        with open(dest_file, 'r') as f:
            dest_content = f.read()

        # 处理special_files中的每个文件
        for source_file, start_marker in file_mapping.items():
            if source_file in def_global:
                dest_file = def_global[source_file]
                # 如果目标文件在def_global中定义了起始标记，则复制文件内容
                try:
                    with open(source_file, 'r') as f:
                        source_content = f.read()
                    with open(dest_file, 'r') as f:
                        dest_content = f.read()

                    # 寻找目标文件中的起始标记
                    start_index = dest_content.find(start_marker)

                    # 如果找到了起始标记，则插入源文件内容到起始标记前
                    if start_index != -1:
                        updated_content = dest_content[:start_index] + source_content + '\n\n' + dest_content[start_index:]
                        dest_content = updated_content

                        # 将更新后的内容写入目标文件
                        with open(dest_file, 'w') as f:
                            f.write(dest_content)
                        print("File '{}' copied successfully to '{}'.".format(source_file, dest_file))
                    else:
                        print("Start marker '{}' not found in '{}'.".format(start_marker, dest_file))
                except IOError:
                    print("File '{}' or '{}' not found.".format(source_file, dest_file))
            else:
                print("Destination file '{}' not found in def_global configuration.".format(dest_file))
    except IOError:
        print("Destination file '{}' not found.".format(dest_file))

def insert_function_call(test_file, function_name, target_function_name):
    try:
        with open(test_file, 'r') as f:
            lines = f.readlines()

        # 找到target_function_name对应的接口起始行
        function_start_pattern = re.compile(r'\b{}\b\s*\(.*\)\s*'.format(target_function_name))
        function_start_index = None
        for i, line in enumerate(lines):
            if function_start_pattern.search(line):
                function_start_index = i
                break

        if function_start_index is None:
            print("Function '{}' not found in '{}'.".format(target_function_name, test_file))
            return

        # 找到特定行（例如：uut_rtn = EC4A_start_lot）
        target_pattern = re.compile(r'\buut_rtn\s*=\s*EC4A_start_lot\b')
        target_index = None
        for i in range(function_start_index, len(lines)):
            if target_pattern.search(lines[i]):
                target_index = i
                break

        if target_index is None:
            print("Target line not found in function '{}' in '{}'.".format(target_function_name, test_file))
            return

        # 在特定行前面插入调用语句
        call_statement = 'uut_rtn = {}();\n'.format(function_name)
        lines.insert(target_index, call_statement)

        # 将更新后的内容写回文件
        with open(test_file, 'w') as f:
            f.writelines(lines)

        print("Inserted function call '{}' into '{}' before line {}.".format(call_statement.strip(), test_file, target_index + 1))

    except IOError:
        print("File '{}' not found.".format(test_file))

def read_cfg(file_path, config_item):
    config_item = config_item.strip()
    with open(file_path, 'r') as file:
        lines = file.readlines()

    config_data = {}
    current_key = None

    for line in lines:
        # 忽略以#开头的注释行
        if not line.strip().startswith('#'):
            # 忽略空行
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                config_data[key] = value
                current_key = key
            elif current_key is not None:
                # 处理多行值
                value = line.strip()
                if value:
                    config_data[current_key] += '\n' + value

    return config_data.get(config_item, "")

def parse_me_cfg(file_path):
    file_mapping = {}
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split('=')
                if len(parts) == 2:
                    key, value = parts[0].strip(), parts[1].strip()
                    if key == "special_file_Name":
                        file_mappings = value.split(',')
                        for mapping in file_mappings:
                            source_file, start_marker = mapping.split(':')
                            file_mapping[source_file.strip()] = start_marker.strip()
                else:
                    print("Illegal line: {}".format(line.strip()))
       