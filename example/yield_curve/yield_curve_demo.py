#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Interest Rate Curve Test Suite

Contains the following test functions:
1. SHIBOR 3M interest rate swap curve test
2. FR007 interest rate swap curve test
3. Single and bilateral yield curve tests

Author: Mathema Team
Last Updated: 2024
"""

import datetime
from typing import List, Dict, Any, Tuple, Union

from example.calendar.calendar_demo import GetCurrencyCalendar, usd_dates
from mcp import mcp, wrapper
from mcp.utils.enums import DayCounter, Frequency
from mcp.mcp import MYieldCurve2, MYieldCurve
from mcp.tool.tools_main import (
    McpSwapCurve, 
    McpVanillaSwapCurveData,
    McpYieldCurve2, 
    McpYieldCurve
)


# ==============================================
# Common Utility Functions
# ==============================================
def print_curve_parameters(title: str, args: Dict[str, Any]) -> None:
    """Print curve construction parameters"""
    print(f"{title} Construction Parameters:")
    print(f"  • Reference Date: {args.get('ReferenceDate', 'N/A')}")
    if 'Tenors' in args:
        print("\n  Tenors and Corresponding Rates:")
        for i, (tenor, *rates) in enumerate(zip(
            args['Tenors'],
            *[args[k] for k in args if k.endswith('Rates')]
        )):
            rate_str = "/".join(f"{r*100:.4f}%" for r in rates)
            print(f"    {i+1:2d}. {tenor:>4s}: {rate_str}")
    elif 'MaturityDates' in args:
        print("\n  Tenors and Corresponding Swap Rates:")
        for i, (date, coupon) in enumerate(zip(args['MaturityDates'], args['Coupons'])):
            print(f"    {i+1:2d}. {date}: {coupon*100:>6.4f}%")


# ==============================================
# SHIBOR 3M Interest Rate Swap Curve Test
# ==============================================
def construct_shibor3m_curve() -> Tuple[McpSwapCurve, Any, str]:
    """Construct SHIBOR 3M interest rate swap curve"""
    print("="*60)
    print("SHIBOR 3M Interest Rate Swap Curve Construction")
    print("="*60)
    
    reference_date = '2024-10-12'
    cal_usd = GetCurrencyCalendar('USD', usd_dates)
    
    curve_args = {
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
            '2025-4-14', '2025-7-14', '2025-10-13', 
            '2026-10-12', '2027-10-12', '2028-10-12',
            '2029-10-12', '2031-10-13', '2034-10-12'
        ],
        "Coupons": [
            0.0184, 0.01755, 0.0171, 0.01715,
            0.0176, 0.0182, 0.01885, 0.01965,
            0.02065
        ],
        "BumpAmounts": [0.0000]*9,
        "Buses": [1]*9
    }
    
    print_curve_parameters("SHIBOR 3M Swap Curve", curve_args)
    
    print("\nConstructing swap curve data...")
    curve_data = McpVanillaSwapCurveData(curve_args)
    
    c_set = wrapper.McpCalibrationSet()
    c_set.addData(curve_data.getHandler())
    c_set.addEnd()
    
    swap_curve = McpSwapCurve({
        "ReferenceDate": reference_date,
        'CalibrationSet': c_set,
        'InterpolatedVariable': 'CONTINUOUSRATES',
        'InterpolationMethod': 'LINEARINTERPOLATION',
        'DayCounter': 'ActActISDA'
    })
    
    print("Curve constructed successfully!")
    return swap_curve, cal_usd, reference_date


def test_shibor3m_curve() -> Dict[str, List]:
    """Test SHIBOR 3M curve"""
    swap_curve, cal_usd, ref_date = construct_shibor3m_curve()
    
    print("\n" + "="*60)
    print("SHIBOR 3M Curve Test Results")
    print("="*60)
    
    tenors = ['0D', 'ON', '2W', '1M', '3M', '6M', '9M', '1Y', 
              '2Y', '3Y', '4Y', '5Y', '7Y', '10Y']
    
    results = {
        'tenor': [],
        'date': [],
        'discount_factor': [],
        'zero_rate': [],
        'forward_rate': []
    }
    
    for tenor in tenors:
        # Calculate maturity date
        maturity_date = ref_date if tenor == '0D' else \
            cal_usd.ValueDate(ref_date, tenor, 'ModifiedFollowing', True)
        
        # Calculate various rates
        df = swap_curve.DiscountFactor(maturity_date)
        zr = swap_curve.ZeroRate(maturity_date)
        
        # Forward rate calculation
        start_date = cal_usd.ValueDate(ref_date, tenor)
        end_date = cal_usd.AddPeriod(start_date, '1M', 'ModifiedFollowing')
        fr = swap_curve.ForwardRate(
            start_date, end_date, 
            DayCounter.ActActISDA, 
            True, 
            Frequency.Continuous
        )
        
        # 存储结果
        results['tenor'].append(tenor)
        results['date'].append(maturity_date)
        results['discount_factor'].append(round(df, 7))
        results['zero_rate'].append(zr)
        results['forward_rate'].append(fr)
        
        # 打印结果
        print(f"{tenor:>4s} | {maturity_date} | DF: {df:.7f} | ZR: {zr*100:.6f}% | FR: {fr*100:.6f}%")
    
    # 验证结果
    expected_df = [
        1.0000000, 0.9998993, 0.9991447, 0.9982901, 
        0.9952279, 0.9907223, 0.9868477, 0.9829320,
        0.9661573, 0.9484094, 0.9294529, 0.9096459, 
        0.8708354, 0.8120126
    ]
    for calc, expected in zip(results['discount_factor'], expected_df):
        assert abs(calc - expected) < 1e-3, f"贴现因子验证失败: {calc} vs {expected}"
    
    print("\n所有测试通过！")
    return results


# ==============================================
# FR007 利率互换曲线测试
# ==============================================
def construct_fr007_curve() -> Tuple[McpSwapCurve, Any, str]:
    """构造FR007利率互换曲线"""
    print("="*60)
    print("FR007利率互换曲线构造")
    print("="*60)
    
    reference_date = '2024-9-21'
    cal_usd = GetCurrencyCalendar('USD', usd_dates)
    
    curve_args = {
        "ReferenceDate": reference_date,
        "SwapStartLag": 1,
        "Calendar": cal_usd,
        "PaymentDateAdjuster": "ModifiedFollowing",
        "AccrDateAdjuster": "Actual",
        "FixedFrequency": "Quarterly",
        "FloatFrequency": "Quarterly",
        "FixedDayCounter": "Act365Fixed",
        "FloatDayCounter": "Act365Fixed",
        "UseIndexEstimation": True,
        "FixingIndex": "7D",
        "FixingRateMethod": "COMPOUNDING",
        "FixInAdvance": True,
        "FixDaysBackward": 1,
        "Margin": 0,
        "MaturityDates": [
            '2025-3-21', '2025-6-23', '2025-9-22', 
            '2026-9-21', '2027-9-21', '2028-9-21',
            '2029-9-21', '2031-9-22', '2034-9-21'
        ],
        "Coupons": [
            0.0184, 0.01755, 0.0171, 0.01715,
            0.0176, 0.0182, 0.01885, 0.01965,
            0.02065
        ],
        "BumpAmounts": [0.0000]*9,
        "Buses": [1]*9
    }
    
    print_curve_parameters("FR007互换曲线", curve_args)
    
    print("\n构造互换曲线数据...")
    curve_data = McpVanillaSwapCurveData(curve_args)
    
    c_set = wrapper.McpCalibrationSet()
    c_set.addData(curve_data.getHandler())
    c_set.addEnd()
    
    swap_curve = McpSwapCurve({
        "ReferenceDate": reference_date,
        'CalibrationSet': c_set,
        'InterpolatedVariable': 'CONTINUOUSRATES',
        'InterpolationMethod': 'LINEARINTERPOLATION',
        'DayCounter': 'ActActISDA'
    })
    
    print("曲线构造成功！")
    return swap_curve, cal_usd, reference_date


def test_fr007_curve() -> Dict[str, List]:
    """测试FR007曲线"""
    swap_curve, cal_usd, ref_date = construct_fr007_curve()
    
    print("\n" + "="*60)
    print("FR007曲线测试结果")
    print("="*60)
    
    tenors = ['0D', 'ON', '2W', '1M', '3M', '6M', '9M', '1Y', 
              '2Y', '3Y', '4Y', '5Y', '7Y', '10Y']
    fw_tenors = ['1W', '1M', '2M', '3M', '4M', '5M', '6M', '1Y']
    
    results = {
        'tenor': [],
        'date': [],
        'discount_factor': [],
        'zero_rate': [],
        'forward_rate': []
    }
    
    # 即期利率计算
    for tenor in tenors:
        maturity_date = ref_date if tenor == '0D' else \
            cal_usd.ValueDate(ref_date, tenor, 'ModifiedFollowing', True)
        
        df = swap_curve.DiscountFactor(maturity_date)
        zr = swap_curve.ZeroRate(maturity_date)
        
        results['tenor'].append(tenor)
        results['date'].append(maturity_date)
        results['discount_factor'].append(round(df, 7))
        results['zero_rate'].append(zr)
        results['forward_rate'].append(None)  # 占位
        
        print(f"{tenor:>4s} | {maturity_date} | DF: {df:.7f} | ZR: {zr*100:.6f}%")
    
    # 远期利率计算
    for tenor in fw_tenors:
        start_date = cal_usd.ValueDate(ref_date, tenor)
        end_date = cal_usd.AddPeriod(start_date, '1M', 'ModifiedFollowing')
        fr = swap_curve.ForwardRate(
            start_date, end_date, 
            DayCounter.ActActISDA, 
            True, 
            Frequency.Continuous
        )
        
        results['forward_rate'].append(fr)
        print(f"FW {tenor:>3s} | {start_date}->{end_date} | FR: {fr*100:.6f}%")
    
    # 验证结果
    expected_df = [
        1.0000000, 0.9998995, 0.9991462, 0.9983432, 
        0.9952878, 0.9907999, 0.9868674, 0.9829580,
        0.9662089, 0.9484981, 0.9295825, 0.9098264, 
        0.8710893, 0.8124332
    ]
    expected_fr = [
        0.018390719, 0.018390719, 0.018390719,
        0.018390719, 0.018390719, 0.01820524,
        0.016339207, 0.01712576
    ]
    
    for calc, expected in zip(results['discount_factor'], expected_df):
        assert abs(calc - expected) < 1e-3, f"贴现因子验证失败: {calc} vs {expected}"
    
    for calc, expected in zip(results['forward_rate'][-len(expected_fr):], expected_fr):
        assert abs(calc - expected) < 1e-3, f"远期利率验证失败: {calc} vs {expected}"
    
    print("\n所有测试通过！")
    return results


# ==============================================
# 收益率曲线测试
# ==============================================
def test_yield_curve(mode: str = 'single') -> Dict[str, List]:
    """测试收益率曲线（单边/双边）"""
    print("="*60)
    print(f"{'单边' if mode == 'single' else '双边'}收益率曲线测试")
    print("="*60)
    
    reference_date = '2024-8-9'
    cal_usd = GetCurrencyCalendar('USD', usd_dates)
    
    if mode == 'single':
        curve_args = {
            'ReferenceDate': reference_date,
            'Tenors': [
                'ON', 'TN', 'SN', 'SW', '2W', '3W', '1M', '2M', 
                '3M', '4M', '5M', '6M', '7M', '8M', '9M', '10M', 
                '11M', '1Y', '2Y', '3Y', '4Y', '5Y'
            ],
            'ZeroRates': [
                0.05275, 0.0535, 0.0535, 0.05385, 0.0539, 0.0541, 
                0.0539, 0.05335, 0.053, 0.0523, 0.0517, 0.0509, 
                0.0508, 0.05, 0.0493, 0.0492, 0.0485, 0.0478, 
                0.0439, 0.0406, 0.0395, 0.0391
            ],
            'Calendar': cal_usd,
            'Frequency': 'NoFrequency',
            'Variable': 'SIMPLERATES',
            'InterpolationMethod': 'LINEARINTERPOLATION'
        }
        yc = McpYieldCurve(curve_args)
    else:
        curve_args = {
            'ReferenceDate': reference_date,
            'Tenors': [
                'ON', 'TN', 'SN', 'SW', '2W', '3W', '1M', '2M', 
                '3M', '4M', '5M', '6M', '7M', '8M', '9M', '10M', 
                '11M', '1Y', '2Y', '3Y', '4Y', '5Y'
            ],
            'BidZeroRates': [
                0.0524, 0.0525, 0.0525, 0.0525, 0.0535, 0.0537, 
                0.0536, 0.053, 0.0526, 0.0518, 0.0512, 0.0504, 
                0.0498, 0.049, 0.0488, 0.0482, 0.0475, 0.0473, 
                0.0424, 0.0391, 0.038, 0.0376
            ],
            'AskZeroRates': [
                0.0531, 0.0545, 0.0545, 0.0552, 0.0543, 0.0545, 
                0.0542, 0.0537, 0.0534, 0.0528, 0.0522, 0.0514, 
                0.0518, 0.051, 0.0498, 0.0502, 0.0495, 0.0483, 
                0.0454, 0.0421, 0.041, 0.0406
            ],
            'Calendar': cal_usd,
            'Frequency': 'NoFrequency',
            'Variable': 'SIMPLERATES',
            'InterpolationMethod': 'LINEARINTERPOLATION'
        }
        yc = McpYieldCurve2(curve_args)
    
    print_curve_parameters("收益率曲线", curve_args)
    
    test_tenors = ['ON', '1W', '2W', '30D', '1M', '2M', '1Y']
    results = {
        'tenor': [],
        'date': [],
        'rate': [],
        'discount_factor': []
    }
    
    if mode == 'single':
        for tenor in test_tenors:
            spot_date = cal_usd.ValueDate(reference_date)
            maturity_date = cal_usd.FXOExpiryDateFromTenor(reference_date, tenor, spot_date)
            
            rate = yc.ZeroRate(maturity_date)
            df = yc.DiscountFactor(maturity_date)
            
            results['tenor'].append(tenor)
            results['date'].append(maturity_date)
            results['rate'].append(rate)
            results['discount_factor'].append(df)
            
            print(f"{tenor:>4s} | {maturity_date} | Rate: {rate*100:.6f}% | DF: {df:.8f}")
        
        # 验证结果
        expected_rates = [
            0.05275, 0.053616667, 0.053871429, 
            0.05398, 0.05394, 0.053435938, 
            0.047846667
        ]
        for calc, expected in zip(results['rate'], expected_rates):
            assert abs(calc - expected) < 1e-8, f"利率验证失败: {calc} vs {expected}"
    else:
        results.update({
            'bid_rate': [],
            'ask_rate': [],
            'mid_rate': [],
            'bid_df': [],
            'ask_df': [],
            'mid_df': []
        })
        
        for tenor in test_tenors:
            spot_date = cal_usd.ValueDate(reference_date)
            maturity_date = cal_usd.FXOExpiryDateFromTenor(reference_date, tenor, spot_date)
            
            bid = yc.ZeroRate(maturity_date, 'bid')
            ask = yc.ZeroRate(maturity_date, 'ask')
            mid = yc.ZeroRate(maturity_date, 'mid')
            
            bid_df = yc.DiscountFactor(maturity_date, 'bid')
            ask_df = yc.DiscountFactor(maturity_date, 'ask')
            mid_df = yc.DiscountFactor(maturity_date, 'mid')
            
            results['tenor'].append(tenor)
            results['date'].append(maturity_date)
            results['bid_rate'].append(bid)
            results['ask_rate'].append(ask)
            results['mid_rate'].append(mid)
            results['bid_df'].append(bid_df)
            results['ask_df'].append(ask_df)
            results['mid_df'].append(mid_df)
            
            print(f"{tenor:>4s} | {maturity_date} | Bid: {bid*100:.6f}% | Ask: {ask*100:.6f}%")
        
        # 验证结果
        expected_bids = [
            0.0524, 0.0525, 0.052928571, 
            0.05364, 0.05362, 0.05309375, 
            0.047313333
        ]
        for calc, expected in zip(results['bid_rate'], expected_bids):
            assert abs(calc - expected) < 1e-8, f"买价验证失败: {calc} vs {expected}"
    
    print("\n所有测试通过！")
    return results


# ==============================================
# 主程序
# ==============================================
def main():
    """运行所有测试"""
    print("利率曲线测试套件启动")
    print(f"运行时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 运行SHIBOR 3M测试
        shibor_results = test_shibor3m_curve()
        
        # 运行FR007测试
        fr007_results = test_fr007_curve()
        
        # 运行收益率曲线测试
        yc_single_results = test_yield_curve('single')
        yc_dual_results = test_yield_curve('dual')
        
        print("\n" + "="*60)
        print("所有测试完成！")
        print("="*60)
        
        return {
            'shibor': shibor_results,
            'fr007': fr007_results,
            'yc_single': yc_single_results,
            'yc_dual': yc_dual_results
        }
    except Exception as e:
        print(f"\n测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    results = main()