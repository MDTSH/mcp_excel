# 猛犸结构化衍生品产品定义与Payoff脚本使用指南

## 目录

1. [概述](#概述)
2. [产品结构定义](#产品结构定义)
3. [时间表（Schedules）定义](#时间表schedules定义)
4. [Payoff脚本语法](#payoff脚本语法)
5. [产品示例](#产品示例)
6. [最佳实践](#最佳实践)

---

## 概述

结构化衍生品产品定义采用YAML格式，用于描述场外衍生品的结构特征、观察时间表和收益计算逻辑。每个产品定义包含三个主要部分：

- **结构定义（structure）**：定义产品的字段、参数和约束条件
- **时间表（schedules）**：定义观察日期序列（可选）
- **Payoff脚本（payoff）**：定义收益计算逻辑

---

## 产品结构定义

### 基本结构

```yaml
packages:
  - name: ProductName
    structure:
      buy_sell_field: ""              # 买卖方向字段（空字符串表示产品内部处理）
      dates: []                        # 日期字段列表
      strikes: []                      # 行权价/障碍价字段
      barriers: []                     # 障碍价列表
      yields: []                       # 收益率字段
      percentages: []                  # 百分比字段
      arguments: []                    # 参数字段
      amounts: []                      # 金额字段
      calendars: []                    # 日历字段
      basis: Act360                    # 计息基础
      strikes_relation: ""             # 行权价关系约束（可选）
    schedules: []                      # 时间表定义（可选）
    payoff: {}                         # Payoff脚本定义
```

### 字段类型说明

#### 1. 日期字段（dates）

定义产品生命周期中的关键日期：

```yaml
dates:
  - StartDate          # 产品起始日
  - ExpiryDate         # 产品到期日
  - EndDate            # 产品结束日（最终结算日）
  - PremiumDate        # 保费支付日
```

**使用方式**：
- 在时间表中通过 `@StartDate` 引用
- 在Payoff脚本中通过 `"@StartDate"` 字符串引用
- 用于日期计算函数（如 `daysBetween`, `monthsBetween`）

#### 2. 行权价/障碍价字段（strikes）

定义产品的行权价或障碍价：

```yaml
strikes:
  - UpperBarrier       # 上障碍价
  - LowerBarrier       # 下障碍价
  - Strike             # 行权价
```

**约束条件**：
```yaml
strikes_relation: UpperBarrier > LowerBarrier  # 定义行权价之间的关系
```

#### 3. 障碍价列表（barriers）

用于定义额外的障碍价（与strikes的区别在于语义）：

```yaml
barriers:
  - KnockInBarrier
  - KnockOutBarrier
```

#### 4. 收益率字段（yields）

定义收益率参数：

```yaml
yields:
  - LowYield           # 低收益率
  - MidYield           # 中收益率
  - HighYield          # 高收益率
```

#### 5. 百分比字段（percentages）

定义百分比参数：

```yaml
percentages:
  - ParticipateRate    # 参与率
```

#### 6. 参数字段（arguments）

定义其他产品参数，只支持数字，不支持字符串：

```yaml
arguments:
  - CallPutType        # 看涨/看跌类型（0=看涨，1=看跌）
  - ObservationRate    # 观察价格
  - LockPeriod         # 锁定期（月数）
```

#### 7. 金额字段（amounts）

定义金额参数：

```yaml
amounts:
  - Notional           # 名义本金
```

#### 8. 日历字段（calendars）

定义交易日历，这里定义好后，产品参数中需要有一个对应的字段名称：

```yaml
calendars:
  - Calendar           # 交易日历
```

#### 9. 计息基础（basis）

定义计息基础：

- `Act360`：实际天数/360
- `Act365Fixed`：固定365天

---

## 时间表（Schedules）定义

时间表用于定义产品生命周期中的观察日期序列。

### 基本语法

```yaml
schedules:
  - name: ScheduleName              # 时间表名称（用于Payoff脚本）
    start: "@StartDate"             # 开始日期（引用日期字段）
    end: "@EndDate"                 # 结束日期
    frequency: Daily                # 频率：Daily, Weekly, Monthly, Quarterly, Yearly
    calendar: "@Calendar"           # 交易日历
    date_adjuster: Following        # 日期调整规则
    end_to_end: true                # 是否包含结束日期
    long_stub: false                # 长尾期处理
    end_stub: false                 # 结束尾期处理
```

### 自定义观察日（覆盖规则生成的时间表）

定价入参字典（Excel / Python，键名会转成小写）中若提供 **`{时间表name}/dates`**，且非空，则 **不再** 用 `start`/`end`/`frequency` 生成 `McpSchedule`，改为使用显式日期序列（需使用与本机 `_mcp` 一致的二进制：`MSchedule` 单参 JSON 构造）。

- 键名示例：时间表 YAML `name: ObservationSchedule` → 入参键 **`observationschedule/dates`**（大小写不敏感，与全局 `to_lower_key` 一致）。
- 取值形式任选其一：
  - JSON 数组字符串：`["20221115","20221215","20230115"]`（元素为 `StaticParse::parseVecDate` 可解析的日期字符串）；
  - `list` / `tuple` / 逗号分隔 / **分号分隔**（字符串中含 `;` 时按分号切分，否则按逗号）：由 `normalize_sdp_schedule_dates_json`（经 `pf_date` / `pf_array_date_json`）统一为上述 JSON。
- 不传或传空列表：行为与原来一致，仍按 YAML 规则生成日程。

**经 Excel `McpStructuredDerivativeProduct` 入参时**：键名以 **`/dates`** 结尾（如 `observationschedule/dates`）的参数会由 Python **先规范化**为 JSON 日期数组字符串，再 **固定放入 `additionalStringValues`**，不会进入 `additionalDateValues`。便于 C++ 在 `TradeConfig::stringArgs` 中按约定解析（与 `StaticParse::parseVecDate` 相同格式）。

### 频率选项

- `Daily`：每日
- `Weekly`：每周
- `Monthly`：每月
- `Quarterly`：每季度
- `Yearly`：每年

### 日期调整规则（date_adjuster）

- `Actual`：使用实际日期，不调整
- `Following`：调整到下一个交易日
- `ModifiedFollowing`：修改的Following规则
- `Preceding`：调整到上一个交易日

### 示例

```yaml
schedules:
  # 敲出观察时间表（月度观察）
  - name: KnockOutObservationSchedule
    start: "@StartDate"
    end: "@ExpiryDate"
    frequency: Monthly
    calendar: "@Calendar"
    date_adjuster: Following
    end_to_end: true
    long_stub: false
    end_stub: false

  # 敲入观察时间表（每日观察）
  - name: KnockInObservationSchedule
    start: "@StartDate"
    end: "@ExpiryDate"
    frequency: Daily
    calendar: "@Calendar"
    date_adjuster: Actual
    end_to_end: true
    long_stub: false
    end_stub: false
```

---

## Payoff脚本语法

Payoff脚本定义了产品在不同时点的收益计算逻辑。脚本在特定的日期或时间表上执行。

### 执行时点

Payoff脚本可以在以下时点执行：

1. **ReferenceDate**：参考日期（产品起始日），用于初始化变量
2. **日期字段**：如 `ExpiryDate`、`EndDate` 等
3. **时间表名称**：如 `ObservationSchedule`、`KnockOutObservationSchedule` 等

### 基本语法

#### 1. 变量赋值

```javascript
VariableName = Value                    # 简单赋值
VariableName = Expression               # 表达式赋值
```

**示例**：
```javascript
InitialPrice = Spot()                  # 获取当前标的价格
Yield = 0                               # 初始化收益率
aLive = 1                               # 设置状态标志
```

#### 2. 条件语句

```javascript
if (Condition) then
  Statement1
  Statement2
endIf

if (Condition) then
  Statement1
else
  Statement2
endIf

if (Condition1) then
  Statement1
else if (Condition2) then
  Statement2
else
  Statement3
endIf
```

**示例**：
```javascript
if (Spot() >= UpperBarrier) then
  IsKnockedOut = 1
endIf

if (aLive = 0) then
  Yield = MidYield
else
  Yield = LowYield
endIf
```

#### 3. 内置函数

##### 价格相关函数

- `Spot()`：获取当前标的价格
- `Spot(date)`：获取指定日期的标的价格

##### 时间相关函数

- `t()`：获取从参考日期到当前日期的年化时间（以年为单位）
- `currentDate()`：获取当前日期
- `daysBetween(date1, date2)`：计算两个日期之间的天数
- `monthsBetween(date1, date2)`：计算两个日期之间的月数

**示例**：
```javascript
DaysHeld = daysBetween("@StartDate", currentDate())
MonthsFromStart = monthsBetween("@StartDate", currentDate())
MaturityYears = daysBetween("@StartDate", "@EndDate") / 365.0
```

##### 数学函数

- `max(a, b)`：返回两个值中的较大者
- `min(a, b)`：返回两个值中的较小者
- `abs(x)`：返回绝对值
- `exp(x)`：指数函数
- `log(x)`：自然对数
- `sqrt(x)`：平方根

**示例**：
```javascript
Yield = LowYield + max(0, Spot() - ObservationRate) / ObservationRate * ParticipateRate
PriceRatio = max(0, FinalPrice / InitialPrice)
```

#### 4. 支付语句

最终支付通过 `opt pays` 语句定义：

```javascript
opt pays Expression                    # 基本支付
opt pays Expression1 + Expression2    # 复合支付
```

**示例**：
```javascript
opt pays Notional * Yield * t()                    # 支付票息
opt pays FinalPayment + Notional                   # 支付最终收益和本金
opt pays Notional * (HighYield * M1/N + LowYield * M2/N) * t()  # 范围累计支付
```
注：pays和“=”的区别在于pays会自动对结果做折现

#### 5. 辅助支付语句

除了 `opt pays`，还可以定义其他辅助支付：

```javascript
df pays Expression                    # 折现因子支付
ratio1 pays Expression                # 比例1支付
ratio2 pays Expression                # 比例2支付
```

**示例**：
```javascript
df pays N/N                           # 折现因子 = 1
ratio1 pays N_KO/N/df                 # 敲出比例
ratio2 pays N_LOW/N/df                # 敲入比例
```

### 变量作用域

- 变量在整个产品生命周期中保持状态
- 在 `ReferenceDate` 初始化的变量可以在后续所有时点访问
- 变量值在时间表或日期执行时更新

### 完整示例

```javascript
# ReferenceDate: 初始化
ReferenceDate: |
  InitialPrice = Spot()
  IsKnockedOut = 0
  IsKnockedIn = 0
  Yield = 0

# KnockInObservationSchedule: 每日检查敲入
KnockInObservationSchedule: |
  if (IsKnockedOut = 0 and IsKnockedIn = 0) then
    if (Spot() <= LowerBarrier) then
      IsKnockedIn = 1
    endIf
  endIf

# ExpiryDate: 到期结算
ExpiryDate: |
  if (IsKnockedOut = 1) then
    FinalPayment = CouponPayment
  else if (IsKnockedIn = 0) then
    FinalPayment = Notional * (MidYield / 100.0) * MaturityYears
  else
    FinalPayment = Notional * (FinalPrice / InitialPrice - 1)
  endIf

# EndDate: 最终支付
EndDate: |
  opt pays FinalPayment + Notional
```

---

## 产品示例

### 1. 数字期权（Digital Call）

**产品描述**：如果到期日标的价格高于障碍价，支付固定收益率；否则支付0。

```yaml
packages:
  - name: DigitaCall
    structure:
      dates:
        - StartDate
        - ExpiryDate
        - EndDate
        - PremiumDate
      strikes:
        - UpperBarrier
      arguments:
        - HighYield
      amounts:
        - Notional
      calendars:
        - Calendar
      basis: Act360
    payoff:
      ReferenceDate: |
        FinalRate = HighYield
      ExpiryDate: |
        if (Spot() >= UpperBarrier and FinalRate != 0) then
          FinalRate = HighYield
        else
          FinalRate = 0
        endIf
      EndDate: |
        opt pays t() * Notional * FinalRate
```

**关键点**：
- 无时间表，仅在到期日判断
- 使用 `FinalRate` 变量记录最终收益率
- 通过 `t()` 计算年化时间

### 2. 鲨鱼鳍（SharkFin）

**产品描述**：在观察期内，如果标的价格触及障碍价，产品敲出并获得中等收益率；否则根据标的价格表现计算收益率，但不超过上限。

```yaml
packages:
  - name: SharkFin
    structure:
      dates:
        - StartDate
        - EndDate
        - ExpiryDate
        - PremiumDate
      strikes:
        - Barrier
        - Strike
      percentages:
        - ParticipateRate
      arguments:
        - LowYield
        - MidYield
        - HighYield
        - CallPutType
        - ObservationRate
      amounts:
        - Notional
      calendars:
        - Calendar
      basis: Act360
    schedules:
      - name: ObservationSchedule
        start: "@StartDate"
        end: "@EndDate"
        frequency: Daily
        calendar: "@Calendar"
        date_adjuster: Actual
        end_to_end: true
    payoff:
      ReferenceDate: |
        aLive = 1
        Yield = 0
        ObservationRate = Spot()
        N = 1
        N_KO = 0
        N_LOW = 0
      ObservationSchedule: |
        if (CallPutType = 0) then
          if (aLive = 1 and Spot() >= Barrier) then
            aLive = 0
          endIf
        else
          if (aLive = 1 and Spot() < Barrier) then
            aLive = 0
          endIf
        endif
      ExpiryDate: |
        if (aLive = 0) then
          Yield = MidYield
          N_KO = 1
        else
          if (CallPutType = 0) then
            Yield = LowYield + (max(0, Spot() - ObservationRate) / ObservationRate) * ParticipateRate
            if (Spot() < ObservationRate) then
              N_LOW = 1
            endIf
          else
            Yield = LowYield + (max(0, ObservationRate - Spot()) / ObservationRate) * ParticipateRate
            if (Spot() > ObservationRate) then
              N_LOW = 1
            endIf
          endIf
        endIf
        if (Yield > HighYield) then
          Yield = HighYield
        endif
      EndDate: |
        opt pays Notional * Yield * t()
        df pays N/N
        ratio1 pays N_KO/N/df
        ratio2 pays N_LOW/N/df
```

**关键点**：
- 使用 `aLive` 标志跟踪产品是否敲出
- 在观察期内每日检查敲出条件
- 使用 `CallPutType` 区分看涨和看跌
- 收益率有上限保护（`HighYield`）

### 3. 范围累计（Range Accrual）

**产品描述**：在观察期内，如果标的价格在范围内，获得高收益率；否则获得低收益率。最终收益按范围内天数比例计算。

```yaml
packages:
  - name: RangeAccrual
    structure:
      dates:
        - StartDate
        - ExpiryDate
        - EndDate
      strikes:
        - LowerBarrier
        - UpperBarrier
      strikes_relation: UpperBarrier > LowerBarrier
      arguments:
        - HighYield
        - LowYield
      amounts:
        - Notional
      calendars:
        - Calendar
      basis: Act360
    schedules:
      - name: ObservationSchedule
        start: "@StartDate"
        end: "@EndDate"
        frequency: Daily
        calendar: "@Calendar"
        date_adjuster: Following
        end_to_end: true
    payoff:
      ReferenceDate: |
        M1 = 0    # 范围内天数
        M2 = 0    # 范围外天数
        N = 0     # 总观察天数
      ObservationSchedule: |
        N = N + 1
        if (Spot() >= LowerBarrier and Spot() <= UpperBarrier) then
          M1 = M1 + 1
        else
          M2 = M2 + 1
        endIf
      EndDate: |
        opt pays Notional * (HighYield * M1/N + LowYield * M2/N) * t()
```

**关键点**：
- 使用计数器 `M1`、`M2`、`N` 统计天数
- 每日检查价格是否在范围内
- 最终收益按比例计算

### 4. 双不触碰（Double No Touch）

**产品描述**：如果标的价格在整个观察期内从未触及上下障碍价，支付高收益率；否则支付低收益率。

```yaml
packages:
  - name: DoubleNoTouch
    structure:
      dates:
        - StartDate
        - EndDate
        - ExpiryDate
      strikes:
        - LowerBarrier
        - UpperBarrier
      strikes_relation: UpperBarrier > LowerBarrier
      arguments:
        - LowYield
        - HighYield
      amounts:
        - Notional
      calendars:
        - Calendar
      basis: Act360
    schedules:
      - name: ObservationSchedule
        start: "@StartDate"
        end: "@EndDate"
        frequency: Daily
        calendar: "@Calendar"
        date_adjuster: Actual
        end_to_end: true
    payoff:
      ReferenceDate: |
        aLive = 1
      ObservationSchedule: |
        if (aLive = 1 and (Spot() <= LowerBarrier or Spot() >= UpperBarrier)) then
          aLive = 0
        endIf
      EndDate: |
        if (aLive = 1) then
          opt pays Notional * HighYield
        else
          opt pays Notional * LowYield
        endIf
```

**关键点**：
- 使用 `aLive` 标志跟踪是否触碰障碍
- 一旦触碰，立即设置 `aLive = 0`
- 最终根据 `aLive` 状态决定支付

### 5. 雪球结构（Snowball）

**产品描述**：结合自动赎回和敲入机制的复杂产品。详见 `Snowball.yaml` 文件中的详细注释。

**关键特性**：
- 敲出观察：月度观察，锁定期后开始
- 敲入观察：每日观察
- 三种收益情况：
  1. 提前敲出：支付敲出票息
  2. 未敲出且未敲入：支付红利票息
  3. 已敲入但未敲出：承担下跌损失

---

## 最佳实践

### 1. 变量命名

- 使用有意义的变量名：`IsKnockedOut` 而不是 `flag1`
- 使用驼峰命名法：`InitialPrice`、`FinalPayment`
- 布尔标志使用 `Is` 前缀：`IsKnockedIn`、`IsKnockedOut`

### 2. 初始化

- 在 `ReferenceDate` 初始化所有变量
- 为计数器设置初始值：`N = 0`、`M1 = 0`
- 为状态标志设置初始值：`aLive = 1`、`IsKnockedOut = 0`

### 3. 条件检查

- 使用明确的比较运算符：`=` 用于相等比较
- 检查边界条件：`if (m_timeToEnd < delta_time_years)`
- 使用逻辑运算符组合条件：`and`、`or`

### 4. 时间计算

- 使用 `t()` 获取年化时间（以年为单位）
- 使用 `daysBetween` 和 `monthsBetween` 进行日期计算
- 注意日期字符串引用：`"@StartDate"` 需要引号

### 5. 支付计算

- 使用 `opt pays` 定义最终支付
- 确保支付金额考虑了时间因子：`* t()`
- 使用辅助支付记录中间结果：`df pays`、`ratio1 pays`

### 6. 调试

- 使用辅助支付输出中间变量值
- 在关键时点设置标志变量
- 检查变量是否在预期范围内

### 7. 性能优化

- 避免在时间表中进行复杂计算
- 将复杂计算移到到期日或结束日
- 使用计数器而不是重复计算

---

## 常见问题

### Q1: 如何在Payoff脚本中引用日期字段？

A: 使用 `"@DateFieldName"` 格式，注意需要引号：
```javascript
DaysHeld = daysBetween("@StartDate", currentDate())
```

### Q2: 如何获取当前标的价格？

A: 使用 `Spot()` 函数：
```javascript
CurrentPrice = Spot()
```

### Q3: 如何计算年化时间？

A: 使用 `t()` 函数，它返回从参考日期到当前日期的年化时间：
```javascript
opt pays Notional * Yield * t()
```

### Q4: 时间表中的日期如何引用？

A: 在时间表定义中使用 `@DateFieldName`（不需要引号）：
```yaml
start: "@StartDate"
end: "@EndDate"
```

### Q5: 如何定义多个时间表？

A: 在 `schedules` 列表中定义多个时间表：
```yaml
schedules:
  - name: Schedule1
    ...
  - name: Schedule2
    ...
```

### Q6: 变量作用域是什么？

A: 变量在整个产品生命周期中保持状态，在 `ReferenceDate` 初始化的变量可以在后续所有时点访问和修改。

---

## 总结

结构化衍生品产品定义系统提供了灵活而强大的方式来定义复杂的场外衍生品。通过合理使用结构定义、时间表和Payoff脚本，可以描述各种类型的结构化产品，从简单的数字期权到复杂的雪球结构。

关键要点：
- 清晰定义产品字段和参数
- 合理设计观察时间表
- 使用Payoff脚本实现收益计算逻辑
- 遵循最佳实践确保代码可读性和可维护性

更多产品示例请参考 `structured_products` 目录下的其他YAML文件。

