import logging
import os

import markdown
# 延迟导入 matplotlib 以避免 NumPy 2.0 兼容性问题
# import matplotlib.pyplot as plt
# from matplotlib.gridspec import GridSpec

from mcp.xscript.utils import xss_utils

import re
import ast
import math
from mcp.optional_deps import numpy as np

class XssLVPlot:

    @staticmethod
    def gen_html(fileName):
        # 延迟导入 matplotlib 以避免 NumPy 2.0 兼容性问题
        import matplotlib.pyplot as plt
        
        # 处理 file:/// 前缀
        if fileName.startswith('file:///'):
            fileName = fileName[8:]  # 移除 file:/// 前缀
        elif fileName.startswith('file://'):
            fileName = fileName[7:]  # 移除 file:// 前缀
        
        file_input = os.path.realpath(fileName)
        file_output = f"{file_input}_report.html"
        output_dir = os.path.dirname(file_output)

        s_tmp = os.path.basename(file_input)
        # 提取标识符
        unique_id = s_tmp.split('_LocalVol', 1)[0]

        # 统一使用UTF-8编码以支持中文
        encoding = 'utf-8'
        result = os.path.realpath(file_output)
        logging.info(f"gen_html: input={file_input}, output={result}")

        # 尝试多种编码读取文件，优先使用UTF-8
        # 注意：使用 read() 而不是 readlines()，以便 markdown 能正确处理表格
        try:
            with open(file_input, 'r', encoding='utf-8') as f:
                md_content = f.read()
        except UnicodeDecodeError:
            # 如果UTF-8失败，尝试GBK
            try:
                with open(file_input, 'r', encoding='gbk') as f:
                    md_content = f.read()
            except UnicodeDecodeError:
                # 如果GBK也失败，尝试使用errors='ignore'忽略错误字符
                with open(file_input, 'r', encoding='utf-8', errors='ignore') as f:
                    md_content = f.read()
        
        # 为了解析绘图数据，需要 lines
        lines = md_content.splitlines(keepends=True)
        
        # 图片文件名（相对于HTML文件的路径）
        file_image1 = f"{unique_id}_plot1.png"
        img_filename1 = os.path.join(output_dir, file_image1)  # 使用绝对路径保存图片
        img_content1_template = f'<img src="{file_image1}" alt="Plot 1"/>'  # HTML中使用相对路径
        file_image2 = f"{unique_id}_plot2.png"
        img_filename2 = os.path.join(output_dir, file_image2)  # 使用绝对路径保存图片
        img_content2_template = f'<img src="{file_image2}" alt="Plot 2"/>'  # HTML中使用相对路径
        
        # 初始化图片内容为空，只有在成功生成图片后才设置
        img_content1_final = ""
        img_content2_final = ""
        
        # 先解析数据并生成图片
        d = XssLVPlot.parse_plot_data(lines)
        logging.info(f"Parsed plot data keys: {list(d.keys())}")
        
        # 检查是否有任何绘图数据
        has_any_data = len(d) > 0
        
        # 检查是否有绘图数据，放宽条件：只要有部分数据就尝试绘图
        has_plot1_data = any(key in d and len(d[key]) > 0 for key in ['midPremium', 'bid', 'ask', 'inSamplePrices'])
        has_plot1_testing_data = any(key in d and len(d[key]) > 0 for key in ['bidTesting', 'midPremiumTesting', 'askTesting', 'outOfSamplePrices'])
        
        if has_any_data and (has_plot1_data or has_plot1_testing_data):
            try:
                # 对plot1进行绘图
                plt.figure(figsize=(8, 6))
                
                # 确定子图数量
                num_subplots = 0
                if has_plot1_data:
                    num_subplots += 1
                if has_plot1_testing_data:
                    num_subplots += 1
                
                if num_subplots == 0:
                    num_subplots = 1  # 至少一个子图
                
                subplot_idx = 1
                
                if has_plot1_data:
                    plt.subplot(num_subplots, 1, subplot_idx)
                    # 找到最长的数据数组长度
                    max_len = 0
                    for key in ['midPremium', 'bid', 'ask', 'inSamplePrices']:
                        if key in d and len(d[key]) > max_len:
                            max_len = len(d[key])
                    
                    if max_len > 0:
                        ax = range(max_len)
                        plot_items = []
                        if 'midPremium' in d and len(d['midPremium']) > 0:
                            plot_items.append((ax[:len(d['midPremium'])], d['midPremium'], "g.", "Mid Premium"))
                        if 'bid' in d and len(d['bid']) > 0:
                            plot_items.append((ax[:len(d['bid'])], d['bid'], "r.", "Bid"))
                        if 'ask' in d and len(d['ask']) > 0:
                            plot_items.append((ax[:len(d['ask'])], d['ask'], "r.", "Ask"))
                        if 'inSamplePrices' in d and len(d['inSamplePrices']) > 0:
                            plot_items.append((ax[:len(d['inSamplePrices'])], d['inSamplePrices'], "co", "In Sample Prices"))
                        
                        if plot_items:
                            for ax_data, y_data, style, label in plot_items:
                                plt.plot(ax_data, y_data, style, label=label)
                            plt.title("In sample results")
                            plt.xlabel("option")
                            plt.ylabel("price")
                            plt.legend()
                    subplot_idx += 1

                if has_plot1_testing_data:
                    plt.subplot(num_subplots, 1, subplot_idx)
                    # 找到最长的测试数据数组长度
                    max_len = 0
                    for key in ['bidTesting', 'midPremiumTesting', 'askTesting', 'outOfSamplePrices']:
                        if key in d and len(d[key]) > max_len:
                            max_len = len(d[key])
                    
                    if max_len > 0:
                        ax2 = range(max_len)
                        plot_items2 = []
                        if 'midPremiumTesting' in d and len(d['midPremiumTesting']) > 0:
                            plot_items2.append((ax2[:len(d['midPremiumTesting'])], d['midPremiumTesting'], "g.", "Mid Premium Testing"))
                        if 'bidTesting' in d and len(d['bidTesting']) > 0:
                            plot_items2.append((ax2[:len(d['bidTesting'])], d['bidTesting'], "r.", "Bid Testing"))
                        if 'askTesting' in d and len(d['askTesting']) > 0:
                            plot_items2.append((ax2[:len(d['askTesting'])], d['askTesting'], "r.", "Ask Testing"))
                        if 'outOfSamplePrices' in d and len(d['outOfSamplePrices']) > 0:
                            plot_items2.append((ax2[:len(d['outOfSamplePrices'])], d['outOfSamplePrices'], "co", "Out of Sample Prices"))
                        
                        if plot_items2:
                            for ax_data, y_data, style, label in plot_items2:
                                plt.plot(ax_data, y_data, style, label=label)
                            plt.title("Out of sample results")
                            plt.xlabel("option")
                            plt.ylabel("price")
                            plt.legend()
                
                plt.tight_layout()
                plt.savefig(img_filename1, dpi=100)
                logging.info(f"Saved plot1 to: {img_filename1}")
                plt.close()
                # 如果图片文件成功生成，设置图片引用
                if os.path.exists(img_filename1):
                    img_content1_final = img_content1_template
            except Exception as e:
                logging.warning(f"Failed to generate plot1: {e}", exc_info=True)
                img_content1_final = ""
        else:
            logging.info("No plot1 data available, skipping plot1 generation")
            img_content1_final = ""

        # 对plot2进行绘图
        # 检查是否有plot2所需的数据
        has_plot2_data = ('midPremium' in d or 'midPremiumTesting' in d) and \
                        ('inSamplePrices' in d or 'outOfSamplePrices' in d)
        
        if has_plot2_data:
            try:
                # 合并 midPremium 和 midPremiumTesting
                combined_premiums = []
                if 'midPremium' in d:
                    combined_premiums.extend(d['midPremium'])
                if 'midPremiumTesting' in d:
                    combined_premiums.extend(d['midPremiumTesting'])
                
                # 合并 inSamplePrices 和 outOfSamplePrices
                combined_prices = []
                if 'inSamplePrices' in d:
                    combined_prices.extend(d['inSamplePrices'])
                if 'outOfSamplePrices' in d:
                    combined_prices.extend(d['outOfSamplePrices'])

                if len(combined_premiums) > 0 and len(combined_prices) > 0:
                    # 绘制图形
                    plt.figure()
                    plt.scatter(combined_prices, combined_premiums, color='blue', label='Heston Premiums vs. Market Premiums')
                    if len(combined_prices) > 1:
                        plt.plot([min(combined_prices), max(combined_prices)], 
                                [min(combined_premiums), max(combined_premiums)], 
                                linestyle='--', color='red', label='Equality Line')
                    plt.title('Comparison of Predicted Premiums and Market Premiums')
                    plt.xlabel('Market Premiums')
                    plt.ylabel('Predicted Premiums')
                    plt.legend()
                    plt.grid(True)
                    plt.savefig(img_filename2, dpi=100)
                    logging.info(f"Saved plot2 to: {img_filename2}")
                    plt.close()
                    # 如果图片文件成功生成，设置图片引用
                    if os.path.exists(img_filename2):
                        img_content2_final = img_content2_template
            except Exception as e:
                logging.warning(f"Failed to generate plot2: {e}", exc_info=True)
                img_content2_final = ""
        else:
            logging.info("No plot2 data available, skipping plot2 generation")
            img_content2_final = ""
        
        # 现在转换markdown为HTML（在生成图片之后）
        # 使用与XssMCPlot完全相同的方式处理markdown，确保表格能正确解析
        # 注意：直接使用 md_content（字符串），而不是重新拼接 lines，以保持原始格式
        # 将Markdown内容转换为HTML，使用扩展以支持表格和中文
        html = markdown.markdown(md_content, extensions=['markdown.extensions.tables', 'markdown.extensions.codehilite'])
        
        # 更新HTML中的图片引用（在生成HTML之后）
        if img_content1_final:
            if '<!--PLOT1-->' in html:
                html = html.replace('<!--PLOT1-->', img_content1_final)
            else:
                # 如果没有占位符，在body末尾添加图片
                html = html + "\n" + img_content1_final
        
        if img_content2_final:
            if '<!--PLOT2-->' in html:
                html = html.replace('<!--PLOT2-->', img_content2_final)
            else:
                # 如果没有占位符，在body末尾添加图片
                html = html + "\n" + img_content2_final
        
        # 构建完整的HTML文档结构，确保中文正确显示，并添加表格样式
        html_with_meta = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LocalVol Report</title>
    <style>
        body {{
            font-family: Arial, "Microsoft YaHei", "SimHei", sans-serif;
            line-height: 1.6;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        tr:hover {{
            background-color: #e8f5e9;
        }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #333;
            margin-top: 20px;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
{html}
</body>
</html>'''
        with open(file_output, 'w', encoding=encoding, errors='xmlcharrefreplace') as f:
            f.write(html_with_meta)

        logging.info(f"HTML report saved to: {result}")
        return result

    @staticmethod
    def parse_plot_data(lines):
        idx_start, idx_end = -1, -1
        for i in range(len(lines)):
            line: str = lines[i]
            if line.startswith('<!--'):
                idx_start = i
            elif line.startswith('-->'):
                idx_end = i
        d = {}
        if idx_end > idx_start >= 0:
            arr = lines[idx_start + 1: idx_end]
            for item in arr:
                item = item.strip()
                if not item or '=' not in item:
                    continue
                try:
                    ss = item.split('=', 1)  # 只分割第一个等号
                    if len(ss) == 2:
                        key = ss[0].strip()
                        value_str = ss[1].strip()
                        if value_str:
                            # 处理可能包含空格的数值列表
                            data = [val.strip() for val in value_str.split(',') if val.strip()]
                            if data:
                                try:
                                    d[key] = [float(val) for val in data]
                                except ValueError:
                                    # 如果无法转换为float，跳过这个字段
                                    logging.warning(f"Failed to parse data for key '{key}': {value_str}")
                except Exception as e:
                    logging.warning(f"Error parsing plot data line '{item}': {e}")
                    continue
        return d


    @staticmethod
    def parse_plot_data(lines):
        idx_start, idx_end = -1, -1
        for i in range(len(lines)):
            line: str = lines[i]
            if line.startswith('<!--'):
                idx_start = i
            elif line.startswith('-->'):
                idx_end = i
        d = {}
        if idx_end > idx_start >= 0:
            arr = lines[idx_start + 1: idx_end]
            for item in arr:
                item = item.strip()
                if not item or '=' not in item:
                    continue
                try:
                    ss = item.split('=', 1)  # 只分割第一个等号
                    if len(ss) == 2:
                        key = ss[0].strip()
                        value_str = ss[1].strip()
                        if value_str:
                            # 处理可能包含空格的数值列表
                            data = [val.strip() for val in value_str.split(',') if val.strip()]
                            if data:
                                try:
                                    d[key] = [float(val) for val in data]
                                except ValueError:
                                    # 如果无法转换为float，跳过这个字段
                                    logging.warning(f"Failed to parse data for key '{key}': {value_str}")
                except Exception as e:
                    logging.warning(f"Error parsing plot data line '{item}': {e}")
                    continue
        return d

class XssMCPlot:

    @staticmethod
    def gen_html(fileName):
        # 延迟导入 matplotlib 以避免 NumPy 2.0 兼容性问题
        import matplotlib.pyplot as plt
        
        # 处理 file:/// 前缀
        if fileName.startswith('file:///'):
            fileName = fileName[8:]  # 移除 file:/// 前缀
        elif fileName.startswith('file://'):
            fileName = fileName[7:]  # 移除 file:// 前缀
        
        file_input = os.path.realpath(fileName)
        file_output = f"{file_input}_report.html"
        output_dir = os.path.dirname(file_output)

        s_tmp = os.path.basename(file_input)
        # 提取标识符
        unique_id = s_tmp.split('_xscript', 1)[0]

        # 统一使用UTF-8编码以支持中文
        encoding = 'utf-8'
        result = os.path.realpath(file_output)
        logging.info(f"gen_html: {id}, {result}")

        # 尝试多种编码读取文件，优先使用UTF-8
        try:
            with open(file_input, 'r', encoding='utf-8') as md_file:
                md_content = md_file.read()
        except UnicodeDecodeError:
            # 如果UTF-8失败，尝试GBK
            try:
                with open(file_input, 'r', encoding='gbk') as md_file:
                    md_content = md_file.read()
            except UnicodeDecodeError:
                # 如果GBK也失败，尝试使用errors='ignore'忽略错误字符
                with open(file_input, 'r', encoding='utf-8', errors='ignore') as md_file:
                    md_content = md_file.read()

        plot_data1 = XssMCPlot.extract_plot1_data(md_content)
        plot_data2 = XssMCPlot.extract_plot2_data(md_content)

        # 将Markdown内容转换为HTML，使用扩展以支持表格和中文
        html = markdown.markdown(md_content, extensions=['markdown.extensions.tables', 'markdown.extensions.codehilite'])

        # print(html)
        file_image1 = f"{unique_id}_plot1.png"
        img_filename1 = os.path.join(output_dir, file_image1)
        img_content1 = f'<img src="{file_image1}"/>'  # 使用字符串格式化操作符
        file_image2 = f"{unique_id}_plot2.png"
        img_filename2 = os.path.join(output_dir, file_image2)
        img_content2 = f'<img src="{file_image2}"/>'  # 使用字符串格式化操作符

        XssMCPlot.generate_plot1(plot_data1,img_filename1)
        XssMCPlot.generate_plot2(plot_data2,img_filename2)

        # 或者使用字符串格式化方法
        # content = '<img src="{}"/>'.format(filename)
        #替换关键词为图片名
        html = html.replace('<!--PLOT1-->', img_content1)
        html = html.replace('<!--PLOT2-->', img_content2)
        # 构建完整的HTML文档结构，确保中文正确显示，并添加表格样式
        html_with_meta = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monte Carlo Report</title>
    <style>
        body {{
            font-family: Arial, "Microsoft YaHei", "SimHei", sans-serif;
            line-height: 1.6;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        tr:hover {{
            background-color: #e8f5e9;
        }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #333;
            margin-top: 20px;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
{html}
</body>
</html>'''
        with open(file_output, 'w', encoding=encoding, errors='xmlcharrefreplace') as f:
            f.write(html_with_meta)


        return result

    @staticmethod
    def extract_plot1_data(original_content):
        # 使用正则表达式提取注释块中的CSV数据
        pattern = r"<!--PLOT1-->\n<!--\s*(.*?)\s*-->"
        match = re.search(pattern, original_content, re.DOTALL)

        if match:
            csv_data = match.group(1)

            # 使用numpy读取CSV数据到NumPy数组
            from io import StringIO  # StringIO用于模拟文件对象
            numpy_array = np.genfromtxt(StringIO(csv_data), delimiter=",")

            # 打印 NumPy数组
            #print(numpy_array)
        else:
            print("未找到匹配的数据块")

        return numpy_array
    
    
    @staticmethod
    def replace_nan(match):
        # 替换float('nan')为math.nan
        return match.group(1) + "math.nan" + match.group(2)
    
    @staticmethod
    def extract_plot2_data(original_content):
        # 正则表达式匹配关键词PLOT2后面的所有内容
        plot2_content = re.search(r"<!--PLOT2-->\n<!--\n(.*?)\n-->", original_content, re.DOTALL)

        if plot2_content:
            # 提取的内容
            extracted_text = plot2_content.group(1)

            # 替换-nan(ind)为math.nan
            #extracted_text = re.sub(r"(-nan\(ind\))", XssMCPlot.replace_nan, extracted_text)
            #extracted_text = re.sub(r"-nan\(ind\)", "math.nan", extracted_text)

            # 匹配SimulationData特殊处理
            simulation_data_match = re.search(r"SimulationData=({.*?})\n", extracted_text, re.DOTALL)
            if simulation_data_match:
                simulation_data_str = simulation_data_match.group(1)
                simulation_data_str = simulation_data_str.replace("{", "[").replace("}", "]")
                # 删除包含-nan(ind)的行
                #simulation_data_str = re.sub(r"\[.*?-nan\(ind\).*?\]", "", simulation_data_str, flags=re.DOTALL)
                simulation_data_str = simulation_data_str.replace("-nan(ind)","0")
                simulation_data_str = simulation_data_str.replace("''","")
                simulation_data_str = simulation_data_str + "]"
                try:
                    simulation_data = ast.literal_eval(simulation_data_str)
                except ValueError as e:
                    print(f"Error parsing SimulationData: {e}")
                    simulation_data = None
            else:
                simulation_data = None

            # 移除SimulationData部分，以便提取其他变量
            extracted_text_without_simulationdata = re.sub(r"SimulationData=({.*?})\n", "", extracted_text, flags=re.DOTALL)

            # 正则表达式匹配其他所有变量及其值
            variables = re.findall(r"(\w+)=([^\n]+)", extracted_text_without_simulationdata)

            # 将匹配到的变量和值转换成字典
            variables_dict = {var: ast.literal_eval(val) for var, val in variables if val.strip()}

            # 添加SimulationData到字典
            if simulation_data:
                variables_dict["SimulationData"] = simulation_data

            return variables_dict
        else:
            print("PLOT2 section not found or no variables extracted.")
            return None
        

    def generate_plot1(data,save_file):
        # 延迟导入 matplotlib 以避免 NumPy 2.0 兼容性问题
        import matplotlib.pyplot as plt
        from matplotlib.gridspec import GridSpec
        
        # 只取100条，应该有200条数据
        prices = data[1:101]
        num_simulations = prices.shape[0]

        # 计算模拟路径的边界
        upper_boundary = np.max(prices, axis=0)
        lower_boundary = np.min(prices, axis=0)

        # 创建网格布局
        fig = plt.figure(figsize=(10, 6))
        gs = GridSpec(1, 2, width_ratios=[4, 1])

        # 绘制模拟路径图表
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])

        for i in range(num_simulations):
            ax1.plot(prices[i])


        # 绘制模拟路径的边界
        ax1.plot(upper_boundary, color='black', linestyle='--', linewidth=2, label='Upper Boundary')
        ax1.plot(lower_boundary, color='black', linestyle='--', linewidth=2, label='Lower Boundary')


        # 设置第二个图的Y轴范围和隐藏刻度和标签
        ax2.set_ylim(ax1.get_ylim())
        ax2.set_yticks([])
        ax2.set_yticklabels([])

        # 绘制度量图（分布图）并旋转90度
        flatten_prices = prices.flatten()  # 将价格数组展平为一维
        ax_dist = ax2
        try:
            ax_dist.hist(flatten_prices, bins=30, alpha=0.5, color='green', density=True, orientation='horizontal')
        except Exception as e:
            print(f"An error occurred: {e}")
            # 这里可以添加你希望执行的跳过错误后的代码
            pass
        # 设置图表标题和标签
        ax1.set_xlabel('Time Step')
        ax1.set_ylabel('Price')
        ax_dist.set_xlabel('Distribution')
        ax_dist.set_ylabel('Price')
        ax1.set_title('Monte Carlo Simulation - Price')
        ax_dist.set_title('Distribution')

        ax1.legend(loc='upper left')

        plt.tight_layout()
        #plt.show()
        plt.savefig(save_file, dpi=100)

    def generate_plot2(simulation_data, save_file):
        # 延迟导入 matplotlib 以避免 NumPy 2.0 兼容性问题
        import matplotlib.pyplot as plt

        SimulationData = simulation_data.get('SimulationData')
        num_simulations = len(SimulationData[0])
        num_step = len(SimulationData)

        # 绘制模拟路径图表
        plt.figure(figsize=(10, 6))
        for i in range(num_step):
            plt.plot(SimulationData[i])
            
        # 添加竖直虚线
        for step in range(num_simulations):
            plt.axvline(x=step, linestyle='--', color='gray', alpha=0.5)
            
        # 添加上限和下限横线
        lines = []
        colors = ['red', 'blue', 'green', 'orange', 'purple']  # 颜色列表，可根据需要扩展

        for key, value in simulation_data.items():
            if 'STRIKE' in key.upper() or 'BARRIER' in key.upper():
                lines.append((key, value))

        for index, (key, value) in enumerate(lines):
            color = colors[index % len(colors)]  # 通过取模运算循环使用颜色
            plt.axhline(y=value, color=color, linewidth=2, linestyle='dashed', label=key)

        plt.xlabel('Time Step')
        plt.ylabel('Price')
        plt.title('Monte Carlo Simulation - Stock Price')
        plt.legend()  # 创建图例
        # plt.grid(True)
        # plt.show()
        plt.savefig(save_file, dpi=100)