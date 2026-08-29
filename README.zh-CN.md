# MCPx（Mathema Calculation Plus）— FICC 衍生品定价库

**[English](README.md)** | **[中文](README.zh-CN.md)**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9–3.13](https://img.shields.io/badge/python-3.9--3.13-blue.svg)](https://www.python.org/downloads/)
[![PyXLL](https://img.shields.io/badge/PyXLL-Required-orange.svg)](https://www.pyxll.com/)

**版本**：v1.6（2026-08-28）· 安装包 `mcp_excel_1.6.20260828.zip` · 内核 `1.6.15103`

面向**固收、外汇与商品（FICC）** 的衍生品定价与风险管理 Python 库。MCP 为金融机构、交易台和量化分析师提供专业工具，并通过 **PyXLL 与 Excel 无缝集成**，可在电子表格中直接搭建复杂金融模型与模板。

## 🚀 主要特性

- **FICC 全覆盖**：外汇、利率、债券、波动率产品
- **专业定价模型**：Black-Scholes、Heston、Bachelier 及进阶波动率模型
- **实时与历史数据**：对接市场数据源
- **Excel 集成**：通过 PyXLL 提供加载项与 UDF
- **高性能**：C++ 核心 + Python 封装
- **生产可用**：已用于多家金融机构

## 📊 支持的金融产品

### 💱 外汇、商品与股指期权
- **香草期权**
  - 看涨 / 看跌
  - 美式期权
  - 亚式期权（平均价 / 平均执行价）
- **奇异期权**
  - 障碍期权（敲入、敲出）
  - 触碰期权（一触即付、不触碰）
  - 数字期权（现金 / 资产或无）

### 🔄 结构化外汇与贵金属产品
- **远期产品**
  - 普通远期
  - 区间远期（价差远期）
  - 保底远期
  - 封顶远期
  - 封顶保底远期（圆柱）
  - 比例远期
  - 双货币远期
  - 目标远期

### 🏦 利率产品
- **债券**
  - 到期一次还本债券
  - 含权债（可赎回等）
  - 附息债
  - 永续债
  - 浮动利率债（FRN）
- **利率互换**
  - 标准 IRS（FR007、SOFR 等）
  - 浮 / 浮互换
  - 浮 / 固互换
  - 固 / 浮互换
- **利率衍生品**
  - 债券远期
  - 债券期权
  - 互换期权（Swaption）
  - 利率上下限（Cap / Floor）
  - 远期利率协议（FRA）

### 📈 市场数据与曲线
- **曲线模型**
  - 远期曲线
  - 收益率曲线
  - 波动率曲面
  - 本地波动率模型
- **利率曲线**
  - 存款曲线
  - 债券曲线
  - 互换曲线
  - 参数化曲线
- **利率曲面**
  - Cap / Floor 波动率曲面
  - 利率期权波动率立方体

### 🏗️ 结构化产品（场外衍生品或结构性存款）
挂钩利率、汇率、商品与股指的定制结构：

- **双边不触碰**（Double No Touch）
- **三区间看跌**（Triple Ranges Put）
- **区间累积**（Range Accrual）
- **数字看涨**（Digital Call）
- **自动赎回**（Autocallables，按月观察）
- **三区间看涨**（Triple Ranges Call）
- **补贴交割远期**（Cash Delivery Forward）
- **双区间**（Double Ranges）
- **数字看跌**（Digital Put）
- **单边触碰**（Single Touch）
- **看涨看跌价差**（Call Put Spread）
- **自动赎回结构**（Auto Call）
- **鲨鱼鳍**（Shark Fin）
- **双向鲨鱼鳍**（Dual Shark Fin）
- **离散双边不触碰**（Discrete Double No Touch）
- **离散向下触碰**（Discrete One Touch Downside）
- **离散向上触碰**（Discrete One Touch Upside）
- **离散乒乓期权**（Discrete Ping Pong Option）
- **单边区间累积看涨** / **看跌**
- **更多定制结构**

#### GPU（可选）

默认 **CPU**（`lib\X64\pyxll.cfg` 中 `MCP_RUNMODE = CPU`）。本包附带 `cudart64_12.dll` 与 `curand64_10.dll`。GPU 模式还需要受支持的 NVIDIA 驱动；普通安装不必开 GPU。

## 🛠️ 安装

支持**一键安装**（推荐）和**手动安装**。

### 🚀 一键安装（推荐）

在解压后的产品根目录执行：

```cmd
install.bat
```

`quick_install.bat` 是同一入口。

#### 验证安装
请使用安装时选中的、供 Excel 使用的同一套 Python：

```cmd
python test_install.py
```

安装程序会扫描 **64 位 CPython 3.9–3.13**，写入 `lib\X64\pyxll.cfg`，并注册 `pyxll.xll`。**不会**设置用户级 `PYTHONPATH`。不支持 32 位 Excel。

**📖 详细安装说明：** [INSTALLATION.md](INSTALLATION.md) · [安装脚本](INSTALL_SCRIPTS_README.md)

### 🔧 手动安装

一键安装失败，或希望自行配置时：

#### 环境要求
- **Python**：64 位 CPython 3.9–3.13
- **系统**：Windows 10/11 64 位
- **Excel**：64 位 Microsoft Excel 2016 或更高
- **PyXLL**：生产环境需许可（评估可用试用）

#### 第 1 步：安装 Python 依赖
```bash
cd C:\path\to\mcp_excel
C:\Path\To\Python\python.exe -m pip install -r requirements.txt
```

#### 第 2 步：配置 Excel 集成
1. 将 `lib\X64\pyxll.cfg` 的 `executable` 设为该 Python 的 `pythonw.exe`。
2. 在 `[LICENSE]` 下粘贴 PyXLL 密钥；试用可留空。
3. 注册 `lib\X64\pyxll.xll`（一键安装会完成），然后重启 Excel。

不要依赖用户级 `PYTHONPATH`。`import mcp` 会按当前解释器加载 `lib\X64\_mcp.cp3xx-win_amd64.pyd`。

#### 第 3 步：验证安装
```cmd
# 测试 Python 库
python -c "import mcp; print('MCP installed successfully')"

# 运行示例
python example\calendar\quickstart.py
```

**📖 手动安装详解：** [INSTALLATION.md](INSTALLATION.md)

**📖 Python API：** [Python 用户指南](http://help.mathema.com.cn/zh/latest/api/userguide_python.html)

**📖 Excel API：** [Excel 用户指南](http://help.mathema.com.cn/zh/latest/api/userguide.html)

**🚀 第一次使用？** 请看 [5 分钟快速上手](QUICK_START.md)。

## 💡 快速示例

### 外汇香草期权定价

```python
from mcp.tool.tools_main import McpVanillaOption
from mcp.utils.enums import BuySell, CallPut, OptionExpiryNature

# 期权参数
option_args = {
    'Pair': 'USD/CNY',
    'BuySell': BuySell.Buy,
    'CallPut': CallPut.Call,
    'OptionExpiryNature': OptionExpiryNature.EUROPEAN,
    'StrikePx': 7.3,
    'SpotPx': 7.0671,
    'Volatility': 0.0484,
    'DomesticRate': 0.0186,
    'ForeignRate': 0.0475,
    'ExpiryDate': '2025-02-14',
    'DeliveryDate': '2025-02-18',
    'FaceAmount': 1000000
}

# 定价
option = McpVanillaOption(option_args)
price = option.Price()
print(f"Option Price: {price:.2f}")
```

### 收益率曲线构建

```python
from mcp.tool.tools_main import McpYieldCurve2
from mcp.utils.enums import DayCounter, Frequency

# 双边收益率曲线
curve_args = {
    'ReferenceDate': '2024-12-13',
    'Tenors': ['ON', '1M', '3M', '6M', '1Y', '2Y', '5Y'],
    'BidZeroRates': [0.0458, 0.0433, 0.0433, 0.0433, 0.0433, 0.043, 0.042],
    'AskZeroRates': [0.0459, 0.0458, 0.0458, 0.0458, 0.0458, 0.046, 0.045],
    'DayCounter': DayCounter.Act365Fixed,
    'Frequency': Frequency.Continuous
}

curve = McpYieldCurve2(curve_args)
zero_rate = curve.ZeroRate('2025-12-13', 'mid')
print(f"1Y Zero Rate: {zero_rate*100:.4f}%")
```

### 外汇远期点曲线

```python
from mcp.tool.tools_main import McpFXForwardPointsCurve2

# 双边远期点曲线
forward_args = {
    'ReferenceDate': '2024-12-13',
    'Pair': 'USD/CNY',
    'FXSpotRate': 7.1650,
    'Tenors': ['ON', '1M', '3M', '6M', '1Y'],
    'BidForwardPoints': [-22.0, -250, -733, -1393, -2395],
    'AskForwardPoints': [-21.0, -248, -730, -1390, -2390]
}

forward_curve = McpFXForwardPointsCurve2(forward_args)
points = forward_curve.FXForwardPoints('2025-03-13', 'mid')
print(f"3M Forward Points: {points:.1f}")
```

### 市场数据快照（RawMD）

仓库内带有样例快照与脚本（`excel/data/market_data/`、`example/market_data/`）：

```cmd
python example\market_data\rawmd_demo.py
```

脚本会从新到旧选取含所需曲线节点（例如 `CNHDEPO_2`）的估值日，再读零息与即期。完整日终包见 [mcp_marketdata](https://github.com/MDTSH/mcp_marketdata)（数据根指到仓库的 `snapshots/`）。

## 📁 目录结构

```
mcp_excel/
├── mcp/                          # MCP 核心库
├── lib/X64/                      # 按 ABI 标记的 _mcp.cp3xx pyd、CUDA 运行时、pyxll.xll
├── example/                      # Python 示例（含 market_data）
├── pyxll_func/                   # Excel UDF
└── excel/                        # 模板 TC01–TC46
    ├── en/
    ├── zh/
    ├── data/market_data/         # 样例快照 JSON
    └── raw_market_data/          # RawMD 加载器
```

## 📚 文档

### 入门
- **🚀 快速上手**：[5 分钟安装](QUICK_START.md)
- **📖 安装指南**：[完整安装说明](INSTALLATION.md)
- **🔧 脚本说明**：[安装脚本文档](INSTALL_SCRIPTS_README.md)

### API
- **API 参考**：[help.mathema.com.cn（中文）](http://help.mathema.com.cn/zh/latest/api/)
- **Python 指南**：[Python 用户指南](http://help.mathema.com.cn/zh/latest/api/userguide_python.html)
- **Excel 指南**：[Excel 用户指南](http://help.mathema.com.cn/zh/latest/api/userguide.html)

### 示例与学习
- **Python 示例**：见 `example/`
- **Excel 模板**：见 `excel/`（中文案例在 `excel/zh`）
- **市场数据示例**：见 `example/market_data/`
- **贡献**：[如何参与](CONTRIBUTING.md)
- **许可**：[MIT License](LICENSE)

## 🔧 运行环境

### 系统
- **操作系统**：Windows 10/11 64 位
- **Python**：64 位 CPython 3.9–3.13
- **内存**：最低 4GB，建议 8GB
- **磁盘**：约 500MB 空闲（五个 ABI 的 pyd 体积较大）
- **Excel**：64 位 Microsoft Excel 2016 或更高

### 依赖

#### 必装（安装脚本会处理）
- **NumPy**：数值计算（本包要求 `numpy>=1.19,<2`）
- **Pandas**：数据处理
- **Requests**：服务端相关 HTTP
- **Python-dateutil**：日期处理

#### 可选
- **PyXLL**：Excel 集成需商业许可
- **Matplotlib**：作图
- **Jupyter**：笔记本
- **开发工具**：pytest、black、flake8、mypy

可选依赖：

```bash
pip install -r requirements-optional.txt
```

#### Excel 集成（PyXLL）
1. **PyXLL 许可**：[pyxll.com](https://www.pyxll.com/)（或试用）
2. **PyXLL 模块**：随包装在 `pyxll/` 下（不必再 pip 装一份）
3. **注册**：运行 `install.bat`，或：
   ```bash
   python -m pyxll install --install-first --non-interactive lib/X64
   python -m pyxll activate --non-interactive lib/X64
   ```

### 安装脚本
- **install.bat** / **quick_install.bat**：一键安装
- **install_mcp_excel.py**：安装逻辑
- **test_install.py**：安装检查

## 📄 许可

本项目采用 **MIT License**，详见 [LICENSE](LICENSE)。

**请注意：**
- Python 源代码开源，可自由分发
- 编译后的二进制（`.pyd`）为专有组件
- PyXLL 需单独购买商业许可
- Excel 模板按 MIT 许可使用

## 🤝 参与贡献

欢迎贡献，请先阅读 [贡献指南](CONTRIBUTING.md)。

1. Fork 本仓库
2. 新建功能分支
3. 提交修改
4. 补充测试
5. 发起 Pull Request

## 🆘 支持

- **GitHub Issues**：[报告缺陷与需求](https://github.com/MDTSH/mcp_excel/issues)
- **文档**：[help.mathema.com.cn](http://help.mathema.com.cn/zh/latest/api/)
- **社区**：通过 Discussions 交流用法与实践

## 🏢 关于 Mathema

Mathema 团队专注量化金融与衍生品定价。MCP 平台服务于风险管理、交易台、量化研究、监管报送与组合估值等场景。

## 🔗 链接

- **官网**：[mathema.com.cn](https://mathema.com.cn)
- **文档（中文）**：[help.mathema.com.cn/zh/latest](http://help.mathema.com.cn/zh/latest/api/)
- **文档（英文）**：[help.mathema.com.cn/latest](http://help.mathema.com.cn/latest/api/)
- **PyXLL**：[www.pyxll.com](https://www.pyxll.com/)
- **GitHub**：[github.com/MDTSH](https://github.com/MDTSH)
- **市场数据标准包**：[MDTSH/mcp_marketdata](https://github.com/MDTSH/mcp_marketdata)

## ❗ 常见问题

**找不到匹配的 Python / ABI 不对**
- 请从 [python.org](https://www.python.org/downloads/) 安装 64 位 CPython 3.9–3.13
- Excel 使用的 Python 版本必须与随包的 `_mcp.cp3xx-win_amd64.pyd` 一致

**`ModuleNotFoundError: No module named 'mcp'`**
- `sys.path` 需包含 MCP 根目录（在该目录运行，或由 `pyxll.cfg` 的 `pythonpath` 提供）
- 不要依赖用户级 `PYTHONPATH`
- 用 Excel 同一套 Python 运行 `python test_install.py`

**Excel 加载项未加载**
- 关闭全部 Excel 窗口后重新运行 `install.bat`
- 确认是 64 位 Excel，且 `lib\X64\pyxll.cfg` 的 `executable` 正确

### 获取帮助

- **诊断**：`python test_install.py`
- **完整指南**：[INSTALLATION.md](INSTALLATION.md)
- **脚本说明**：[INSTALL_SCRIPTS_README.md](INSTALL_SCRIPTS_README.md)
- **GitHub Issues**：[提交问题](https://github.com/MDTSH/mcp_excel/issues)

---

**⚠️ 免责声明**：本软件供教学与专业使用。使用者须自行遵守适用法规及第三方许可条款。作者不对任何财务损失或监管违规承担责任。
