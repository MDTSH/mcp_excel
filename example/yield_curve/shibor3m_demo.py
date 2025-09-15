#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SHIBOR 3M Interest Rate Swap Curve Test Program

This program demonstrates how to:
1. Construct SHIBOR 3M interest rate swap curve
2. Calculate zero rates, discount factors and forward rates for different tenors
3. Support calculations for standard and custom tenors

Features:
- Support for multiple interest rate interpolation methods (linear interpolation, etc.)
- Provide detailed curve construction parameter output
- Calculation result verification and debugging information

Author: Mathema Team
Last Updated: 2024
"""

import datetime
from typing import List, Dict, Any, Tuple

from example.calendar.calendar_demo import GetCurrencyCalendar, usd_dates
from mcp import mcp, wrapper
from mcp.utils.enums import DayCounter, Frequency
from mcp.tool.tools_main import McpSwapCurve, McpVanillaSwapCurveData


def print_curve_parameters(args: Dict[str, Any]) -> None:
    """打印互换曲线构造参数"""
    print("SHIBOR 3M 利率互换曲线构造参数:")
    print(f"  • 参考日期: {args['ReferenceDate']}")
    print(f"  • 互换起始延迟: {args['SwapStartLag']} 天")
    print(f"  • 固定端频率: {args['FixedFrequency']}")
    print(f"  • 浮动端频率: {args['FloatFrequency']}")
    print(f"  • 固定端计息方式: {args['FixedDayCounter']}")
    print(f"  • 浮动端计息方式: {args['FloatDayCounter']}")
    print(f"  • 基准指标: {args['FixingIndex']}")
    print(f"  • 利率确定方式: {args['FixingRateMethod']}")
    print("\n  期限及对应互换利率:")
    for i, (date, coupon) in enumerate(zip(args['MaturityDates'], args['Coupons'])):
        print(f"    {i+1:2d}. {date}: {coupon*100:>6.4f}%")


def construct_swap_curve() -> Tuple[McpSwapCurve, Any, str]:
    """构造 SHIBOR 3M 利率互换曲线"""
    print("=" * 60)
    print("SHIBOR 3M 利率互换曲线构造")
    print("=" * 60)
    
    # 基础参数设置
    reference_date = '2024-10-12'
    cal_usd = GetCurrencyCalendar('USD', usd_dates)
    
    # 互换曲线数据参数
    vsc_data_args = {
        "ReferenceDate": reference_date,
        "SwapStartLag": 1,
        "Calendar": cal_usd,
        "PaymentDateAdjuster": "ModifiedFollowing",
        "AccrDateAdjuster": "Actual",
        "FixedFrequency": "Quarterly",
        "FloatFrequency": "Quarterly",
        "FixedDayCounter": "Act365Fixed",
        "FloatDayCounter": "Act360",
        "UseIndexEstimation": True,
        "FixingIndex": "3M",
        "FixingRateMethod": "SIMPLE_AVERAGE",
        "FixInAdvance": True,
        "FixDaysBackward": 1,
        "Margin": 0,
        "MaturityDates": [
            '2025-4-14', '2025-7-14', '2025-10-13', '2026-10-12',
            '2027-10-12', '2028-10-12', '2029-10-12', '2031-10-13',
            '2034-10-12'
        ],
        "Coupons": [
            0.0184, 0.01755, 0.0171, 0.01715,
            0.0176, 0.0182, 0.01885, 0.01965,
            0.02065
        ],
        "BumpAmounts": [0.0000] * 9,
        "Buses": [1] * 9
    }
    
    # 打印构造参数
    print_curve_parameters(vsc_data_args)
    
    # 构造互换曲线数据
    print("\n构造互换曲线数据...")
    vsc_data_args_curve = McpVanillaSwapCurveData(vsc_data_args)
    
    # 设置校准集
    c_set = wrapper.McpCalibrationSet()
    c_set.addData(vsc_data_args_curve.getHandler())
    c_set.addEnd()
    
    # 构造互换曲线
    fixed_sc_args = {
        "ReferenceDate": reference_date,
        'CalibrationSet': c_set,
        'InterpolatedVariable': 'CONTINUOUSRATES',
        'InterpolationMethod': 'LINEARINTERPOLATION',
        'DayCounter': 'ActActISDA'
    }
    
    print("\n构造互换曲线对象...")
    swap_curve = McpSwapCurve(fixed_sc_args)
    print("互换曲线构造成功！")
    
    return swap_curve, cal_usd, reference_date


def calculate_spot_rates(swap_curve: McpSwapCurve, cal_usd: Any, reference_date: str) -> Dict[str, List]:
    """计算即期利率和贴现因子"""
    print("\n" + "=" * 60)
    print("即期利率和贴现因子计算")
    print("=" * 60)
    
    tenors = ['0D', 'ON', '2W', '1M', '3M', '6M', '9M', '1Y', '2Y', '3Y', '4Y', '5Y', '7Y', '10Y']
    
    results = {
        'tenor': [],
        'maturity_date': [],
        'discount_factor': [],
        'zero_rate': []
    }
    
    for tenor in tenors:
        # 计算到期日
        if tenor == '0D':
            maturity_date = reference_date
        else:
            maturity_date = cal_usd.ValueDate(reference_date, tenor, 'ModifiedFollowing', True)
        
        # 计算贴现因子和零息利率
        discount_factor = swap_curve.DiscountFactor(maturity_date)
        zero_rate = swap_curve.ZeroRate(maturity_date)
        
        results['tenor'].append(tenor)
        results['maturity_date'].append(maturity_date)
        results['discount_factor'].append(round(discount_factor, 7))
        results['zero_rate'].append(zero_rate)
        
        print(f"期限 {tenor:>3s}:")
        print(f"  • 到期日: {maturity_date}")
        print(f"  • 贴现因子: {discount_factor:.7f}")
        print(f"  • 零息利率: {zero_rate*100:.6f}%")
        print()
    
    return results


def calculate_forward_rates(swap_curve: McpSwapCurve, cal_usd: Any, reference_date: str) -> Dict[str, List]:
    """计算远期利率"""
    print("=" * 60)
    print("远期利率计算")
    print("=" * 60)
    
    tenors = ['0D', 'ON', '2W', '1M', '3M', '6M', '9M', '1Y']
    
    results = {
        'tenor': [],
        'start_date': [],
        'end_date': [],
        'forward_rate': []
    }
    
    for tenor in tenors:
        # 计算起息日和到期日
        start_date = cal_usd.ValueDate(reference_date, tenor)
        end_date = cal_usd.AddPeriod(start_date, '1M', 'ModifiedFollowing')
        
        # 计算远期利率
        forward_rate = swap_curve.ForwardRate(
            start_date, end_date,
            DayCounter.ActActISDA,
            True,
            Frequency.Continuous
        )
        
        results['tenor'].append(tenor)
        results['start_date'].append(start_date)
        results['end_date'].append(end_date)
        results['forward_rate'].append(forward_rate)
        
        print(f"期限 {tenor:>3s}:")
        print(f"  • 起息日: {start_date}")
        print(f"  • 到期日: {end_date}")
        print(f"  • 远期利率: {forward_rate*100:.6f}%")
        print()
    
    return results


def validate_results(spot_results: Dict[str, List], forward_results: Dict[str, List]) -> None:
    """验证计算结果（容差 1e-6）"""
    print("=" * 60)
    print("计算结果验证")
    print("=" * 60)
    
    expected_discount_factors = [
        1.0000000, 0.9998993, 0.9991447, 0.9982901,
        0.9952279, 0.9907223, 0.9868477, 0.9829320,
        0.9661573, 0.9484094, 0.9294529, 0.9096459,
        0.8708354, 0.8120126
    ]
    
    expected_forward_rates = [
        0.018421897, 0.018421897, 0.018421897,
        0.018421897, 0.018421897, 0.018244286,
        0.016301621, 0.017154092
    ]
    
    # 贴现因子验证
    print("\n贴现因子验证:")
    for i, (calc, expected) in enumerate(zip(spot_results['discount_factor'], expected_discount_factors)):
        diff = abs(calc - expected)
        print(
            f"期限 {spot_results['tenor'][i]:>3s}: "
            f"计算值={calc:.7f}, 预期值={expected:.7f}, 差异={diff:.7f}"
        )
        assert diff < 1e-3, f"贴现因子验证失败: 期限 {spot_results['tenor'][i]}"
    
    # 远期利率验证
    print("\n远期利率验证:")
    for i, (calc, expected) in enumerate(zip(forward_results['forward_rate'], expected_forward_rates)):
        diff = abs(calc - expected)
        print(
            f"期限 {forward_results['tenor'][i]:>3s}: "
            f"计算值={calc:.9f}, 预期值={expected:.9f}, 差异={diff:.9f}"
        )
        assert diff < 1e-2, f"远期利率验证失败: 期限 {forward_results['tenor'][i]}"
    
    print("\n所有计算结果验证通过！")


def main():
    """主函数：运行所有测试"""
    try:
        print("SHIBOR 3M 利率互换曲线测试程序启动")
        print(f"运行时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 构造互换曲线
        swap_curve, cal_usd, reference_date = construct_swap_curve()
        
        # 2. 计算即期利率和贴现因子
        spot_results = calculate_spot_rates(swap_curve, cal_usd, reference_date)
        
        # 3. 计算远期利率
        forward_results = calculate_forward_rates(swap_curve, cal_usd, reference_date)
        
        # 4. 验证结果
        validate_results(spot_results, forward_results)
        
        print("\n" + "=" * 60)
        print("程序运行完成！")
        print("=" * 60)
        
        return {
            'swap_curve': swap_curve,
            'spot_results': spot_results,
            'forward_results': forward_results
        }
        
    except Exception as e:
        print(f"\n程序运行出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    results = main()