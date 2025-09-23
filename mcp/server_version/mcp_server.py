import copy
import math
import os
import traceback
from datetime import datetime
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# 禁用SSL警告
urllib3.disable_warnings(InsecureRequestWarning)

from mcp import wrapper
from mcp.mcp import MBillCurveData, MVanillaSwapCurveData, MFixedRateBondCurveData
from mcp.tool.tools_main import (McpFixedRateBond, McpYieldCurve, McpVanillaSwap, McpBondCurve, McpSwapCurve, \
                                 McpYieldCurve2, McpFXForwardPointsCurve2, McpMktVolSurface2, McpParametricCurve,
                                 McpFXVolSurface2,
                                 McpForwardCurve2, McpVolSurface2, McpCapVolStripping, McpSwaptionCube, McpForwardCurve,
                                 McpVolSurface, McpFXForwardPointsCurve, McpFXVolSurface, McpHistVols)
from mcp.tools import McpCalendar
from mcp.utils.enums import *
from mcp.utils.mcp_utils import excel_date_to_string
from mcp.wrapper import McpRateConvention

# default_url = "http://127.0.0.1:5000"
default_url = 'https://fxo.mathema.com.cn/McpService'
node = None

all_cache = {}
object_data_cache = {}


class McpNode:
    def __init__(self, node_url: str):
        self.node_url = node_url
        print(f'self.node_url{self.node_url}')


# node = McpNode(url)
def create_McpNode(url=default_url):
    print(f'url:{url}')
    global node
    node = McpNode(url)
    return node


def ensureAuthorized(className: str) -> str:
    return "valid-signature"  # 假设已实现

def create_no_proxy_session():
    """创建绕过VPN代理的requests session"""
    # 完全清除所有代理设置
    proxy_vars = [
        'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
        'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy',
        'FTP_PROXY', 'ftp_proxy', 'SOCKS_PROXY', 'socks_proxy'
    ]
    for var in proxy_vars:
        if var in os.environ:
            del os.environ[var]

    # 创建完全无代理的session
    session = requests.Session()
    session.proxies = {
        'http': '',
        'https': '',
        'ftp': '',
        'socks': ''
    }
    return session

def safe_post_request(url, json=None, headers=None, timeout=5):
    """安全的POST请求，自动绕过VPN代理"""
    session = create_no_proxy_session()
    
    try:
        # 尝试使用certifi证书验证
        response = session.post(url, json=json, headers=headers, timeout=timeout, verify=True)
        return response
    except requests.exceptions.SSLError:
        try:
            # 尝试禁用SSL验证
            response = session.post(url, json=json, headers=headers, timeout=timeout, verify=False)
            return response
        except requests.exceptions.RequestException:
            # 最后尝试使用urllib3直接连接
            import json as json_module
            http = urllib3.PoolManager()
            
            request_headers = dict(headers) if headers else {}
            request_headers['Content-Type'] = 'application/json'
            
            response = http.request('POST', url, 
                                  body=json_module.dumps(json).encode('utf-8') if json else None,
                                  headers=request_headers,
                                  timeout=timeout)
            
            # 转换为requests Response对象
            from requests.models import Response
            req_response = Response()
            req_response.status_code = response.status
            req_response._content = response.data
            req_response.headers = dict(response.headers)
            return req_response

class McpObject:
    _cache = {}  # 类级缓存，避免重复构造

    def __init__(self, node: McpNode, class_name: str, identifier: str):
        self.node = node
        self.class_name = class_name
        self.identifier = identifier
        self.key = ensureAuthorized(class_name)
        if not self.key:
            raise Exception(f"Unauthorized access to {class_name}")
        self._raw_data = None
        self._risk_metrics = {}

    def _call_method(self, method_name: str, *args, **kwargs):
        url = f"{self.node.node_url}/{self.class_name}/{self.identifier}/{method_name}"
        payload = {"args": list(args), **kwargs}
        headers = {"X-Signature": self.key}
        response = safe_post_request(url, json=payload, headers=headers, timeout=5)
        response_data = response.json()
        if response_data["status"] == "success":
            return response_data["result"]
        else:
            raise Exception(f"Error from server: {response_data['error']}")

    def __getattr__(self, method_name):
        def method(*args, **kwargs):
            return self._call_method(method_name, *args, **kwargs)

        return method

    @classmethod
    def create_object(cls, node: McpNode, class_name: str, identifiers: List[str], params: List[str]):
        """
        批量创建对象。
        :return: {identifier: McpObject} 字典
        """
        url = f"{node.node_url}/{class_name}/create_object"
        payload = {"identifiers": identifiers, "params": params}
        key = ensureAuthorized(class_name)
        headers = {"X-Signature": key}
        response = safe_post_request(url, json=payload, headers=headers, timeout=50)
        response_data = response.json()
        if response_data["status"] != "success":
            raise Exception(f"Batch create failed: {response_data['error']}")
        return response_data

    @classmethod
    def batch_create_objects(cls, node: McpNode, class_name: str, identifiers: List[str]):
        """
        批量创建对象。
        :return: {identifier: McpObject} 字典
        """
        url = f"{node.node_url}/{class_name}/batch_create"
        payload = {"identifiers": identifiers}
        key = ensureAuthorized(class_name)
        headers = {"X-Signature": key}
        response = safe_post_request(url, json=payload, headers=headers, timeout=5)
        response_data = response.json()
        print(response_data)
        if response_data["status"] != "success":
            raise Exception(f"Batch create failed: {response_data['error']}")

        # objects = {}
        # for identifier in identifiers:
        #     key_instance = f"{class_name}:{identifier}"
        #     if key_instance not in cls._cache:
        #         proxy = cls(node, class_name, identifier)
        #         cls._cache[key_instance] = proxy
        #     objects[identifier] = cls._cache[key_instance]
        return response_data

    @classmethod
    def batch_get_risk_metrics(cls, node: McpNode, class_name: str, identifiers: List[str], metric_names: List[str]) -> \
            Dict[str, Dict[str, float]]:
        """
        批量获取多支债券的多个风险指标。
        :return: {identifier: {metric_name: value}} 字典
        """
        url = f"{node.node_url}/{class_name}/batch_risk_metrics"
        payload = {"identifiers": identifiers, "metric_names": metric_names}
        key = ensureAuthorized(class_name)
        headers = {"X-Signature": key}
        response = safe_post_request(url, json=payload, headers=headers, timeout=5)
        response_data = response.json()
        if response_data["status"] != "success":
            raise Exception(f"Error from server: {response_data['error']}")
        return response_data["results"]

    @classmethod
    def batch_get_data(cls, node: McpNode, class_name: str, identifiers: List[str]) -> \
            Dict[str, Dict[str, float]]:
        """获取单个风险指标（带缓存）"""
        url = f"{node.node_url}/{class_name}/batch_get_raw_data"
        payload = {"identifiers": identifiers}
        key = ensureAuthorized(class_name)
        headers = {"X-Signature": key}
        response = safe_post_request(url, json=payload, headers=headers, timeout=5)
        response_data = response.json()
        if response_data["status"] != "success":
            raise Exception(f"Error from server: {response_data['error']}")
        return response_data["raw_datas"]

    @classmethod
    def batch_get_vol_data(cls, node: McpNode, class_name: str, identifiers: List[str]) -> \
            Dict[str, Dict[str, float]]:
        """获取单个风险指标（带缓存）"""
        url = f"{node.node_url}/{class_name}/batch_get_vol_data"
        payload = {"identifiers": identifiers}
        key = ensureAuthorized(class_name)
        headers = {"X-Signature": key}
        response = safe_post_request(url, json=payload, headers=headers, timeout=10)
        response_data = response.json()
        if response_data["status"] != "success":
            raise Exception(f"Error from server: {response_data['error']}")
        return response_data["raw_datas"]

    @classmethod
    def get_history_vol_data(cls, node: McpNode, class_name: str, identifiers: List[str], reference_date: str, count: int = 60, periods : int = 30) -> \
            Dict[str, Dict[str, float]]:
        """获取单个风险指标（带缓存）"""
        url = f"{node.node_url}/{class_name}/get_history_vol_data"
        payload = {"identifiers": identifiers, "reference_date": reference_date, "count": count, "periods": periods}
        key = ensureAuthorized(class_name)
        headers = {"X-Signature": key}
        response = safe_post_request(url, json=payload, headers=headers, timeout=10)
        response_data = response.json()
        if response_data["status"] != "success":
            raise Exception(f"Error from server: {response_data['error']}")
        return response_data["raw_datas"]

    @classmethod
    def get_swaptioncube_data(cls, node: McpNode, class_name: str, identifiers: List[str]) -> \
            Dict[str, Dict[str, float]]:
        """获取单个风险指标（带缓存）"""
        url = f"{node.node_url}/{class_name}/get_cube_data"
        payload = {"identifiers": identifiers}
        key = ensureAuthorized(class_name)
        headers = {"X-Signature": key}
        response = safe_post_request(url, json=payload, headers=headers, timeout=10)
        response_data = response.json()
        if response_data["status"] != "success":
            raise Exception(f"Error from server: {response_data['error']}")
        return response_data["raw_datas"]

    @classmethod
    def get_fxforward_data(cls, node: McpNode, class_name: str, identifiers: List[str], ref_date: [str]) -> \
            Dict[str, Dict[str, float]]:
        """获取单个风险指标（带缓存）"""
        url = f"{node.node_url}/{class_name}/get_fxforward_data"
        payload = {"identifiers": identifiers, "params": ref_date}
        print(f'=========payload={payload}')
        key = ensureAuthorized(class_name)
        headers = {"X-Signature": key}
        response = safe_post_request(url, json=payload, headers=headers, timeout=10)
        response_data = response.json()
        if response_data["status"] != "success":
            raise Exception(f"Error from server: {response_data['error']}")
        return response_data["raw_datas"]

def SetNode(url: str) -> str:
    global default_url
    default_url = url
    global node
    node = create_McpNode(default_url)
    return '已加载节点'

def McpBatchCreateObjects(identifiers, class_name=''):
    ids = identifiers.split(",")
    if class_name == '':
        class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    objects = McpObject.batch_create_objects(node, class_name, ids)

    global all_cache
    result = []
    for id in ids:
        row = []
        keys = f"{class_name}_{id}"
        # row.append(f"{class_name}_{id}")
        aa = objects["instances"][id]
        if class_name == "FixedRateBond":
            frb = McpFixedRateBond({
                'ValueDate': aa["ValueDate"],
                'MaturityDate': aa["MaturityDate"],
                'Coupon': aa["Coupon"],
                'Frequency': aa["Frequency"],
                'CouponType': aa["CouponType"],
                'IssuePrice': aa["IssuePrice"],
                'SettlementDate': aa["SettlementDate"],
            })
            row.append(frb)
            result.append(row)
            all_cache[keys] = frb
        elif class_name == "VanillaSwap":
            args = {
                'ReferenceDate': aa["ReferenceDate"],
                'StartDate': aa["StartDate"],
                'EndDate': aa["EndDate"],
                'RollDate': aa["RollDate"],
                'FixedPayReceive': aa["FixedPayReceive"],
                'Notional': aa["Notional"],
                'Coupon': aa["Coupon"],
                'Margin': aa["Margin"],
                'FixedPaymentFrequency': aa["FixedPaymentFrequency"],
                'FixedPaymentDateAdjuster': aa["FixedPaymentDateAdjuster"],
                'FixedPaymentDayCounter': aa["FixedPaymentDayCounter"],
                'FixedResetFrequency': aa["FixedResetFrequency"],
                'FixedResetDateAdjuster': aa["FixedResetDateAdjuster"],
                'FixedResetDayCounter': aa["FixedResetDayCounter"],
                'FloatPaymentFrequency': aa["FloatPaymentFrequency"],
                'FloatPaymentDateAdjuster': aa["FloatPaymentDateAdjuster"],
                'FloatPaymentDayCounter': aa["FloatPaymentDayCounter"],
                'FloatResetFrequency': aa["FloatResetFrequency"],
                'FloatResetDateAdjuster': aa["FloatResetDateAdjuster"],
                'FloatResetDayCounter': aa["FloatResetDayCounter"],
                'FixingFrequency': aa["FixingFrequency"],
                'FixingIndex': aa["FixingIndex"],
                'FixingDateAdjuster': aa["FixingDateAdjuster"],
                'FixInAdvance': aa["FixInAdvance"],
                'FixDaysBackward': aa["FixDaysBackward"],
                'FixingRateMethod': aa["FixingRateMethod"]
            }

            curve_keys = ['FixedCurveData', 'FloatingCurveData', 'FloatCurveData']
            calendar_cal = None
            for key in curve_keys:
                if key in aa and 'Calendar' in aa[key]:
                    currency = [aa[key]['Calendar']['currency']]
                    holidays = [aa[key]['Calendar']['holidays']]
                    calendar_cal = McpCalendar(currency, holidays)
                    aa[key]['Calendar'] = calendar_cal

                if 'BillCurveData' in aa[key] and 'SwapCurveData' in aa[key]:
                    bill_data = aa[key]['BillCurveData']
                    swap_data = aa[key]['SwapCurveData']
                    mode = aa[key]['mode']
                    insert_index = 3
                    swap_data.insert(insert_index, calendar_cal)
                    bill_curve = MBillCurveData(*bill_data)
                    # swap_curve = wrapper.McpVanillaSwapCurveData(mode, *swap_data)
                    swap_curve = wrapper.McpVanillaSwapCurveData(mode, *swap_data)
                    mCalibrationSet = wrapper.McpCalibrationSet()
                    mCalibrationSet.addData(bill_curve.getHandler())
                    mCalibrationSet.addData(swap_curve.getHandler())
                    mCalibrationSet.addEnd()
                    arg = {
                        "SettlementDate": aa[key]['SettlementDate'],
                        "CalibrationSet": mCalibrationSet,
                        "InterpolatedVariable": aa[key]['InterpolatedVariable'],
                        "InterpolationMethod": aa[key]['InterpolationMethod'],
                        "DayCounter": aa[key]['DayCounter'],
                        "UseGlobalSolver": aa[key]['UseGlobalSolver'],
                        "PillarEndDate": aa[key]['PillarEndDate']
                    }
                    swap_curve = McpSwapCurve(arg)
                    if key == 'FixedCurveData':
                        args.update({
                            # "FixedEstimationCurve": swap_curve,
                            "FixedDiscountCurve": swap_curve,
                        })
                    elif key == 'FloatingCurveData':
                        args.update({
                            # "FloatingEstimationCurve": swap_curve,
                            "FloatDiscountCurve": swap_curve,
                        })
                    else:
                        args.update({
                            "FloatEstimationCurve": swap_curve,
                            # "FloatDiscountCurve": swap_curve,
                        })
                elif 'Buses' in aa[key]:
                    SwapCurve = McpSwapCurve(aa[key])
                    if key == 'FixedCurveData':
                        args.update({
                            # "FixedEstimationCurve": SwapCurve,
                            "FixedDiscountCurve": SwapCurve,
                        })
                    elif key == 'FloatingCurveData':
                        args.update({
                            # "FloatingEstimationCurve": SwapCurve,
                            "FloatDiscountCurve": SwapCurve,
                        })
                    else:
                        args.update({
                            "FloatEstimationCurve": SwapCurve,
                            # "FloatDiscountCurve": SwapCurve,
                        })
                else:
                    YieldCurve = McpYieldCurve(aa[key])
                    if key == 'FixedCurveData':
                        args.update({
                            # "FixedEstimationCurve": YieldCurve,
                            "FixedDiscountCurve": YieldCurve,
                        })
                    elif key == 'FloatingCurveData':
                        args.update({
                            # "FloatingEstimationCurve": YieldCurve,
                            "FloatDiscountCurve": YieldCurve,
                        })
                    else:
                        args.update({
                            "FloatEstimationCurve": YieldCurve,
                            # "FloatDiscountCurve": YieldCurve,
                        })
            frb = McpVanillaSwap(args)
            row.append(frb)
            result.append(row)
            all_cache[keys] = frb
    return result

def McpFixedRateBonds_(identifiers):
    ids = identifiers.split(",")
    class_name = "FixedRateBond"
    result = []
    # ids_no_cache = []
    # global all_cache
    # for i in ids:
    #     keys = f"{class_name}_{i}"
    #     if keys in all_cache:
    #         result.append(all_cache[keys])
    #     else:
    #         ids_no_cache.append(i)
    global node
    if node is None:
        node = create_McpNode()
        # if len(ids_no_cache) > 0:
    objects = McpObject.batch_create_objects(node, class_name, ids)
    for id in ids:
        keys = f"{class_name}_{id}"
        row = []
        instance = objects["instances"][id]
        args = {
            'ValueDate': instance["ValueDate"],
            'MaturityDate': instance["MaturityDate"],
            'Coupon': instance["Coupon"],
            'Frequency': instance["Frequency"],
            'CouponType': instance["CouponType"],
            'IssuePrice': instance["IssuePrice"],
            'SettlementDate': instance["SettlementDate"],
        }
        frb = McpFixedRateBond(args)
        row.append(frb)
        result.append(row)
        all_cache[keys] = frb
        object_data_cache[frb] = args
    return result

def McpFixedRateBonds(identifiers, settlement_date=None):
    if settlement_date is None:
        return McpFixedRateBonds_(identifiers)

    ids = identifiers.split(",")
    class_name = "FixedRateBond"
    settlement_date = excel_date_to_string(settlement_date)
    result = []
    global node
    if node is None:
        node = create_McpNode()
    objects = McpObject.create_object(node, class_name, ids, [f'{settlement_date}'])
    for id in ids:
        keys = f"{class_name}_{id}"
        row = []
        instance = objects["instances"][id]
        args = {
            'ValueDate': instance["ValueDate"],
            'MaturityDate': instance["MaturityDate"],
            'Coupon': instance["Coupon"],
            'Frequency': instance["Frequency"],
            'CouponType': instance["CouponType"],
            'IssuePrice': instance["IssuePrice"],
            'SettlementDate': instance["SettlementDate"],
        }
        frb = McpFixedRateBond(args)
        row.append(frb)
        result.append(row)
        all_cache[keys] = frb
        object_data_cache[frb] = args
    return result


def McpBond(identifier, settlement_date=None):
    class_name = "FixedRateBond"
    settlement_date = excel_date_to_string(settlement_date)
    global node
    if node is None:
        node = create_McpNode()
    objects = McpObject.create_object(node, class_name, [identifier], [f'{settlement_date}'])
    keys = f"{class_name}_{identifier}"
    instance = objects["instances"][identifier]
    args = {
        'SettlementDate': instance["SettlementDate"],
        'MaturityDate': instance["MaturityDate"],
        'Frequency': instance["Frequency"],
        'Coupon': instance["Coupon"],
        'CouponType': instance["CouponType"],
        'ValueDate': instance["ValueDate"],
        'IssuePrice': instance["IssuePrice"],
        'DayCounter': DayCounter.ActActXTR,
    }
    # 直接调用tool_def.tool_create避免函数名冲突
    frb = McpFixedRateBond(args)
    all_cache[keys] = frb
    object_data_cache[frb] = args
    return frb

def McpFixedRateBondsData(mcpFixedRateBond, flag=False):
    obj = object_data_cache[mcpFixedRateBond]
    # ordered_dict = sort_dict_by_order(obj, fixed_bond_field)
    return decode(obj, flag)

def McpBondCurves(identifiers):
    ids = identifiers.split(",")
    class_name = 'BondCurve'
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_data(node, class_name, ids)
    # result = []
    # for curve_data in results.values():
    #     bond_curve = McpBondCurve(curve_data)
    #     result.append(bond_curve)
    #     object_data_cache[bond_curve] = curve_data
    # return result
    deep_copied_list = copy.deepcopy(results)
    for curve_name in ids:
        keys = f"{class_name}_{curve_name}"
        arg = results[curve_name]
        frb = McpBondCurve(arg)
        all_cache[keys] = frb
        object_data_cache[frb] = deep_copied_list[curve_name]
        return frb

def McpBondCurvesData(mcpBondCurve, flag=False):
    obj = object_data_cache[mcpBondCurve]
    # ordered_dict = sort_dict_by_order(obj, bond_curve_field)
    return decode(obj, flag)

def McpParametricCurves(identifiers):
    ids = identifiers.split(",")
    class_name = 'ParametricCurve'
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_data(node, class_name, ids)

    deep_copied_list = copy.deepcopy(results)
    for curve_name in ids:
        keys = f"{class_name}_{curve_name}"
        arg = results[curve_name]
        frb = McpParametricCurve(arg)
        all_cache[keys] = frb
        object_data_cache[frb] = deep_copied_list[curve_name]
        return frb

def McpParametricCurvesData(mcpParametricCurve, flag=False):
    obj = object_data_cache[mcpParametricCurve]
    # ordered_dict = sort_dict_by_order(obj, bond_curve_field)
    return decode(obj, flag)

def McpBondRemainingMaturity(identifiers):
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, [f'GetRemainingMaturity'])
    metrics1 = ['GetRemainingMaturity']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics1] for id in ids]

def get_result(ids, results, flag):
    # 动态获取所有可能的字段名
    fields = set()
    for id_data in results.values():
        fields.update(id_data.keys())
    # fields = sorted(fields)  # 排序以保证结果的一致性

    # 初始化结果列表，先添加字段名列表
    result = []

    # 遍历每个 id，提取对应的值
    for id in ids:
        for field in fields:
            row = []
            row.append(field)
            value = results[id].get(field)
            if isinstance(value, float) and math.isnan(value):
                row.append("#N/A")
            # elif type(value) == list:
            #     for l1 in value:
            #         row.append(l1)
            else:
                row.append(value)
            result.append(row)
    max_length = max(len(sublist) for sublist in result)
    padded_data = [sublist + [''] * (max_length - len(sublist)) for sublist in result]
    result = np.array(padded_data, dtype=object)

    if flag:
        # 将二维列表转换为 numpy 数组
        original_array = np.array(result, dtype=object)

        # 进行转置操作
        transposed_array = original_array.T

        # 将转置后的 numpy 数组转换为二维列表
        transposed_list = transposed_array.tolist()
        return transposed_list
    return result

def McpCalenders(ccy):
    ids = ccy.split(",")
    class_name = "Calender"
    result = []
    # ids_no_cache = []
    # global all_cache
    # for i in ids:
    #     keys = f"{class_name}_{i}"
    #     if keys in all_cache:
    #         result.append(all_cache[keys])
    #     else:
    #         ids_no_cache.append(i)
    global node
    if node is None:
        node = create_McpNode()
    # if len(ids_no_cache) > 0:
    results = McpObject.batch_get_data(node, class_name, ids)
    currencys = []
    holidays = []
    for name in ids:
        keys = f"{class_name}_{name}"
        currency = results[name]['currency']
        holiday = results[name]['holidays']
        currencys.append(currency)
        holidays.append(holiday)

    cal = McpCalendar(currencys, holidays)
    # result.append(cal)
    all_cache[ccy] = cal
    results={}
    results['currency'] = currencys
    results['holidays'] = holidays
    object_data_cache[cal] = results
    # calendar_cal = McpCalendar(currencys, holidays)
    return cal

def McpCalendersData(mcpCalender, flag=False):
    obj = object_data_cache[mcpCalender]
    # ordered_dict = sort_dict_by_order(obj, calender_field_order)
    return decode(obj, flag)

def McpVanillaSwaps2(identifiers, enddate='', swaprate='', point='0'):
    enddate = excel_date_to_string(enddate)
    ids = identifiers.split(",")
    params = ''
    class_name = "VanillaSwap"
    result = []
    global node
    if node is None:
        node = create_McpNode()
    objects = McpObject.create_object(node, class_name, ids, [f'{swaprate}|{enddate}|{point}'])
    for id in ids:
        row = []
        keys = f"{class_name}_{id}"
        aa = objects["instances"][id]
        args = {
            'ReferenceDate': aa["ReferenceDate"],
            'StartDate': aa["StartDate"],
            'EndDate': aa["EndDate"],
            'RollDate': aa["RollDate"],
            'FixedPayReceive': aa["FixedPayReceive"],
            'Notional': aa["Notional"],
            'Coupon': round(float(aa['Coupon']), 8),
            'Margin': aa["Margin"],
            'FixedPaymentFrequency': aa["FixedPaymentFrequency"],
            'FixedPaymentDateAdjuster': aa["FixedPaymentDateAdjuster"],
            'FixedPaymentDayCounter': aa["FixedPaymentDayCounter"],
            'FixedResetFrequency': aa["FixedResetFrequency"],
            'FixedResetDateAdjuster': aa["FixedResetDateAdjuster"],
            'FixedResetDayCounter': aa["FixedResetDayCounter"],
            'FloatPaymentFrequency': aa["FloatPaymentFrequency"],
            'FloatPaymentDateAdjuster': aa["FloatPaymentDateAdjuster"],
            'FloatPaymentDayCounter': aa["FloatPaymentDayCounter"],
            'FloatResetFrequency': aa["FloatResetFrequency"],
            'FloatResetDateAdjuster': aa["FloatResetDateAdjuster"],
            'FloatResetDayCounter': aa["FloatResetDayCounter"],
            'FixingFrequency': aa["FixingFrequency"],
            'FixingIndex': aa["FixingIndex"],
            'FixingDateAdjuster': aa["FixingDateAdjuster"],
            'FixInAdvance': aa["FixInAdvance"],
            'FixDaysBackward': aa["FixDaysBackward"],
            'FixingRateMethod': aa["FixingRateMethod"]
        }

        curve_keys = ['FixedCurveData', 'FloatingCurveData', 'FloatCurveData']
        calendar_cal = None
        for key in curve_keys:
            if key in aa and 'Calendar' in aa[key]:
                currency = [aa[key]['Calendar']['currency']]
                holidays = [aa[key]['Calendar']['holidays']]
                calendar_cal = McpCalendar(currency, holidays)
                aa[key]['Calendar'] = calendar_cal

            if 'BillCurveData' in aa[key] and 'SwapCurveData' in aa[key]:
                bill_data = aa[key]['BillCurveData']
                swap_data = aa[key]['SwapCurveData']
                mode = aa[key]['mode']
                insert_index = 3
                swap_data.insert(insert_index, calendar_cal)
                bill_curve = MBillCurveData(*bill_data)
                swap_curve = wrapper.McpVanillaSwapCurveData(mode, *swap_data)
                mCalibrationSet = wrapper.McpCalibrationSet()
                mCalibrationSet.addData(bill_curve.getHandler())
                mCalibrationSet.addData(swap_curve.getHandler())
                mCalibrationSet.addEnd()
                arg = {
                    "SettlementDate": aa[key]['SettlementDate'],
                    "CalibrationSet": mCalibrationSet,
                    "InterpolatedVariable": aa[key]['InterpolatedVariable'],
                    "InterpolationMethod": aa[key]['InterpolationMethod'],
                    "DayCounter": aa[key]['DayCounter'],
                    "UseGlobalSolver": aa[key]['UseGlobalSolver'],
                    "PillarEndDate": aa[key]['PillarEndDate']
                }
                swap_curve = McpSwapCurve(arg)
                if key == 'FixedCurveData':
                    args.update({
                        # "FixedEstimationCurve": swap_curve,
                        "FixedDiscountCurve": swap_curve,
                    })
                elif key == 'FloatingCurveData':
                    args.update({
                        # "FloatingEstimationCurve": swap_curve,
                        "FloatDiscountCurve": swap_curve,
                    })
                else:
                    args.update({
                        "FloatEstimationCurve": swap_curve,
                        # "FloatDiscountCurve": swap_curve,
                    })
            elif 'Buses' in aa[key]:
                SwapCurve = McpSwapCurve(aa[key])
                if key == 'FixedCurveData':
                    args.update({
                        # "FixedEstimationCurve": SwapCurve,
                        "FixedDiscountCurve": SwapCurve,
                    })
                elif key == 'FloatingCurveData':
                    args.update({
                        # "FloatingEstimationCurve": SwapCurve,
                        "FloatDiscountCurve": SwapCurve,
                    })
                else:
                    args.update({
                        "FloatEstimationCurve": SwapCurve,
                        # "FloatDiscountCurve": SwapCurve,
                    })
            else:
                YieldCurve = McpYieldCurve(aa[key])
                if key == 'FixedCurveData':
                    args.update({
                        # "FixedEstimationCurve": YieldCurve,
                        "FixedDiscountCurve": YieldCurve,
                    })
                elif key == 'FloatingCurveData':
                    args.update({
                        # "FloatingEstimationCurve": YieldCurve,
                        "FloatDiscountCurve": YieldCurve,
                    })
                else:
                    args.update({
                        "FloatEstimationCurve": YieldCurve,
                        # "FloatDiscountCurve": YieldCurve,
                    })
        print(f'args{args}')
        frb = McpVanillaSwap(args)
        swaprate = frb.CalculateSwapRateFromNPV(0)
        args['Coupon'] = swaprate
        frb = McpVanillaSwap(args)
        row.append(frb)
        result.append(row)
        object_data_cache[frb] = aa
    return result

def McpVanillaSwaps(identifiers):
    ids = identifiers.split(",")
    class_name = "VanillaSwap"
    result = []
    # ids_no_cache = []
    # global all_cache
    # for i in ids:
    #     keys = f"{class_name}_{i}"
    #     if keys in all_cache:
    #         result.append(all_cache[keys])
    #     else:
    #         ids_no_cache.append(i)
    global node
    if node is None:
        node = create_McpNode()
    # if len(ids_no_cache) > 0:
    objects = McpObject.batch_create_objects(node, class_name, ids)
    for id in ids:
        row = []
        keys = f"{class_name}_{id}"
        aa = objects["instances"][id]
        args = {
            'ReferenceDate': aa["ReferenceDate"],
            'StartDate': aa["StartDate"],
            'EndDate': aa["EndDate"],
            'RollDate': aa["RollDate"],
            'FixedPayReceive': aa["FixedPayReceive"],
            'Notional': aa["Notional"],
            'Coupon': round(float(aa['Coupon']), 8),
            'Margin': aa["Margin"],
            'FixedPaymentFrequency': aa["FixedPaymentFrequency"],
            'FixedPaymentDateAdjuster': aa["FixedPaymentDateAdjuster"],
            'FixedPaymentDayCounter': aa["FixedPaymentDayCounter"],
            'FixedResetFrequency': aa["FixedResetFrequency"],
            'FixedResetDateAdjuster': aa["FixedResetDateAdjuster"],
            'FixedResetDayCounter': aa["FixedResetDayCounter"],
            'FloatPaymentFrequency': aa["FloatPaymentFrequency"],
            'FloatPaymentDateAdjuster': aa["FloatPaymentDateAdjuster"],
            'FloatPaymentDayCounter': aa["FloatPaymentDayCounter"],
            'FloatResetFrequency': aa["FloatResetFrequency"],
            'FloatResetDateAdjuster': aa["FloatResetDateAdjuster"],
            'FloatResetDayCounter': aa["FloatResetDayCounter"],
            'FixingFrequency': aa["FixingFrequency"],
            'FixingIndex': aa["FixingIndex"],
            'FixingDateAdjuster': aa["FixingDateAdjuster"],
            'FixInAdvance': aa["FixInAdvance"],
            'FixDaysBackward': aa["FixDaysBackward"],
            'FixingRateMethod': aa["FixingRateMethod"]
        }

        curve_keys = ['FixedCurveData', 'FloatingCurveData', 'FloatCurveData']
        calendar_cal = None
        for key in curve_keys:
            if key in aa and 'Calendar' in aa[key]:
                currency = [aa[key]['Calendar']['currency']]
                holidays = [aa[key]['Calendar']['holidays']]
                calendar_cal = McpCalendar(currency, holidays)
                aa[key]['Calendar'] = calendar_cal

            if 'BillCurveData' in aa[key] and 'SwapCurveData' in aa[key]:
                bill_data = aa[key]['BillCurveData']
                swap_data = aa[key]['SwapCurveData']
                mode = aa[key]['mode']
                insert_index = 3
                swap_data.insert(insert_index, calendar_cal)
                bill_curve = MBillCurveData(*bill_data)
                swap_curve = wrapper.McpVanillaSwapCurveData(mode, *swap_data)
                mCalibrationSet = wrapper.McpCalibrationSet()
                mCalibrationSet.addData(bill_curve.getHandler())
                mCalibrationSet.addData(swap_curve.getHandler())
                mCalibrationSet.addEnd()
                arg = {
                    "SettlementDate": aa[key]['SettlementDate'],
                    "CalibrationSet": mCalibrationSet,
                    "InterpolatedVariable": aa[key]['InterpolatedVariable'],
                    "InterpolationMethod": aa[key]['InterpolationMethod'],
                    "DayCounter": aa[key]['DayCounter'],
                    "UseGlobalSolver": aa[key]['UseGlobalSolver'],
                    "PillarEndDate": aa[key]['PillarEndDate']
                }
                swap_curve = McpSwapCurve(arg)
                if key == 'FixedCurveData':
                    args.update({
                        # "FixedEstimationCurve": swap_curve,
                        "FixedDiscountCurve": swap_curve,
                    })
                elif key == 'FloatingCurveData':
                    args.update({
                        # "FloatingEstimationCurve": swap_curve,
                        "FloatDiscountCurve": swap_curve,
                    })
                else:
                    args.update({
                        "FloatEstimationCurve": swap_curve,
                        # "FloatDiscountCurve": swap_curve,
                    })
            elif 'Buses' in aa[key]:
                SwapCurve = McpSwapCurve(aa[key])
                if key == 'FixedCurveData':
                    args.update({
                        # "FixedEstimationCurve": SwapCurve,
                        "FixedDiscountCurve": SwapCurve,
                    })
                elif key == 'FloatingCurveData':
                    args.update({
                        # "FloatingEstimationCurve": SwapCurve,
                        "FloatDiscountCurve": SwapCurve,
                    })
                else:
                    args.update({
                        "FloatEstimationCurve": SwapCurve,
                        # "FloatDiscountCurve": SwapCurve,
                    })
            else:
                YieldCurve = McpYieldCurve(aa[key])
                if key == 'FixedCurveData':
                    args.update({
                        # "FixedEstimationCurve": YieldCurve,
                        "FixedDiscountCurve": YieldCurve,
                    })
                elif key == 'FloatingCurveData':
                    args.update({
                        # "FloatingEstimationCurve": YieldCurve,
                        "FloatDiscountCurve": YieldCurve,
                    })
                else:
                    args.update({
                        "FloatEstimationCurve": YieldCurve,
                        # "FloatDiscountCurve": YieldCurve,
                    })
        print(f'args{args}')
        frb = McpVanillaSwap(args)
        row.append(frb)
        result.append(row)
        all_cache[keys] = frb
        object_data_cache[frb] = aa
    return result

def McpVanillaSwapsData(mcpVanillaSwap, flag=False):
    obj = object_data_cache[mcpVanillaSwap]

    # ordered_dict = sort_dict_by_order(obj, swap_fields)
    result = decode(obj, flag)
    # print(result)
    return [node for node in result if not (node[0] == 'SwaptionCube' )]

def McpVolSurfaces(identifiers):
    ids = identifiers.split(",")
    class_name = 'VolSurface'
    global node
    if node is None:
        node = create_McpNode()

    results = McpObject.batch_get_data(node, class_name, ids)
    deep_copied_list = copy.deepcopy(results)
    for vol_name in ids:
        data = results[vol_name]

        acc_data = data['DomesticCurve2']
        currency = [acc_data['Calendar']['currency']]
        holidays = [acc_data['Calendar']['holidays']]
        calendar_cal = McpCalendar(currency, holidays)
        acc_data['Calendar'] = calendar_cal.getHandler()
        acc_curve = McpYieldCurve2(acc_data)

        und_data = data['ForeignCurve2']
        currency1 = [und_data['Calendar']['currency']]
        holidays1 = [und_data['Calendar']['holidays']]
        calendar_cal1 = McpCalendar(currency1, holidays1)
        und_data['Calendar'] = calendar_cal1.getHandler()
        und_curve = McpYieldCurve2(und_data)

        point_data = data['FxForwardPointsCurve2']
        currency2 = point_data['Calendar']['currency']
        holidays2 = point_data['Calendar']['holidays']
        calendar_cal2 = McpCalendar(currency2, holidays2)
        point_data['Calendar'] = calendar_cal2.getHandler()
        point_curve = McpFXForwardPointsCurve2(point_data)
        bid_list_array = data['BidVolatilities']
        ask_list_array = data['AskVolatilities']
        var_args = {
            'ShortName': data['ShortName'],
            'Symbol': data['Symbol'],
            'DayCounter': data['DayCounter'],
            'DateAdjusterRule': data['DateAdjusterRule'],
            'DeltaType': data['DeltaType'],
            'UndCurve': data['UndCurve'],
            'AccCurve': data['AccCurve'],
            'DomesticCurve2': acc_curve,
            'SmileInterpMethod': data['SmileInterpMethod'],
            'FxForwardPointsCurve': data['FxForwardPointsCurve'],
            'PremiumAdjusted': data['PremiumAdjusted'],
            'IsATMFwd': data['IsATMFwd'],
            'calculatedTarget': data['calculatedTarget'],
            'ReferenceDate': data['ReferenceDate'],
            'DeltaStrings': data['DeltaStrings'],
            'Tenors': data['Tenors'],
            'BidVolatilities': ';'.join([', '.join(map(str, sub_list)) for sub_list in bid_list_array]),
            'AskVolatilities': ';'.join([', '.join(map(str, sub_list)) for sub_list in ask_list_array]),
            'FxForwardPointsCurve2': point_curve,
            'ForeignCurve2': und_curve,
            'Calendar': calendar_cal2
        }
        frb = McpFXVolSurface2(var_args)
        object_data_cache[frb] = deep_copied_list[vol_name]
        return frb
    return 'fail'

def McpVolSurfacesData(mcpVolSurfaces, flag=False):
    obj = object_data_cache[mcpVolSurfaces]
    # ordered_dict = sort_dict_by_order(obj, swap_curve_field)
    return decode(obj, flag)

def McpHistory(identifiers, reference_date, count, periods):
    ids = identifiers.split(",")
    class_name = 'BondCurveHistory'
    global all_cache
    for i in ids:
        keys = f"{class_name}_{i}"
        if keys in all_cache:
            return all_cache[keys]

    global node
    if node is None:
        node = create_McpNode()


    results = McpObject.get_history_vol_data(node, class_name, ids, reference_date, int(count), int(periods))
    deep_copied_list = copy.deepcopy(results)
    for curve_name in ids:
        keys = f"{class_name}_{id}"
        args = results[curve_name]
        vsf = McpHistVols(args)
        all_cache[keys] = vsf
        object_data_cache[vsf] = deep_copied_list[curve_name]
        return vsf

def McpBondMarketData(identifiers, key):
    ids = identifiers.split(",")
    class_name = 'BondMKT'
    global all_cache
    for i in ids:
        keys = f"{class_name}_{i}"
        if keys in all_cache:
            return all_cache[keys]

    global node
    if node is None:
        node = create_McpNode()

    results = McpObject.get_history_vol_data(node, class_name, ids, "", 30)
    for curve_name in ids:
        # 动态获取所有可能的字段名
        fields = set()
        for id_data in results.values():
            fields.update(id_data.keys())
        for field in fields:
            if key == field:
                return results[curve_name].get(field)

def McpBondMarketArgs(identifiers):
    ids = identifiers.split(",")
    class_name = 'BondMKT'
    global all_cache
    for i in ids:
        keys = f"{class_name}_{i}"
        if keys in all_cache:
            return all_cache[keys]

    global node
    if node is None:
        node = create_McpNode()

    results = McpObject.get_history_vol_data(node, class_name, ids, "", 30, 10)
    for curve_name in ids:
        # 动态获取所有可能的字段名
        fields = []
        for id_data in results.values():
            for keyss in id_data.keys():
                fields.append(keyss)
        temp = {}
        temp["keys"] = fields
        # 将二维列表转换为 numpy 数组
        original_array = np.array(temp, dtype=object)
        # 进行转置操作
        transposed_array = original_array.T
        # 将转置后的 numpy 数组转换为二维列表
        transposed_list = transposed_array.tolist()
        # print(f'result1:{transposed_list}')
        return transposed_list

def McpSwapCurves(identifiers):
    ids = identifiers.split(",")
    class_name = 'SwapCurve'
    global all_cache
    for i in ids:
        keys = f"{class_name}_{i}"
        if keys in all_cache:
            return all_cache[keys]

    global node
    if node is None:
        node = create_McpNode()

    results = McpObject.batch_get_data(node, class_name, ids)
    deep_copied_list = copy.deepcopy(results)
    for curve_name in ids:
        keys = f"{class_name}_{id}"
        currency = [results[curve_name]['Calendar']['currency']]
        holidays = [results[curve_name]['Calendar']['holidays']]
        calendar_cal = McpCalendar(currency, holidays)
        results[curve_name]['Calendar'] = calendar_cal
        if 'BondCurveData' in results[curve_name] and 'BillCurveData' in results[curve_name]:
            bond_data = results[curve_name]['BondCurveData']
            bill_data = results[curve_name]['BillCurveData']
            bond_data.insert(len(bond_data), calendar_cal.getHandler())
            bond_curve_data = MFixedRateBondCurveData(*bond_data)
            bill_curve = MBillCurveData(*bill_data)
            mCalibrationSet = wrapper.McpCalibrationSet()
            mCalibrationSet.addData(bond_curve_data.getHandler())
            mCalibrationSet.addData(bill_curve.getHandler())
            if 'SwapCurveData' in results[curve_name]:
                swap_data = results[curve_name]['SwapCurveData']
                mode = results[curve_name]['mode']
                insert_index = 3
                swap_data.insert(insert_index, calendar_cal)
                swap_curve = wrapper.McpVanillaSwapCurveData(mode, *swap_data)
                mCalibrationSet.addData(swap_curve.getHandler())
            mCalibrationSet.addEnd()
            arg = {
                "SettlementDate": results[curve_name]['SettlementDate'],
                "CalibrationSet": mCalibrationSet,
                "InterpolatedVariable": results[curve_name]['InterpolatedVariable'],
                "InterpolationMethod": results[curve_name]['InterpolationMethod'],
                "DayCounter": results[curve_name]['DayCounter']
            }
            print(arg)
            frb = McpBondCurve(arg)
            all_cache[keys] = frb
            object_data_cache[frb] = deep_copied_list[curve_name]
            return frb
        elif 'BillCurveData' in results[curve_name] and 'SwapCurveData' in results[curve_name]:
            bill_data = results[curve_name]['BillCurveData']
            swap_data = results[curve_name]['SwapCurveData']
            mode = results[curve_name]['mode']
            insert_index = 3
            swap_data.insert(insert_index, calendar_cal)
            bill_curve = MBillCurveData(*bill_data)
            swap_curve = wrapper.McpVanillaSwapCurveData(mode, *swap_data)
            mCalibrationSet = wrapper.McpCalibrationSet()
            mCalibrationSet.addData(bill_curve.getHandler())
            mCalibrationSet.addData(swap_curve.getHandler())
            mCalibrationSet.addEnd()
            arg = {
                "SettlementDate": results[curve_name]['SettlementDate'],
                "CalibrationSet": mCalibrationSet,
                "InterpolatedVariable": results[curve_name]['InterpolatedVariable'],
                "InterpolationMethod": results[curve_name]['InterpolationMethod'],
                "DayCounter": results[curve_name]['DayCounter'],
                "UseGlobalSolver": results[curve_name]['UseGlobalSolver'],
                "PillarEndDate": results[curve_name]['PillarEndDate']
            }
            frb = McpSwapCurve(arg)
            all_cache[keys] = frb
            object_data_cache[frb] = deep_copied_list[curve_name]
            return frb
        elif 'Buses' in results[curve_name]:
            args = results[curve_name]
            frb = McpSwapCurve(args)
            all_cache[keys] = frb
            object_data_cache[frb] = deep_copied_list[curve_name]
            return frb
        else:
            args = results[curve_name]
            frb = McpYieldCurve(args)
            all_cache[keys] = frb
            object_data_cache[frb] = deep_copied_list[curve_name]
            return frb

def McpVolSurface2ByName(identifiers, flag=False):
    ids = identifiers.split(",")
    if flag:
        class_name = 'VolSurface2_Future'
    else:
        class_name = 'VolSurface2_BTC'
    global all_cache
    for i in ids:
        keys = f"{class_name}_{i}"
        if keys in all_cache:
            return all_cache[keys]

    global node
    if node is None:
        node = create_McpNode()

    results = McpObject.batch_get_vol_data(node, class_name, ids)
    deep_copied_list = copy.deepcopy(results)
    for curve_name in ids:
        keys = f"{class_name}_{id}"
        currency = results[curve_name]['YieldCurve2']['Symbol']
        calendar_cal = McpCalendar(currency)


        fc_args = results[curve_name]['ForwardCurve2']
        yc_args = results[curve_name]['YieldCurve2']
        vs_args = results[curve_name]['VolSurface2']

        yc_args['Calendar'] = calendar_cal

        fc = McpForwardCurve2(fc_args)
        yc = McpYieldCurve2(yc_args)

        vs_args['YieldCurve2'] = yc
        vs_args['RiskFreeRateCurve2'] = fc
        vs_args['Calendar'] = calendar_cal

        vsf = McpVolSurface2(vs_args)
        all_cache[keys] = vsf
        object_data_cache[vsf] = deep_copied_list[curve_name]
        return vsf
def McpVolSurface2Equity(identifiers):
    ids = identifiers.split(",")
    class_name = 'VolSurface2_Equity'
    global all_cache
    for i in ids:
        keys = f"{class_name}_{i}"
        if keys in all_cache:
            return all_cache[keys]

    global node
    if node is None:
        node = create_McpNode()

    results = McpObject.batch_get_vol_data(node, class_name, ids)
    deep_copied_list = copy.deepcopy(results)
    for curve_name in ids:
        keys = f"{class_name}_{id}"
        currency = results[curve_name]['RiskFreeRateCurve2']['Symbol']
        calendar_cal = McpCalendar(currency)

        yc_args = results[curve_name]['RiskFreeRateCurve2']
        vs_args = results[curve_name]['VolSurface2']

        yc_args['Calendar'] = calendar_cal

        yc = McpYieldCurve2(yc_args)

        vs_args['RiskFreeRateCurve2'] = yc
        vs_args['Calendar'] = calendar_cal

        vsf = McpVolSurface2(vs_args)
        all_cache[keys] = vsf
        object_data_cache[vsf] = deep_copied_list[curve_name]
        return vsf

def McpVolSurfaceByName(identifiers, flag=False):
    ids = identifiers.split(",")
    if flag:
        class_name = 'VolSurface_Future'
    else:
        class_name = 'VolSurface_BTC'
    global all_cache
    for i in ids:
        keys = f"{class_name}_{i}"
        if keys in all_cache:
            return all_cache[keys]

    global node
    if node is None:
        node = create_McpNode()

    results = McpObject.batch_get_vol_data(node, class_name, ids)
    deep_copied_list = copy.deepcopy(results)
    for curve_name in ids:
        keys = f"{class_name}_{id}"
        currency = results[curve_name]['YieldCurve']['Symbol']
        calendar_cal = McpCalendar(currency)


        fc_args = results[curve_name]['ForwardCurve']
        yc_args = results[curve_name]['YieldCurve']
        vs_args = results[curve_name]['VolSurface']

        yc_args['Calendar'] = calendar_cal

        fc = McpForwardCurve(fc_args)
        yc = McpYieldCurve(yc_args)

        vs_args['RiskFreeRateCurve'] = yc
        vs_args['ForwardCurve'] = fc
        vs_args['Calendar'] = calendar_cal

        vsf = McpVolSurface(vs_args)
        all_cache[keys] = vsf
        object_data_cache[vsf] = deep_copied_list[curve_name]
        return vsf

def McpFXVolSurfaceByName(identifiers):
    ids = identifiers.split(",")
    class_name = 'McpFXVolSurfaceByName'
    global all_cache
    for i in ids:
        keys = f"{class_name}_{i}"
        if keys in all_cache:
            return all_cache[keys]

    global node
    if node is None:
        node = create_McpNode()

    results = McpObject.batch_get_vol_data(node, class_name, ids)
    deep_copied_list = copy.deepcopy(results)
    for curve_name in ids:
        keys = f"{class_name}_{id}"

        yc_args = results[curve_name]['ForeignCurve']
        currency =yc_args['Calendar']['currency']
        holidays = yc_args['Calendar']['holidays']
        calendar_cal = McpCalendar(currency, holidays)
        yc_args['Calendar'] = calendar_cal


        yc2_args = results[curve_name]['DomesticCurve']
        currency =yc2_args['Calendar']['currency']
        holidays = yc2_args['Calendar']['holidays']
        calendar_cal = McpCalendar(currency, holidays)
        yc2_args['Calendar'] = calendar_cal

        fc_args = results[curve_name]['FxForwardPointsCurve']
        currency = fc_args['Calendar']['currency']
        holidays = fc_args['Calendar']['holidays']
        calendar_cal = McpCalendar(currency, holidays)
        fc_args['Calendar'] = calendar_cal


        vs_args = results[curve_name]['FXVolSurface']
        currency =vs_args['Calendar']['currency']
        holidays = vs_args['Calendar']['holidays']
        calendar_cal = McpCalendar(currency, holidays)
        vs_args['Calendar'] = calendar_cal

        yc = McpYieldCurve(yc_args)
        yc2 = McpYieldCurve(yc2_args)
        fc = McpFXForwardPointsCurve(fc_args)

        vs_args['ForeignCurve'] = yc
        vs_args['DomesticCurve'] = yc2
        vs_args['FxForwardPointsCurve'] = fc

        vsf = McpFXVolSurface(vs_args)
        all_cache[keys] = vsf
        object_data_cache[vsf] = deep_copied_list[curve_name]
        return vsf

def McpFXVolSurface2ByName(identifiers):
    ids = identifiers.split(",")
    class_name = 'McpFXVolSurface2ByName'
    global all_cache
    for i in ids:
        keys = f"{class_name}_{i}"
        if keys in all_cache:
            return all_cache[keys]

    global node
    if node is None:
        node = create_McpNode()

    results = McpObject.batch_get_vol_data(node, class_name, ids)
    deep_copied_list = copy.deepcopy(results)
    for curve_name in ids:
        keys = f"{class_name}_{id}"

        yc_args = results[curve_name]['ForeignCurve2']
        currency = yc_args['Calendar']['currency']
        holidays = yc_args['Calendar']['holidays']
        calendar_cal = McpCalendar(currency, holidays)
        yc_args['Calendar'] = calendar_cal

        yc2_args = results[curve_name]['DomesticCurve2']
        currency = yc2_args['Calendar']['currency']
        holidays = yc2_args['Calendar']['holidays']
        calendar_cal = McpCalendar(currency, holidays)
        yc2_args['Calendar'] = calendar_cal

        fc_args = results[curve_name]['FxForwardPointsCurve2']
        currency = fc_args['Calendar']['currency']
        holidays = fc_args['Calendar']['holidays']
        calendar_cal = McpCalendar(currency, holidays)
        fc_args['Calendar'] = calendar_cal

        vs_args = results[curve_name]['FXVolSurface2']
        currency = vs_args['Calendar']['currency']
        holidays = vs_args['Calendar']['holidays']
        calendar_cal = McpCalendar(currency, holidays)
        vs_args['Calendar'] = calendar_cal

        yc = McpYieldCurve2(yc_args)
        yc2 = McpYieldCurve2(yc2_args)
        fc = McpFXForwardPointsCurve2(fc_args)

        vs_args["BidVolatilities"] = convert_to_float_array_np(vs_args["BidVolatilities"])
        vs_args["AskVolatilities"] = convert_to_float_array_np(vs_args["AskVolatilities"])

        vs_args['ForeignCurve2'] = yc
        vs_args['DomesticCurve2'] = yc2
        vs_args['FxForwardPointsCurve2'] = fc


        vsf = McpFXVolSurface2(vs_args)
        all_cache[keys] = vsf
        object_data_cache[vsf] = deep_copied_list[curve_name]
        return vsf

def McpSwapCurvesData(mcpSwapCurve, flag=False):
    obj = object_data_cache[mcpSwapCurve]
    # ordered_dict = sort_dict_by_order(obj, swap_curve_field)
    result = decode(obj, flag)
    result = [node for node in result if not (node[0] == 'SwaptionCube')]
    return result

def McpGetValue(identifier, key):
    """批量获取风险指标"""

    class_name = "FixedRateBond" if ".IB" in identifier or ".SH" in identifier else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_data(node, class_name, [identifier])
    # 动态获取所有可能的字段名
    fields = set()
    for id_data in results.values():
        fields.update(id_data.keys())
    for field in fields:
        if key == field:
            return results[identifier].get(field)

def McpBatchGetRowData(identifiers, class_name='', flag=False):
    """批量获取风险指标"""
    ids = identifiers.split(",")
    if class_name == '' or class_name is None:
        class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_data(node, class_name, ids)
    return get_result(ids, results, flag)


def check_list_type(lst):
    if isinstance(lst, list):
        if all(isinstance(item, list) for item in lst):  # 二维数组
            return True
        else:  # 一维数组
            return False
    else:
        return False

def decode2(obj, flag=False):
    result = []
    isList = False
    if isinstance(obj, list):
        for l1 in obj:
            result.append(l1)
        if not check_list_type(result):
            result = [result]
        isList = True

    if isinstance(obj, dict):
        fixed_order = list(obj.keys())
        for field in fixed_order:
            if field in obj:
                row = [field]
                value = obj.get(field)
                if "DayCounter".lower() == field.lower():
                    # 创建反向映射字典
                    enum_map = {v: k for k, v in DayCounter.__dict__.items() if not k.startswith('__')}
                    value = enum_map.get(value, value)
                elif "Frequency".lower() == field.lower():
                    enum_map = {v: k for k, v in Frequency.__dict__.items() if not k.startswith('__')}
                    value = enum_map.get(value, value)
                elif "BuySell".lower() == field.lower():
                    enum_map = {v: k for k, v in BuySell.__dict__.items() if not k.startswith('__')}
                    value = enum_map.get(value, value)
                elif "Side".lower() == field.lower():
                    enum_map = {v: k for k, v in Side.__dict__.items() if not k.startswith('__')}
                    value = enum_map.get(value, value)
                elif "CallPut".lower() == field.lower():
                    enum_map = {v: k for k, v in CallPut.__dict__.items() if not k.startswith('__')}
                    value = enum_map.get(value, value)
                elif "CalculateTarget".lower() == field.lower():
                    enum_map = {v: k for k, v in CalculateTarget.__dict__.items() if not k.startswith('__')}
                    value = enum_map.get(value, value)
                elif "InterpolationMethod".lower() == field.lower():
                    enum_map = {v: k for k, v in InterpolationMethod.__dict__.items() if not k.startswith('__')}
                    value = enum_map.get(value, value)
                elif "Model".lower() == field.lower():
                    enum_map = {v: k for k, v in HistVolsModel.__dict__.items() if not k.startswith('__')}
                    value = enum_map.get(value, value)
                elif "ReturnMethod".lower() == field.lower():
                    enum_map = {v: k for k, v in HistVolsReturnMethod.__dict__.items() if not k.startswith('__')}
                    value = enum_map.get(value, value)
                elif "Method".lower() == field.lower():
                    enum_map = {v: k for k, v in InterpolationMethod.__dict__.items() if not k.startswith('__')}
                    value = enum_map.get(value, value)
                elif "Variable".lower() == field.lower():
                    enum_map = {v: k for k, v in InterpolationVariable.__dict__.items() if not k.startswith('__')}
                    value = enum_map.get(value, value)
                elif "InterpolationVariable".lower() == field.lower():
                    enum_map = {v: k for k, v in InterpolationVariable.__dict__.items() if not k.startswith('__')}
                    value = enum_map.get(value, value)
                elif "InterpolatedVariable".lower() == field.lower():
                    enum_map = {v: k for k, v in InterpolatedVariable.__dict__.items() if not k.startswith('__')}
                    value = enum_map.get(value, value)
                if isinstance(value, float) and math.isnan(value):
                    row.append("#N/A")
                else:
                    row.append(value)
                result.append(row)

    # 检查 result 是否为空
    if result:
        max_length = max(len(sublist) for sublist in result)
        padded_data = [sublist + [''] * (max_length - len(sublist)) for sublist in result]
        result = np.array(padded_data, dtype=object)
    else:
        result = np.array([], dtype=object)

    if len(result) > 1:
        # 分离集合数据和非集合数据
        non_collection_items = []
        collection_items = []

        for item in result:
            key, value = item
            if isinstance(value, list):  # 检查值是否是列表类型
                collection_items.append(item)
            else:
                non_collection_items.append(item)

        # 合并结果：非集合数据在前，集合数据在后
        result = non_collection_items + collection_items

    if not isList:
        if flag:
            # 将二维列表转换为 numpy 数组
            original_array = np.array(result, dtype=object)
            # 进行转置操作
            transposed_array = original_array.T
            # 将转置后的 numpy 数组转换为二维列表
            transposed_list = transposed_array.tolist()
            # print(f'result2:{transposed_list}')
            return transposed_list
        else:
            return result
    else:
        if flag:
            return result
        else:
            # 将二维列表转换为 numpy 数组
            original_array = np.array(result, dtype=object)
            # 进行转置操作
            transposed_array = original_array.T
            # 将转置后的 numpy 数组转换为二维列表
            transposed_list = transposed_array.tolist()
            # print(f'result1:{transposed_list}')
            return transposed_list
from typing import Union


def is_int(value):
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False


def decode(obj: Union[List, Dict], flag: bool = False) -> np.ndarray:
    """
    将输入对象解码为二维数组，支持输出到 Excel。

    Args:
        obj: 输入数据（字典或列表）
        flag: 是否转置输出

    Returns:
        np.ndarray: 二维数组，可直接写入 Excel
    """
    result = []
    isList = isinstance(obj, list)

    # 处理列表输入
    if isList:
        # 确保每个元素都是列表（单元素变成 [element]）
        result = [[item] if not isinstance(item, (list, tuple)) else list(item) for item in obj]

    # 处理字典输入
    elif isinstance(obj, dict):
        for field in obj:
            value = obj[field]

            if "DayCounter".lower() == field.lower():
                # 创建反向映射字典
                enum_map = {v: k for k, v in DayCounter.__dict__.items() if not k.startswith('__')}
                value = enum_map.get(value, value)
            elif "Frequency".lower() == field.lower():
                if is_int(value):
                    value = int(value)
                enum_map = {v: k for k, v in Frequency.__dict__.items() if not k.startswith('__')}
                value = enum_map.get(value, value)
            elif "BuySell".lower() == field.lower():
                enum_map = {v: k for k, v in BuySell.__dict__.items() if not k.startswith('__')}
                value = enum_map.get(value, value)
            elif "Side".lower() == field.lower():
                enum_map = {v: k for k, v in Side.__dict__.items() if not k.startswith('__')}
                value = enum_map.get(value, value)
            elif "CallPut".lower() == field.lower():
                enum_map = {v: k for k, v in CallPut.__dict__.items() if not k.startswith('__')}
                value = enum_map.get(value, value)
            elif "CalculateTarget".lower() == field.lower():
                enum_map = {v: k for k, v in CalculateTarget.__dict__.items() if not k.startswith('__')}
                value = enum_map.get(value, value)
            elif "InterpolationMethod".lower() == field.lower():
                enum_map = {v: k for k, v in InterpolationMethod.__dict__.items() if not k.startswith('__')}
                value = enum_map.get(value, value)
            elif "Model".lower() == field.lower():
                enum_map = {v: k for k, v in HistVolsModel.__dict__.items() if not k.startswith('__')}
                value = enum_map.get(value, value)
            elif "ReturnMethod".lower() == field.lower():
                enum_map = {v: k for k, v in HistVolsReturnMethod.__dict__.items() if not k.startswith('__')}
                value = enum_map.get(value, value)
            elif "Method".lower() == field.lower():
                enum_map = {v: k for k, v in InterpolationMethod.__dict__.items() if not k.startswith('__')}
                value = enum_map.get(value, value)
            elif "Variable".lower() == field.lower():
                enum_map = {v: k for k, v in InterpolatedVariable.__dict__.items() if not k.startswith('__')}
                value = enum_map.get(value, value)
            elif "InterpolatedVariable".lower() == field.lower():
                enum_map = {v: k for k, v in InterpolatedVariable.__dict__.items() if not k.startswith('__')}
                value = enum_map.get(value, value)
            elif "InterpolationVariable".lower() == field.lower():
                enum_map = {v: k for k, v in InterpolationVariable.__dict__.items() if not k.startswith('__')}
                value = enum_map.get(value, value)
            elif "IROptionQuotation".lower() == field.lower():
                enum_map = {v: k for k, v in IROptionQuotation.__dict__.items() if not k.startswith('__')}
                value = enum_map.get(value, value)
            elif "CapVolPaymentType".lower() == field.lower():
                enum_map = {v: k for k, v in CapVolPaymentType.__dict__.items() if not k.startswith('__')}
                value = enum_map.get(value, value)
            elif "StrippingMethod".lower() == field.lower():
                enum_map = {v: k for k, v in StrippingMethod.__dict__.items() if not k.startswith('__')}
                value = enum_map.get(value, value)
            elif "BillCurveData".lower() == field.lower():
                data_list = []
                for idx,item in enumerate(value):
                    if idx == 1:
                        item = "Act365Fixed"
                    data_list.append(item)
                value = data_list
            elif "SwapCurveData".lower() == field.lower():
                data_list = []
                for idx, item in enumerate(value):
                    if idx == 1:
                        enum_map = {v: k for k, v in DayCounter.__dict__.items() if not k.startswith('__')}
                        item = enum_map.get(item, value)
                    if idx == 3:
                        enum_map = {v: k for k, v in DateAdjusterRule.__dict__.items() if not k.startswith('__')}
                        item = enum_map.get(item, value)
                    if idx == 4:
                        enum_map = {v: k for k, v in DateAdjusterRule.__dict__.items() if not k.startswith('__')}
                        item = enum_map.get(item, value)
                    if idx == 6:
                        enum_map = {v: k for k, v in Frequency.__dict__.items() if not k.startswith('__')}
                        item = enum_map.get(item, value)
                    if idx == 7:
                        enum_map = {v: k for k, v in Frequency.__dict__.items() if not k.startswith('__')}
                        item = enum_map.get(item, value)
                    if idx == 8:
                        enum_map = {v: k for k, v in DayCounter.__dict__.items() if not k.startswith('__')}
                        item = enum_map.get(item, value)
                    if idx == 9:
                        enum_map = {v: k for k, v in DayCounter.__dict__.items() if not k.startswith('__')}
                        item = enum_map.get(item, value)
                    if idx == 12:
                        enum_map = {v: k for k, v in ResetRateMethod.__dict__.items() if not k.startswith('__')}
                        item = enum_map.get(item, value)
                    data_list.append(item)
                value = data_list
            # 处理 NaN 值
            if isinstance(value, float) and math.isnan(value):
                value = "#N/A"

            result.append([field, value])

    # 转换为等长的二维数组
    if not result:
        return np.array([], dtype=object)

    # 计算最大列数并填充空缺
    max_len = max(len(row) for row in result)
    padded_result = [row + [''] * (max_len - len(row)) for row in result]

    # 转换为 NumPy 数组
    np_result = np.array(padded_result, dtype=object)

    # 分离集合数据和非集合数据（如果仍有需要）
    if len(np_result) > 1:
        non_collection = []
        collection = []
        for row in np_result:
            if len(row) >= 2 and isinstance(row[1], (list, np.ndarray)):
                collection.append(row)
            else:
                non_collection.append(row)
        np_result = np.vstack(non_collection + collection) if non_collection or collection else np_result

    # 转置控制
    if flag:
        return np_result.T
    return np_result

def McpZSpread(identifiers, curve_name, yield_value=''):
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, [f'FrbZSpread|{curve_name},{yield_value}'])
    metrics1 = ['FrbZSpread']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics1] for id in ids]

def McpGet1(identifiers, key):
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    if class_name == "FixedRateBond" and key.lower() == "lastest":
        results = McpObject.batch_get_risk_metrics(node, class_name, ids, [f'BondMarketValue|{ids[0]}'])
        metrics1 = ['BondMarketValue']
        return [[results.get(id, {}).get(m, "#N/A") for m in metrics1] for id in ids]
    elif class_name == "VanillaSwap" and key.lower() == "coupon":
        results = McpObject.batch_get_risk_metrics(node, class_name, ids, [f'VanillaSwapCoupon|{ids[0]}'])
        metrics1 = ['VanillaSwapCoupon']
        return [[results.get(id, {}).get(m, "#N/A") for m in metrics1] for id in ids]
    else:
        return f'not found this key'

def McpGSpread(identifiers, curve_name, yield_value=''):
    ids = identifiers.split(",")

    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, [f'FrbGSpread|{curve_name},{yield_value}'])
    metrics1 = ['FrbGSpread']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics1] for id in ids]

def McpCleanPriceFromYield(identifiers, yield_value=''):
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, [f'FrbCleanPriceFromYield|{yield_value}'])
    metrics = ['FrbCleanPriceFromYield']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpDirtyPriceFromYield(identifiers, yield_value=''):
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, [f'FrbDirtyPriceFromYield|{yield_value}'])
    metrics = ['FrbDirtyPriceFromYield']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpDurationCHN(identifiers, yield_value=''):
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, [f'FrbDurationCHN|{yield_value}'])
    metrics = ['FrbDurationCHN']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpMDurationCHN(identifiers, yield_value=''):
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, [f'FrbMDurationCHN|{yield_value}'])
    metrics = ['FrbMDurationCHN']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpConvexityCHN(identifiers, yield_value=''):
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, [f'FrbConvexityCHN|{yield_value}'])
    metrics = ['FrbConvexityCHN']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFrbPrice(identifiers, curve_name):
    """
    计算指定标识符的 Price 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 Price 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, [f'FrbPrice|{curve_name}'])
    metrics = ['FrbPrice']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpPVBPCHN(identifiers, yield_value=''):
    """
    计算指定标识符的 FrbPVBPCHN 值，支持额外参数。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。
        param (str): 额外参数。

    返回:
        List[List[Any]]: 包含 FrbPVBPCHN 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, [f'FrbPVBPCHN|{yield_value}'])
    metrics = ['FrbPVBPCHN']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpYieldFromDirtyPrice(identifiers, dirty_price=''):
    """
    计算指定标识符的 FrbYieldFromDirtyPrice 值，支持额外参数。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。
        param (str): 额外参数。

    返回:
        List[List[Any]]: 包含 FrbYieldFromDirtyPrice 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, [f'FrbYieldFromDirtyPrice|{dirty_price}'])
    metrics = ['FrbYieldFromDirtyPrice']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFairValue(identifiers, curve_name):
    """
    计算指定标识符的 FrbFairValue 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FrbFairValue 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, [f'FrbFairValue|{curve_name}'])
    metrics = ['FrbFairValue']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFixedLegNPV(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 FixedLegNPV 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FixedLegNPV 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['FixedLegNPV'])
    metrics = ['FixedLegNPV']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFloatingLegNPV(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 FloatingLegNPV 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FloatingLegNPV 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['FloatingLegNPV'])
    metrics = ['FloatingLegNPV']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFixedLegDuration(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 FixedLegDuration 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FixedLegDuration 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['FixedLegDuration'])
    metrics = ['FixedLegDuration']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFloatingLegDuration(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 FloatingLegDuration 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FloatingLegDuration 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['FloatingLegDuration'])
    metrics = ['FloatingLegDuration']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFixedLegMDuration(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 FixedLegMDuration 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FixedLegMDuration 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['FixedLegMDuration'])
    metrics = ['FixedLegMDuration']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFloatingLegMDuration(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 FloatingLegMDuration 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FloatingLegMDuration 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['FloatingLegMDuration'])
    metrics = ['FloatingLegMDuration']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFixedLegAnnuity(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 FixedLegAnnuity 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FixedLegAnnuity 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['FixedLegAnnuity'])
    metrics = ['FixedLegAnnuity']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFloatingLegAnnuity(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 FloatingLegAnnuity 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FloatingLegAnnuity 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['FloatingLegAnnuity'])
    metrics = ['FloatingLegAnnuity']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFixedLegDV01(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 FixedLegDV01 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FixedLegDV01 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['FixedLegDV01'])
    metrics = ['FixedLegDV01']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFloatingLegDV01(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 FloatingLegDV01 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FloatingLegDV01 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['FloatingLegDV01'])
    metrics = ['FloatingLegDV01']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFixedLegAccrued(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 FixedLegAccrued 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FixedLegAccrued 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['FixedLegAccrued'])
    metrics = ['FixedLegAccrued']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFloatingLegAccrued(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 FloatingLegAccrued 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FloatingLegAccrued 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['FloatingLegAccrued'])
    metrics = ['FloatingLegAccrued']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFixedLegPremium(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 FixedLegPremium 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FixedLegPremium 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['FixedLegPremium'])
    metrics = ['FixedLegPremium']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFloatingLegPremium(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 FloatingLegPremium 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FloatingLegPremium 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['FloatingLegPremium'])
    metrics = ['FloatingLegPremium']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFixedLegMarketValue(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 FixedLegMarketValue 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FixedLegMarketValue 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['FixedLegMarketValue'])
    metrics = ['FixedLegMarketValue']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFloatingLegMarketValue(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 FloatingLegMarketValue 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FloatingLegMarketValue 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['FloatingLegMarketValue'])
    metrics = ['FloatingLegMarketValue']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFixedLegCumPV(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 FixedLegCumPV 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FixedLegCumPV 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['FixedLegCumPV'])
    metrics = ['FixedLegCumPV']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFloatingLegCumPV(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 FloatingLegCumPV 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FloatingLegCumPV 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['FloatingLegCumPV'])
    metrics = ['FloatingLegCumPV']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFixedLegCumCF(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 FixedLegCumCF 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FixedLegCumCF 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['FixedLegCumCF'])
    metrics = ['FixedLegCumCF']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFloatingLegCumCF(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 FloatingLegCumCF 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 FloatingLegCumCF 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['FloatingLegCumCF'])
    metrics = ['FloatingLegCumCF']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpNPV(identifiers, enddate=None, swaprate=None, point=None):
    """
    计算指定标识符的 NPV 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 NPV 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    if swaprate and enddate:
        s = f'NPV|{swaprate},{enddate},{point}'
    else:
        s = 'NPV'
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, [s])
    metrics = ['NPV']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpMarketParRate(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 MarketParRate 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 MarketParRate 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['MarketParRate'])
    metrics = ['MarketParRate']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpDuration(identifiers, enddate=None, swaprate=None, point=None):
    # @xl_func("str identifiers: var[][]")
    # def McpDuration(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 Duration 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 Duration 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    if swaprate and enddate:
        s = f'Duration|{swaprate},{enddate},{point}'
    else:
        s = 'Duration'
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, [s])
    metrics = ['Duration']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpMDuration(identifiers, enddate=None, swaprate=None, point=None):
    # @xl_func("str identifiers: var[][]")
    # def McpMDuration(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 MDuration 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 MDuration 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    if swaprate and enddate:
        s = f'MDuration|{swaprate},{enddate},{point}'
    else:
        s = 'MDuration'
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, [s])
    metrics = ['MDuration']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpPV01(identifiers, enddate=None, swaprate=None, point=None):
    """
    计算指定标识符的 PV01 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 PV01 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    if swaprate and enddate:
        s = f'PV01|{swaprate},{enddate},{point}'
    else:
        s = 'PV01'
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, [s])
    metrics = ['PV01']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpDV01(identifiers, enddate=None, swaprate=None, point=None):
    """
    计算指定标识符的 DV01 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 DV01 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    if swaprate and enddate:
        s = f'DV01|{swaprate},{enddate},{point}'
    else:
        s = 'DV01'
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, [s])
    metrics = ['DV01']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpCF(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 CF 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 CF 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['CF'])
    metrics = ['CF']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpValuationDayCF(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 ValuationDayCF 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 ValuationDayCF 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['ValuationDayCF'])
    metrics = ['ValuationDayCF']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]


def McpMarketValues(identifiers, enddate=None, swaprate=None, point=None):
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    if swaprate and enddate:
        s = f'MarketValue|{swaprate},{enddate},{point}'
    else:
        s = 'MarketValue'
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, [s])
    metrics = ['MarketValue']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpMarketValue(identifiers_or_obj: Union[str, object], isAmount: bool = True) -> Union[List[List[Any]], float]:
    """
    计算指定标识符或对象的 MarketValue 值。

    参数:
        identifiers_or_obj (str or object): 输入的标识符字符串（多个标识符用逗号分隔）或对象。
        isAmount (bool): 是否返回金额形式，默认 True。

    返回:
        List[List[Any]] 或 float: 如果输入是字符串，返回包含 MarketValue 的二维列表；如果输入是对象，返回 MarketValue 值。
    """
    if isinstance(identifiers_or_obj, str):
        # 第一种用法：处理字符串标识符
        ids = identifiers_or_obj.split(",")
        class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
        global node
        if node is None:
            node = create_McpNode()
        results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['MarketValue'])
        metrics = ['MarketValue']
        return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]
    else:
        # 第二种用法：处理对象
        return identifiers_or_obj.MarketValue(isAmount)

def McpAccrued(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 Accrued 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 Accrued 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['Accrued'])
    metrics = ['Accrued']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]


def McpPNLs(identifiers: str) -> List[List[Any]]:
    """
    计算指定标识符的 PNL 值。

    参数:
        identifiers (str): 输入的标识符字符串，多个标识符用逗号分隔。

    返回:
        List[List[Any]]: 包含 PNL 值的二维列表。
    """
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, ['PNL'])
    metrics = ['PNL']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpCalculateSwapRateFromNPV(identifiers, npv=''):
    ids = identifiers.split(",")
    class_name = "FixedRateBond" if ".IB" in ids[0] or ".SH" in ids[0] else "VanillaSwap"
    global node
    if node is None:
        node = create_McpNode()
    results = McpObject.batch_get_risk_metrics(node, class_name, ids, [f'CalculateSwapRateFromNPV|{npv}'])
    metrics = ['CalculateSwapRateFromNPV']
    return [[results.get(id, {}).get(m, "#N/A") for m in metrics] for id in ids]

def McpFIPortDurations(bondlist, amountlist, yieldlist):
    result = 0
    total_sum = 0
    total_amount = 0
    class_name = "FixedRateBond"
    for bond_id, amount, yld in zip(bondlist, amountlist, yieldlist):
        global node
        if node is None:
            node = create_McpNode()
        results = McpObject.batch_get_risk_metrics(node, class_name, [bond_id], [f'FrbDurationCHN|{yld}'])
        total_sum = total_sum + float(results[bond_id]['FrbDurationCHN']) * amount
        total_amount = total_amount + amount
    result = total_sum / total_amount
    return result

def McpFIPortKRDs(bondlist, amountlist, tenors, curvename):
    result = []
    sum = None
    total_sum = 0
    total_amount = 0
    aggregated_krd = {}
    class_name = "FixedRateBond"

    # a=[]
    # for bond_id, amount in zip(bondlist, amountlist):
    #
    #     a1=f'KeyRateDuration|{curvename},{tn}'
    #     a.append(a1)
    global node
    if node is None:
        node = create_McpNode()
    tn = ','.join(tenors)
    results = McpObject.batch_get_risk_metrics(node, class_name, bondlist, [f'KeyRateDuration|{curvename},{tn}'])
    for bond_id, amount in zip(bondlist, amountlist):
        total_amount = total_amount + amount
        i = 0
        for krd_value in results[bond_id]['KeyRateDuration']:
            if i not in aggregated_krd:
                aggregated_krd[i] = 0
            aggregated_krd[i] += krd_value * amount
            i = i + 1
    weighted_average_krd = [value / total_amount for timepoint, value in aggregated_krd.items()]
    result.append(weighted_average_krd)
    return result
    # print(f'KeyRateDuration result:{results}')
    # for bond_id, amount in zip(bondlist, amountlist):
    #     global node
    #     if node is None:
    #         node = create_McpNode()
    #     tn = ','.join(tenors)
    #     print(f'KeyRateDuration|{curvename},{tn}')
    #
    #     results = McpObject.batch_get_risk_metrics(node, class_name, [bond_id], [f'KeyRateDuration|{curvename},{tn}'])
    #     print(f'KeyRateDuration result:{results}')
    #     total_amount = total_amount + amount
    #     i = 0
    #     for krd_value in results[bond_id]['KeyRateDuration']:
    #         if i not in aggregated_krd:
    #             aggregated_krd[i] = 0
    #         aggregated_krd[i] += krd_value * amount
    #         i = i + 1
    # weighted_average_krd = [value / total_amount for timepoint, value in aggregated_krd.items()]
    # result.append(weighted_average_krd)
    # return result

def MCPGet(assetid, field):
    cur_path = os.path.realpath(__file__)
    print(cur_path)
    parent_dir = os.path.dirname(cur_path)
    print(parent_dir)
    file_path = os.path.join(parent_dir, "control", "IRS.xlsx")
    dfzz = pd.read_excel(file_path)

    if assetid.count('-') > 0 or assetid.startswith('T'):
        try:
            file_path = os.path.join(parent_dir, "control", "IRS.xlsx")
            # cur_path = str(cur_path) + "./control/IRS.xlsx"
            # df = pd.read_excel(cur_path)
            # global dfzz
            # if dfzz is None:
            dfzz = pd.read_excel(file_path)
        except:
            traceback.print_exc()
        if dfzz is None or dfzz.empty:
            raise Exception(f"Load irs error.")
        df2 = dfzz[dfzz['AssetID'] == assetid]
        if df2 is None or df2.empty:
            raise Exception(f"Unknown assetid {assetid}.")
        df2.set_index('AssetID', inplace=True)
        row_id_dic = df2.to_dict(orient='index')
        if field in row_id_dic[assetid]:
            return row_id_dic[assetid][field]
        else:
            raise Exception(f"Can't get field {field}")
    else:
        return file_path

def McpCapVolSurface(identifiers):
    ids = identifiers.split(",")
    class_name = 'VolSurface_CapVol'
    global all_cache
    for i in ids:
        keys = f"{class_name}_{i}"
        if keys in all_cache:
            return all_cache[keys]

    global node
    if node is None:
        node = create_McpNode()

    results = McpObject.batch_get_vol_data(node, class_name, ids)
    deep_copied_list = copy.deepcopy(results)
    for curve_name in ids:
        keys = f"{class_name}_{id}"
        currency = results[curve_name]['Calendar']['currency']
        holidays = results[curve_name]['Calendar']['holidays']
        calendar_cal = McpCalendar(currency,holidays)

        dis_args = results[curve_name]['DiscountingCurveConfig']
        es_args = results[curve_name]['EstimatingCurveConfig']
        cp_args = results[curve_name]['CapvolConfig']

        dis_args['Calendar'] = calendar_cal
        es_args['Calendar'] = calendar_cal

        if dis_args['SwapCurveEnable'] and dis_args['YieldCurveEnable']:
            args = dis_args['BillCurveData']
            bill_curve = MBillCurveData(*args)

            swap_args = dis_args['SwapCurveData']
            mode = dis_args['mode']
            insert_index = 3
            swap_args.insert(insert_index, calendar_cal)
            swap_curve = wrapper.McpVanillaSwapCurveData(mode, *swap_args)
            mCalibrationSet = wrapper.McpCalibrationSet()
            mCalibrationSet.addData(bill_curve.getHandler())
            mCalibrationSet.addData(swap_curve.getHandler())
            mCalibrationSet.addEnd()
            arg = {
                "SettlementDate": dis_args['SettlementDate'],
                "CalibrationSet": mCalibrationSet,
                "InterpolatedVariable": dis_args['InterpolatedVariable'],
                "InterpolationMethod": dis_args['InterpolationMethod'],
                "DayCounter": dis_args['DayCounter'],
                "UseGlobalSolver": dis_args['UseGlobalSolver'],
                "PillarEndDate": dis_args['PillarEndDate']
            }
            dis_curve = McpSwapCurve(arg)
        elif dis_args['BondCurveEnable'] and dis_args['YieldCurveEnable']:
            args = dis_args['BillCurveData']
            bill_curve = MBillCurveData(*args)

            bond_args = dis_args['BondCurveData']
            bond_curve = MFixedRateBondCurveData(*bond_args)

            mCalibrationSet = wrapper.McpCalibrationSet()
            mCalibrationSet.addData(bill_curve.getHandler())
            mCalibrationSet.addData(bond_curve.getHandler())
            if dis_args['SwapCurveEnable']:
                swap_args = dis_args['SwapCurveData']
                mode = dis_args['mode']
                insert_index = 3
                swap_args.insert(insert_index, calendar_cal)
                swap_curve = wrapper.McpVanillaSwapCurveData(mode, *swap_args)
                mCalibrationSet.addData(swap_curve.getHandler())
            mCalibrationSet.addEnd()
            arg = {
                "SettlementDate": dis_args['SettlementDate'],
                "CalibrationSet": mCalibrationSet,
                "InterpolatedVariable": InterpolatedVariable.CONTINUOUSRATES,
                "InterpolationMethod": InterpolationMethod.LINEARINTERPOLATION,
                "DayCounter": DayCounter.Act365Fixed
            }
            dis_curve = McpBondCurve(arg)
        elif dis_args['SwapCurveEnable']:
            swap_args = dis_args
            dis_curve = McpSwapCurve(swap_args)
        else:
            yield_args = dis_args
            dis_curve = McpYieldCurve(yield_args)

        if es_args['SwapCurveEnable'] and es_args['YieldCurveEnable']:
            args = es_args['BillCurveData']
            bill_curve = MBillCurveData(*args)

            swap_args = es_args['SwapCurveData']
            mode = es_args['mode']
            insert_index = 3
            swap_args.insert(insert_index, calendar_cal)
            swap_curve = wrapper.McpVanillaSwapCurveData(mode, *swap_args)
            mCalibrationSet = wrapper.McpCalibrationSet()
            mCalibrationSet.addData(bill_curve.getHandler())
            mCalibrationSet.addData(swap_curve.getHandler())
            mCalibrationSet.addEnd()
            arg = {
                "SettlementDate": es_args['SettlementDate'],
                "CalibrationSet": mCalibrationSet,
                "InterpolatedVariable": es_args['InterpolatedVariable'],
                "InterpolationMethod": es_args['InterpolationMethod'],
                "DayCounter": es_args['DayCounter'],
                "UseGlobalSolver": es_args['UseGlobalSolver'],
                "PillarEndDate": es_args['PillarEndDate']
            }
            es_curve = McpSwapCurve(arg)
        elif es_args['BondCurveEnable'] and es_args['YieldCurveEnable']:
            args = es_args['BillCurveData']
            bill_curve = MBillCurveData(*args)

            bond_args = es_args['BondCurveData']
            bond_curve = MFixedRateBondCurveData(*bond_args)

            mCalibrationSet = wrapper.McpCalibrationSet()
            mCalibrationSet.addData(bill_curve.getHandler())
            mCalibrationSet.addData(bond_curve.getHandler())
            if es_args['SwapCurveEnable']:
                swap_args = es_args['SwapCurveData']
                mode = es_args['mode']
                insert_index = 3
                swap_args.insert(insert_index, calendar_cal)
                swap_curve = wrapper.McpVanillaSwapCurveData(mode, *swap_args)
                mCalibrationSet.addData(swap_curve.getHandler())
            mCalibrationSet.addEnd()
            arg = {
                "SettlementDate": es_args['SettlementDate'],
                "CalibrationSet": mCalibrationSet,
                "InterpolatedVariable": InterpolatedVariable.CONTINUOUSRATES,
                "InterpolationMethod": InterpolationMethod.LINEARINTERPOLATION,
                "DayCounter": DayCounter.Act365Fixed
            }
            es_curve = McpBondCurve(arg)
        elif es_args['SwapCurveEnable']:
            swap_args = es_args
            es_curve = McpSwapCurve(swap_args)
        else:
            yield_args = es_args
            es_curve = McpYieldCurve(yield_args)
        cp_args['EstimatingCurve'] = es_curve
        cp_args['DiscountingCurve'] = dis_curve
        cp_args['Calendar'] = calendar_cal
        cpv = McpCapVolStripping(cp_args)
        all_cache[keys] = cpv
        object_data_cache[cpv] = deep_copied_list[curve_name]
        return cpv

def McpCapVolSurfaceData(mcpVolSurfaces, flag=False):
    obj = object_data_cache[mcpVolSurfaces]
    # ordered_dict = sort_dict_by_order(obj, swap_curve_field)
    return decode(obj, flag)

def McpSwaptionCubes(identifiers):
    ids = identifiers.split(",")
    print(f'McpSwaptionCubes:{identifiers}')
    class_name = 'VolSurface_SwaptionCube'
    global all_cache
    for i in ids:
        keys = f"{class_name}_{i}"
        if keys in all_cache:
            return all_cache[keys]

    global node
    if node is None:
        node = create_McpNode()
    print(f'McpSwaptionCubes node={node},class_name={class_name},ids={ids}')
    results = McpObject.get_swaptioncube_data(node, class_name, ids)
    deep_copied_list = copy.deepcopy(results)

    for curve_name in ids:
        keys = f"{class_name}_{id}"
        data = results[curve_name]
        currency = data['Calendar']['currency']
        holidays = data['Calendar']['holidays']
        calendar_cal = McpCalendar(currency, holidays)

        fixed_dis_args = data['FixedDiscountCurve']
        FixedDiscountCurve = gen_swap_obj(fixed_dis_args,calendar_cal)

        float_dis_args = data['FloatDiscountCurve']
        FloatDiscountCurve = gen_swap_obj(float_dis_args, calendar_cal)

        float_es_args = data['FloatEstimationCurve']
        FloatEstimationCurve = gen_swap_obj(float_es_args,calendar_cal)

        convention = McpRateConvention(data['Code'])
        s_cub_args = {
            'ReferenceDate': data['ReferenceDate'],
            'UsingSpread': data['UsingSpread'],
            'StrikeInterpType': data['StrikeInterpType'],
            'TenorInterpMethod': data['TenorInterpMethod'],
            'RateConvention': convention,
            'FixedDiscountCurve': FixedDiscountCurve,
            'FloatEstimationCurve': FloatEstimationCurve,
            'FloatDiscountCurve': FloatDiscountCurve,
            'Calendar': calendar_cal,
            'VolSpread': data['VolSpread'],
        }

        cube_market_data = {
            'StrikeOrSpreads': convert_to_float_array_np(data['StrikeOrSpreads']),
            'ExpiryTenorPillars': data['ExpiryTenorPillars'],
            'VolSpreadOrVols': convert_to_float_array_np(data['VolSpreadOrVols']),
            'AtmMaturityPillars': data['AtmMaturityPillars'],
            'AtmExpiryPillars': data['AtmExpiryPillars'],
            'AtmVols': convert_to_float_array_np(data['AtmVols'])
        }
        s_cub_args.update(cube_market_data)
        print(f's_cub_args: {s_cub_args}')
        s_cub_obj = McpSwaptionCube(s_cub_args)
        all_cache[keys] = s_cub_obj
        object_data_cache[s_cub_obj] = deep_copied_list[curve_name]
        return s_cub_obj

def McpSwaptionCubesData(mcpSwaptionCube, flag=False):
    obj = object_data_cache[mcpSwaptionCube]
    # ordered_dict = sort_dict_by_order(obj, swap_curve_field)
    return decode(obj, flag)

def McpFXForwardPointsCurves(identifiers,refdate=""):
    if not refdate:
        refdate = datetime.now().strftime("%Y/%m/%d")
    ids = identifiers.split(",")
    print(f'McpFXForwardPointsCurves:{identifiers}')
    class_name = 'FxForwardCurve'
    global all_cache
    for i in ids:
        keys = f"{class_name}_{i}"
        if keys in all_cache:
            return all_cache[keys]

    global node
    if node is None:
        node = create_McpNode()
    print(f'McpFXForwardPointsCurves node={node},class_name={class_name},ids={ids}')
    results = McpObject.get_fxforward_data(node, class_name, [identifiers], [refdate])
    deep_copied_list = copy.deepcopy(results)
    for curve_name in ids:
        keys = f"{class_name}_{id}"
        data = results[curve_name]
        currency = data['Calendar']['currency']
        holidays = data['Calendar']['holidays']
        calendar_cal = McpCalendar(currency, holidays)
        data['Calendar'] = calendar_cal

        print(f'fx_forward_points_curve: {data}')
        forward_points_obj = McpFXForwardPointsCurve(data)
        all_cache[keys] = forward_points_obj
        object_data_cache[forward_points_obj] = deep_copied_list[curve_name]
        return forward_points_obj

def McpFXForwardPointsCurvesData(mcpFXForwardPointsCurves, flag=False):
    obj = object_data_cache[mcpFXForwardPointsCurves]
    # ordered_dict = sort_dict_by_order(obj, swap_curve_field)
    return decode(obj, flag)

def McpFXForwardPointsCurves2(identifiers,refdate=""):
    if not refdate:
        refdate = datetime.now().strftime("%Y/%m/%d")
    ids = identifiers.split(",")
    print(f'McpFXForwardPointsCurves2:{identifiers}')
    class_name = 'FxForwardCurve2'
    global all_cache
    for i in ids:
        keys = f"{class_name}_{i}"
        if keys in all_cache:
            return all_cache[keys]

    global node
    if node is None:
        node = create_McpNode()
    print(f'McpFXForwardPointsCurves node={node},class_name={class_name},ids={ids}')
    results = McpObject.get_fxforward_data(node, class_name, [identifiers], [refdate])
    deep_copied_list = copy.deepcopy(results)
    for curve_name in ids:
        keys = f"{class_name}_{id}"
        data = results[curve_name]
        currency = data['Calendar']['currency']
        holidays = data['Calendar']['holidays']
        calendar_cal = McpCalendar(currency, holidays)
        data['Calendar'] = calendar_cal

        print(f'fx_forward_points_curve: {data}')
        forward_points_obj = McpFXForwardPointsCurve2(data)
        all_cache[keys] = forward_points_obj
        object_data_cache[forward_points_obj] = deep_copied_list[curve_name]
        return forward_points_obj

def McpFXForwardPointsCurves2Data(mcpFXForwardPointsCurves2, flag=False):
    obj = object_data_cache[mcpFXForwardPointsCurves2]
    # ordered_dict = sort_dict_by_order(obj, swap_curve_field)
    return decode(obj, flag)

def convert_to_float_array_np(data):
    # 创建NumPy数组，指定dtype=object以保留原始结构
    arr = np.array(data, dtype=object)

    # 定义转换函数
    def convert_element(x):
        if isinstance(x, str):
            if x == '':
                return np.nan
            try:
                return float(x)
            except ValueError:
                return np.nan
        elif isinstance(x, list):
            return convert_to_float_array_np(x)  # 递归处理嵌套列表
        return x

    # 应用转换（使用vectorize提高效率）
    vectorized_convert = np.vectorize(convert_element)
    return vectorized_convert(arr)

def gen_swap_obj(dis_args,calendar_cal):
    if dis_args['SwapCurveEnable'] and dis_args['YieldCurveEnable']:
        args = dis_args['BillCurveData']
        bill_curve = MBillCurveData(*args)

        swap_args = dis_args['SwapCurveData']
        mode = dis_args['mode']
        insert_index = 3
        swap_args.insert(insert_index, calendar_cal)
        swap_curve = wrapper.McpVanillaSwapCurveData(mode, *swap_args)
        mCalibrationSet = wrapper.McpCalibrationSet()
        mCalibrationSet.addData(bill_curve.getHandler())
        mCalibrationSet.addData(swap_curve.getHandler())
        mCalibrationSet.addEnd()
        arg = {
            "SettlementDate": dis_args['SettlementDate'],
            "CalibrationSet": mCalibrationSet,
            "InterpolatedVariable": dis_args['InterpolatedVariable'],
            "InterpolationMethod": dis_args['InterpolationMethod'],
            "DayCounter": dis_args['DayCounter'],
            "UseGlobalSolver": dis_args['UseGlobalSolver'],
            "PillarEndDate": dis_args['PillarEndDate']
        }
        dis_curve = McpSwapCurve(arg)
    elif dis_args['BondCurveEnable'] and dis_args['YieldCurveEnable']:
        args = dis_args['BillCurveData']
        bill_curve = MBillCurveData(*args)

        bond_args = dis_args['BondCurveData']
        bond_curve = MFixedRateBondCurveData(*bond_args)

        mCalibrationSet = wrapper.McpCalibrationSet()
        mCalibrationSet.addData(bill_curve.getHandler())
        mCalibrationSet.addData(bond_curve.getHandler())
        if dis_args['SwapCurveEnable']:
            swap_args = dis_args['SwapCurveData']
            mode = dis_args['mode']
            insert_index = 3
            swap_args.insert(insert_index, calendar_cal)
            swap_curve = wrapper.McpVanillaSwapCurveData(mode, *swap_args)
            mCalibrationSet.addData(swap_curve.getHandler())
        mCalibrationSet.addEnd()
        arg = {
            "SettlementDate": dis_args['SettlementDate'],
            "CalibrationSet": mCalibrationSet,
            "InterpolatedVariable": InterpolatedVariable.CONTINUOUSRATES,
            "InterpolationMethod": InterpolationMethod.LINEARINTERPOLATION,
            "DayCounter": DayCounter.Act365Fixed
        }
        dis_curve = McpBondCurve(arg)
    elif dis_args['SwapCurveEnable']:
        swap_args = dis_args
        dis_curve = McpSwapCurve(swap_args)
    else:
        yield_args = dis_args
        dis_curve = McpYieldCurve(yield_args)
    return dis_curve