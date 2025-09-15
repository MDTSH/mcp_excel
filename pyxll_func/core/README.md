# MCP核心定价引擎模块

## 模块概述

`pyxll_func/core/` 目录包含了MCP定价引擎的核心模块，提供各种金融产品的定价和风险计算功能。所有模块都经过标准化整理，具有统一的代码风格和完整的文档注释。

## 目录结构

```
pyxll_func/core/
├── bond.py                  # 债券定价核心模块
├── option.py                # 期权定价核心模块
├── swap.py                  # 利率互换定价核心模块
├── forward.py               # 外汇结构化远期定价核心模块
├── curve.py                 # 收益率曲线核心模块
├── volatility.py            # 波动率模型核心模块
├── mcp_calendar.py          # 日历工具模块
├── mcp_server_mktdata.py    # 市场数据模块
├── server_factory.py        # 服务器工厂模块
├── xscript.py               # 脚本执行模块
├── quick_method.py          # 快速方法模块
└── utils.py                 # 通用工具模块
```

## 模块功能说明

### 1. 核心定价引擎
- **bond.py**: 固定利率债券定价，包含应计利息、现金流分析、风险指标计算
- **option.py**: 期权定价核心，包含香草期权、Black-Scholes模型、希腊字母计算
- **swap.py**: 利率互换定价，包含香草互换、跨货币互换、现金流分析
- **forward.py**: 远期定价，包含远期汇率、远期利率计算
- **curve.py**: 收益率曲线构建和插值，包含远期利率、零息利率计算
- **volatility.py**: 波动率模型，包含Heston模型、局部波动率模型

### 2. 辅助功能模块
- **mcp_calendar.py**: 日历工具，处理交易日历和日期计算
- **mcp_server_mktdata.py**: 市场数据获取和处理
- **server_factory.py**: 服务器工厂，提供带_Svr后缀的新API
- **xscript.py**: 脚本执行功能
- **quick_method.py**: 快速计算方法

### 3. 工具函数模块
- **utils.py**: 通用工具函数，包含字符串处理、数组操作、数学计算

## 代码规范

### 1. 导入规范
- 所有模块都使用统一的导入顺序：标准库 → 第三方库 → 本地模块
- 使用明确的导入语句，避免`from module import *`
- 添加类型提示支持

### 2. 函数注释
- 每个函数都有完整的docstring
- 包含参数说明、返回值说明、功能描述
- 使用中文注释，便于理解

### 3. 代码风格
- 统一的代码格式和缩进
- 清晰的函数分组和注释分隔
- 一致的命名规范

## 使用说明

### 1. Excel函数调用
所有函数都可以直接在Excel中调用，函数名和参数保持不变，确保向后兼容。

### 2. 模块导入
在Python代码中导入模块时，使用相对路径：
```python
from pyxll_func.core import bond, option, swap
```

### 3. 服务器端函数
新的服务器端函数使用`_Svr`后缀，例如：
- `McpFixedRateBond_Svr`: 服务器端固定利率债券函数
- `McpVanillaSwap_Svr`: 服务器端香草互换函数

## 维护指南

### 1. 添加新函数
- 在相应模块中添加函数
- 添加完整的docstring
- 确保函数名符合命名规范

### 2. 修改现有函数
- 保持函数签名不变
- 更新docstring
- 确保向后兼容

### 3. 代码审查
- 检查导入语句是否规范
- 确保所有函数都有注释
- 验证代码格式一致性
