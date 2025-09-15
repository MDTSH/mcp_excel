import logging
import os

import markdown
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

from mcp.xscript.utils import xss_utils

import re
import ast
import math
import numpy as np

class XssLVPlot:

    @staticmethod
    def gen_html(fileName):
        folder = xss_utils.extract_folder(fileName)
        # 确保folder以斜杠结尾，如果没有则添加斜杠
        if not folder.endswith('/'):
            folder += '/'

        s_tmp = fileName.split('/')[-1]
        # 提取标识符
        unique_id = s_tmp.split('_LocalVol', 1)[0]

        file_input =  os.path.realpath(fileName)
        file_output = f"{fileName}_report.html"
        
        encoding = 'gbk'
        result = os.path.realpath(file_output)
        logging.info(f"gen_html: {id}, {result}")

        with open(file_input, 'r', encoding=encoding) as f:
            lines = f.readlines()
            s = "\n".join(lines)
        html = markdown.markdown(s)
        # print(html)
        file_image1 = f"{unique_id}_plot1.png"
        img_filename1 = folder + f'{unique_id}_plot1.png'  # 拼接文件名
        img_content1 = f'<img src="{file_image1}"/>'  # 使用字符串格式化操作符
        file_image2 = f"{unique_id}_plot2.png"
        img_filename2 = folder + f'{unique_id}_plot2.png'  # 拼接文件名
        img_content2 = f'<img src="{file_image2}"/>'  # 使用字符串格式化操作符
        # 或者使用字符串格式化方法
        # content = '<img src="{}"/>'.format(filename)
        #替换关键词为图片名
        html = html.replace('<!--PLOT1-->', img_content1)
        html = html.replace('<!--PLOT2-->', img_content2)
        with open(file_output, 'w', encoding=encoding) as f:
            f.write(html)

        d = XssLVPlot.parse_plot_data(lines)
        # for key in d:
        #     print(f"{key} {len(d[key])}: {d[key]}")
        # 对plot1进行绘图
        plt.figure(figsize=(8, 6))
        plt.subplot(2, 1, 1)
        ax = range(len(d['midPremium']))
        plt.plot(ax, d['midPremium'], "g.", ax, d['bid'], "r.", ax, d['ask'], "r.", ax, d['inSamplePrices'], "co")
        plt.title("In sample results")
        plt.xlabel("option")
        plt.ylabel("price")
        plt.legend()

        plt.subplot(2, 1, 2)
        size = len(d['bidTesting'])
        ax2 = range(size)
        plt.plot(ax2, d['midPremiumTesting'][:size], "g.", ax2, d['bidTesting'], "r.",
                 ax2, d['askTesting'], "r.", ax2, d['outOfSamplePrices'], "co")
        plt.title("Out of sample results")
        plt.xlabel("option")
        plt.ylabel("price")
        plt.legend()
        plt.tight_layout()
        plt.savefig(img_filename1, dpi=100)


        # 对plot2进行绘图
        # 合并 midPremium 和 midPremiumTesting
        combined_premiums = d['midPremium'] + d['midPremiumTesting']
        # 合并 inSamplePrices 和 outOfSamplePrices
        combined_prices = d['inSamplePrices'] + d['outOfSamplePrices']

        # 绘制图形
        plt.figure()
        plt.scatter(combined_prices, combined_premiums, color='blue', label='Heston Premiums vs. Market Premiums')
        plt.plot([min(combined_prices), max(combined_prices)], [min(combined_premiums), max(combined_premiums)], linestyle='--', color='red', label='Equality Line')
        plt.title('Comparison of Predicted Premiums and Market Premiums')
        plt.xlabel('Market Premiums')
        plt.ylabel('Predicted Premiums')
        plt.legend()
        plt.grid(True)
        plt.savefig(img_filename2, dpi=100)

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
                ss = item.split('=')
                data = ss[1].split(',')
                d[ss[0]] = [float(val) for val in data]
        return d

class XssMCPlot:

    @staticmethod
    def gen_html(fileName):
        folder = xss_utils.extract_folder(fileName)
        # 确保folder以斜杠结尾，如果没有则添加斜杠
        if not folder.endswith('/'):
            folder += '/'

        s_tmp = fileName.split('/')[-1]
        # 提取标识符
        unique_id = s_tmp.split('_xscript', 1)[0]

        file_input =  os.path.realpath(fileName)
        file_output = f"{fileName}_report.html"
        
        encoding = 'gbk'
        result = os.path.realpath(file_output)
        logging.info(f"gen_html: {id}, {result}")

        # 读取Markdown文件内容
        with open(file_input, 'r', encoding='utf-8') as md_file:
            md_content = md_file.read()

        plot_data1 = XssMCPlot.extract_plot1_data(md_content)
        plot_data2 = XssMCPlot.extract_plot2_data(md_content)

        # 将Markdown内容转换为HTML
        html = markdown.markdown(md_content, extensions=['markdown.extensions.tables'])

        # print(html)
        file_image1 = f"{unique_id}_plot1.png"
        img_filename1 = folder + f'{unique_id}_plot1.png'  # 拼接文件名
        img_content1 = f'<img src="{file_image1}"/>'  # 使用字符串格式化操作符
        file_image2 = f"{unique_id}_plot2.png"
        img_filename2 = folder + f'{unique_id}_plot2.png'  # 拼接文件名
        img_content2 = f'<img src="{file_image2}"/>'  # 使用字符串格式化操作符

        XssMCPlot.generate_plot1(plot_data1,img_filename1)
        XssMCPlot.generate_plot2(plot_data2,img_filename2)

        # 或者使用字符串格式化方法
        # content = '<img src="{}"/>'.format(filename)
        #替换关键词为图片名
        html = html.replace('<!--PLOT1-->', img_content1)
        html = html.replace('<!--PLOT2-->', img_content2)
        with open(file_output, 'w', encoding=encoding) as f:
            f.write(html)


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