import traceback
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json

from mcp.server_version import mcp_server

from pyxll import xl_func, xl_arg

# Configure server addresses
SERVER_CONFIG = {
    "primary": "https://fxo.mathema.com.cn",
    "secondary": "http://172.20.0.154:8803"
}

# Data type and endpoint mapping
DATA_TYPE_MAP = {
    "LocalVol": "/md/mkdata",
    "YieldCurve": "/md/fxoptiondata",
    "ktVolSurface2": "/md/voldata",
    "DiscountRateCurve": "/md/yieldccydata",
    "YieldCurve2": "/md/yieldcurvedata"
}

def get_value_by_case_insensitive_key(dictionary, key):
    # Convert all keys to lowercase
    lowercase_keys = {k.lower(): v for k, v in dictionary.items()}
    # Retrieve the value corresponding to the key
    return lowercase_keys.get(key.lower())

def fetch_data(data_type, params=None, DataServer="",timeout=5):
    """
    Generic data fetching function that dynamically selects endpoints based on data type.

    Args:
        data_type (str): Data type, e.g., 'LocalVol', 'YieldCurve', 'ktVolSurface2', 'DiscountRateCurve'.
        params (dict): Request parameters.
        timeout (int): Request timeout, default 5 seconds.

    Returns:
        dict: Returned JSON data.
    """
    if data_type not in DATA_TYPE_MAP:
        raise ValueError(f"Invalid data type: {data_type}. Supported types: {list(DATA_TYPE_MAP.keys())}")

    # Get data endpoint
    endpoint = DATA_TYPE_MAP[data_type]

    # Construct complete URL
    if (DataServer != ""):
        if not DataServer.startswith(('http://', 'https://')):
            DataServer = 'http://' + DataServer  # Default add http:// prefix
        url_primary = DataServer + endpoint
        url_secondary = SERVER_CONFIG["primary"] + endpoint
    else:
        url_primary = SERVER_CONFIG["primary"] + endpoint
        url_secondary = SERVER_CONFIG["secondary"] + endpoint

    # Configure retry strategy
    session = requests.Session()
    retries = Retry(total=2, backoff_factor=1, status_forcelist=[500, 502, 503, 504, 404])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))

    # Parameter validation
    if params is None:
        params = {}

    # Try first server
    try:
        response = session.post(url_primary, params=params, timeout=timeout)
        response.raise_for_status()  # Raise exception if status code is not 200
        return response.json()
    except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as e:
        print(f"Warning: Primary server failed for {data_type}. Error: {e}")

        # Try second server
        try:
            response = session.post(url_secondary, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except (requests.ConnectionError, requests.Timeout) as e:
            print(f"Error: Secondary server failed for {data_type}. Error: {e}")
            raise Exception(f"Both servers failed to respond for {data_type}.")
        

@xl_func(macro=False, recalc_on_open=False)
@xl_arg("DataServer", "str")
@xl_arg("LocalVolName", "str")
def McpLocalVolData(DataServer, LocalVolName):
    try:
        if not LocalVolName:
            raise ValueError("LocalVolName is required.")
        params = {"Volsurface_shortname": LocalVolName}
        dataMap = fetch_data("LocalVol", params=params, DataServer=DataServer)

        voldata = dataMap["Data"]["localVol"]
        observationRate = 0
        time = ''
        referenceDate = ''
        if 'observationRate' in voldata:
            observationRate = voldata['observationRate']
        if 'lastupdatetime' in voldata:
            time = voldata['lastupdatetime']
        if 'referenceDate' in voldata:
            referenceDate = voldata['referenceDate']
        asset = voldata["assetClass"]
        if "Forex" == asset:
            optiondata = []
            dataSize = len(voldata["expiryDates"])
            for i in range(dataSize):
                tmpdata = []
                tmpdata.append(voldata["expiryDates"][i])
                cp = voldata["optionTypes"][i]
                if cp == 0:
                    tmpdata.append("Call")
                else:
                    tmpdata.append("Put")
                tmpdata.append(voldata["strikes"][i])
                tmpdata.append(voldata["premiums"][i])
                tmpdata.append(voldata["impVols"][i] / 100)
                optiondata.append(tmpdata)

            fxForwardCurve = {
                "ReferenceDate": voldata["fxForwardCurve"]["ReferenceDate"],
                "BidFXSpotRate": voldata["fxForwardCurve"]["BidFXSpotRate"],
                "AskFXSpotRate": voldata["fxForwardCurve"]["AskFXSpotRate"],
                "Method": voldata["fxForwardCurve"]["Method"],
                # "Calendar": voldata["fxForwardCurve"]["BidFXSpotRate"],
                "ScaleFactor": voldata["fxForwardCurve"]["scaleFactor"]
            }
            fwddata = voldata["fxForwardCurve"]["Points"]
            fxForwardCurveData = []
            for i in range(len(fwddata["Ask"])):
                tmpdata = [fwddata["Tenors"][i], (fwddata["Bid"][i] + fwddata["Ask"][i]) / 2]
                fxForwardCurveData.append(tmpdata)

            domesticCurveData = []
            domesdata = voldata["domesticCurve"]
            for item in domesdata["yieldPriceList"]:
                tenor = item["tenor"]
                if tenor == "1W":
                    tenor = "SW"
                tmpdata = [tenor, (item["bid"] + item["ask"]) / 2]
                domesticCurveData.append(tmpdata)

            order = ['ON', 'TN', 'SN', 'SW', '2W', '3W', '1M', '2M', '3M', '4M', '5M', '6M', '7M', '8M', '9M', '10M',
                     '11M', '1Y', '2Y', '3Y', '4Y', '5Y', '7Y', '10Y']
            sorted_domesticCurveData = sorted(domesticCurveData, key=lambda x: order.index(x[0]))

            foreignCurveData = []
            forexdata = voldata["foreignCurve"]
            for item in forexdata["yieldPriceList"]:
                tmpdata = [item["tenor"], (item["bid"] + item["ask"]) / 2]
                foreignCurveData.append(tmpdata)

            forexLocalVolData = {
                "referenceDate": voldata["referenceDate"],
                "spot": voldata["spot"],
                "premiumAdjusted": voldata["premiumAdjusted"],
                "domesticCurve": domesdata["curve_shortname"],
                "foreignCurve": forexdata["curve_shortname"],
                "fxForwardCurve": voldata["fxForwardCurve"]["curveName"],
                "calculatedTarget": voldata["calculationTarget"],
                "LocalVolModel": voldata["model"],
                "loglevel": voldata["logLevel"],
                # "calendar": voldata["calendar"],
                "dateAdjusterRule": voldata["dateAdjusterRule"],
                # "spotDate": voldata["spotDate"],
                "miniStrikeSize": voldata["miniStrikeSize"],
                "usingImpVols": voldata["usingImpVols"]
            }
            key_traceFile = "traceFile"
            if key_traceFile in voldata:
                forexLocalVolData[key_traceFile] = voldata[key_traceFile]
            key_calendar = "calendar"
            if key_calendar in voldata:
                forexLocalVolData[key_calendar] = voldata[key_calendar]

            ForexLocalvol = {
                "OptionData": optiondata,
                "fxForwardCurve": fxForwardCurve,
                "fxForwardCurveData": fxForwardCurveData,
                "domesticCurveData": sorted_domesticCurveData,
                "foreignCurveData": foreignCurveData,
                "Localvol": forexLocalVolData
            }
            if time != '':
                ForexLocalvol['LastUpdateTime'] = time
            if observationRate != 0:
                ForexLocalvol['ObservationRate'] = observationRate
            if referenceDate != '':
                ForexLocalvol['ReferenceDate'] = referenceDate
            return ForexLocalvol
        elif (asset == "Equity"):
            optiondata = []
            dataSize = len(voldata["expiryDates"])
            for i in range(dataSize):
                tmpdata = []
                tmpdata.append(voldata["expiryDates"][i])
                cp = voldata["optionTypes"][i]
                if cp == 0:
                    tmpdata.append("Call")
                else:
                    tmpdata.append("Put")
                tmpdata.append(voldata["strikes"][i])
                tmpdata.append(voldata["premiums"][i])
                tmpdata.append(voldata["impVols"][i])
                optiondata.append(tmpdata)

            riskFreeRateCurveData = []
            riskFreeRateCurve = voldata["riskFreeRateCurve"]
            for item in riskFreeRateCurve["yieldPriceList"]:
                tmpdata = [item["tenor"], item["bid"], item["ask"]]
                riskFreeRateCurveData.append(tmpdata)

            equityLocalVolData = {
                "referenceDate": voldata["referenceDate"],
                "spot": voldata["spot"],
                "riskFreeRateCurve": voldata["riskFreeRateCurve"]["curve_shortname"],
                "dividend": voldata["dividend"],
                "LocalVolModel": voldata["model"],
                "loglevel": voldata["logLevel"],
                "calendar": voldata["calendar"],
                "dateAdjusterRule": voldata["dateAdjusterRule"],
                # "spotDate": voldata["spotDate"],
                "miniStrikeSize": voldata["miniStrikeSize"],
                "usingImpVols": voldata["usingImpVols"]
            }
            key_traceFile = "traceFile"
            if key_traceFile in voldata:
                equityLocalVolData[key_traceFile] = voldata[key_traceFile]

            EquityLocalvol = {
                "OptionData": optiondata,
                "riskFreeRateCurveData": riskFreeRateCurveData,
                "Localvol": equityLocalVolData
            }
            if time != '':
                EquityLocalvol['LastUpdateTime'] = time
            if observationRate != 0:
                EquityLocalvol['ObservationRate'] = observationRate
            if referenceDate != '':
                EquityLocalvol['ReferenceDate'] = referenceDate
            return EquityLocalvol
        elif (asset == "Future"):
            optiondata = []
            dataSize = len(voldata["expiryDates"])
            for i in range(dataSize):
                tmpdata = []
                tmpdata.append(voldata["expiryDates"][i])
                cp = voldata["optionTypes"][i]
                if cp == 0:
                    tmpdata.append("Call")
                else:
                    tmpdata.append("Put")
                tmpdata.append(voldata["strikes"][i])
                tmpdata.append(voldata["premiums"][i])
                tmpdata.append(voldata["impVols"][i])
                optiondata.append(tmpdata)

            riskFreeRateCurveData = []
            riskFreeRateCurve = voldata["riskFreeRateCurve"]
            for item in riskFreeRateCurve["yieldPriceList"]:
                tmpdata = [item["tenor"], item["bid"], item["ask"]]
                riskFreeRateCurveData.append(tmpdata)

            forwardCure = voldata["forwardCurve"]
            forwardCurveData = []
            dataSize1 = len(forwardCure["expiryDates"])
            for i in range(dataSize1):
                tmpdata = [forwardCure["expiryDates"][i], forwardCure["underlyingRates"][i]]
                forwardCurveData.append(tmpdata)

            futureLocalVolData = {
                "referenceDate": voldata["referenceDate"],
                "riskFreeRateCurve": voldata["riskFreeRateCurve"]["curve_shortname"],
                "forwardCurve": "",
                "LocalVolModel": voldata["model"],
                "loglevel": voldata["logLevel"],
                "calendar": voldata["calendar"],
                "dateAdjusterRule": voldata["dateAdjusterRule"],
                # "spotDate": voldata["spotDate"],
                "miniStrikeSize": voldata["miniStrikeSize"],
                "usingImpVols": voldata["usingImpVols"]
            }
            key_traceFile = "traceFile"
            if key_traceFile in voldata:
                futureLocalVolData[key_traceFile] = voldata[key_traceFile]

            FutureLocalvol = {
                "OptionData": optiondata,
                "riskFreeRateCurveData": riskFreeRateCurveData,
                "forwardCurveData": forwardCurveData,
                "Localvol": futureLocalVolData
            }
            if time != '':
                FutureLocalvol['LastUpdateTime'] = time
            if observationRate != 0:
                FutureLocalvol['ObservationRate'] = observationRate
            if referenceDate != '':
                FutureLocalvol['ReferenceDate'] = referenceDate
            return FutureLocalvol
        else:
            raise Exception("unknow asset class!")

    except Exception as e:
        s = f"McpLocalVolData except: {e}"
        return s


@xl_func(macro=False, auto_resize=True,recalc_on_open=False)
@xl_arg("obj", "obj")
def mkdtGetKeys(obj):
    result = None
    if 'KeyDescription' in obj:
        result = list(obj['KeyDescription'].items())
    else:
        result = list(obj.keys())
    return result


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "obj")
@xl_arg("key", "str")
def mkdtGetValue(obj, key):
    ret = get_value_by_case_insensitive_key(obj, key)
    return ret


@xl_func(macro=False, recalc_on_open=False, auto_resize=True, transpose=False)
@xl_arg("obj", "obj")
@xl_arg("key", "str")
@xl_arg("denominator", "float", 0)
def mkdtGetValues(obj, key, denominator):
    if (denominator == 0):
        ret = get_value_by_case_insensitive_key(obj, key)
        if (key.lower() == "optiontypes" or key.lower() == "callputtypes"):
            result = []
            for item in ret:
                if item == 0:
                    result.append("Call")
                elif item == 1:
                    result.append("Put")
                else:
                    raise ValueError("Unexpected value: {}".format(item))
            return result
    else:
        data = get_value_by_case_insensitive_key(obj, key)
        result = []
        for sublist in data:
            label = sublist[0]
            values = sublist[1:]
            average_value = sum(values) / len(values) / denominator
            result.append([label] + [average_value])
        return result
    return ret

@xl_func(macro=False, recalc_on_open=False)
@xl_arg("DataServer", "str")
@xl_arg("CurveName", "str")
def McpYieldCurveData(DataServer="", CurveName=""):
    try:
        if not CurveName:
            return "Invalid param CurveName"

        params = {
            "curve_shortname": CurveName,
            "curveType": "Y",
            "dataType": "ori"
        }
        dataMap = fetch_data('YieldCurve2', params=params, DataServer=DataServer)

        # 检查返回的 Code
        if dataMap["Msg"] == "success":
            yield_data = dataMap["Data"].get("yieldConfPricePoList", [])
            if yield_data:
                # 提取所需的数据
                yield_prices = yield_data[0].get("yieldPriceList", [])
                # 生成 curveData
                curveData = []
                for item in yield_prices:
                    curveData.append([item["tenor"], item["bid"], item["ask"]])

                curve_shortname = yield_data[0].get("curve_shortname", "")
                interpolated_variable = yield_data[0].get("interpolatedVariable", "")

                YieldCurveData = {
                    "curveData": curveData,
                    "curve_shortname": curve_shortname,
                    "interpolatedVariable": interpolated_variable
                }
                return YieldCurveData
            else:
                raise ("unknown data retured!")
        else:
            return None

    except Exception as e:
        return ("unknown data retured!")


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("DataServer", "str")
@xl_arg("CcyName", "str")
def McpDiscountRateCurveData(DataServer, CcyName):
    try:
        if not CcyName:
            raise ValueError("CcyName is required.")
        params = {"ccyname": CcyName}
        dataMap = fetch_data("DiscountRateCurve", params=params, DataServer=DataServer)

        code = dataMap['Code']
        if code != "0000":
            raise Exception(f"Get data fail. Code is {code}.")
        yieldConfPricePoList = dataMap["Data"]["yieldConfPricePoList"]
        # yieldPriceList = yieldConfPricePoList['yieldPriceList']
        discountRateCurveData = []
        disData = yieldConfPricePoList[0]["yieldPriceList"]
        for item in disData:
            tmpdata = [item["tenor"], (item["bid"] + item["ask"]) / 2]
            discountRateCurveData.append(tmpdata)
        DiscountRateCurveData = {'discountRateCurveData': discountRateCurveData}
        return DiscountRateCurveData
    except Exception as e:
        return ("unknown data retured!")


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("DataServer", "str")
@xl_arg("VolSurfaceShortName", "str")
@xl_arg("org_txt", "bool")
def McpMktVolSurface2Data(DataServer, VolSurfaceShortName, org_txt=False):
    try:
        if not VolSurfaceShortName:
            raise ValueError("VolSurfaceShortName is required.")
        params = {"volsurface_shortname": VolSurfaceShortName}
        dataMap = fetch_data("ktVolSurface2", params=params, DataServer=DataServer)

        vol_data = dataMap['Data']
        vol_surface_data = {}
        key_desc_dic = {}
        yld_curve_data = vol_data['YieldCurve']
        for currency, curve_data in yld_curve_data.items():
            ask_arr = to_percent(curve_data['Ask'])
            bid_arr = to_percent(curve_data['Bid'])
            tenors = curve_data['Tenors']
            cur_yld_curve_data = []
            for ask, bid, tenor in zip(ask_arr, bid_arr, tenors):
                cur_yld_curve_data.append([tenor, bid, ask])
            vol_surface_data[f'YieldCurveData({currency})'] = cur_yld_curve_data
            key_desc_dic[f'YieldCurveData({currency})'] = f'{currency}曲线数据'
        ask_points_data = vol_data['Points']['Ask']
        bid_points_data = vol_data['Points']['Bid']
        points_tenor = vol_data['Points']['Tenors']
        points_data = []
        for ask, bid, tenor in zip(ask_points_data, bid_points_data, points_tenor):
            points_data.append([tenor, bid, ask])
        vol_surface_data['ForwardPointsData'] = points_data
        key_desc_dic['ForwardPointsData'] = '远期曲线数据'
        vol_surface_data['SpotAsk'] = vol_data['SpotAsk']
        key_desc_dic['SpotAsk'] = '即期Ask价格'
        vol_surface_data['SpotBid'] = vol_data['SpotBid']
        key_desc_dic['SpotBid'] = '即期Bid价格'
        delta_strings = vol_data['Vol']['DeltaStrings']
        tenors = vol_data['Vol']['Tenors']
        vol_bids = to_percent_2d(vol_data['Vol']['Bid'])
        vol_asks = to_percent_2d(vol_data['Vol']['Ask'])
        # vol_bid_tenor_delta_arr = []
        temp_bid_deltas = ['BidVolatilities/Tenors/DeltaStrings']
        temp_bid_deltas.extend(delta_strings)
        # vol_bid_tenor_delta_arr.append(temp_bid_deltas)
        # for tenor, bids in zip(tenors, vol_bids):
        #     temp_arr = [tenor]
        #     temp_arr.extend(bids)
        #     vol_bid_tenor_delta_arr.append(temp_arr)
        vol_bid_tenor_delta_arr = [temp_bid_deltas]
        i_bid = 0

        for tenor in tenors:
            temp_tenor_bids = [tenor]
            for bids in vol_bids:
                temp_tenor_bids.append(bids[i_bid])
            i_bid = i_bid + 1
            vol_bid_tenor_delta_arr.append(temp_tenor_bids)


        # vol_ask_tenor_delta_arr = []
        temp_ask_deltas = ['AskVolatilities/Tenors/DeltaStrings']
        temp_ask_deltas.extend(delta_strings)
        # vol_ask_tenor_delta_arr.append(temp_ask_deltas)
        # for tenor, asks in zip(tenors, vol_asks):
        #     temp_arr = [tenor]
        #     temp_arr.extend(asks)
        #     vol_ask_tenor_delta_arr.append(temp_arr)
        vol_ask_tenor_delta_arr = [temp_ask_deltas]
        i_ask = 0
        for tenor in tenors:
            temp_tenor_asks = [tenor]
            for asks in vol_asks:
                temp_tenor_asks.append(asks[i_ask])
            i_ask = i_ask + 1
            vol_ask_tenor_delta_arr.append(temp_tenor_asks)
        vol_surface_data['VolatilityAskData'] = vol_ask_tenor_delta_arr
        key_desc_dic['VolatilityAskData'] = '波动率Ask数据'
        vol_surface_data['VolatilityBidData'] = vol_bid_tenor_delta_arr
        key_desc_dic['VolatilityBidData'] = '波动率Bid数据'
        vol_surface_data['KeyDescription'] = key_desc_dic
        return vol_surface_data
    except Exception as e:
        return ("unknown data retured!")



@xl_func(macro=False, recalc_on_open=False)
@xl_arg("DataServer", "str")
@xl_arg("VolSurfaceShortName", "str")
@xl_arg("org_txt", "bool")
def McpFXVolSurface2Data(DataServer, VolSurfaceShortName, org_txt=False):
    try:
        if not VolSurfaceShortName:
            raise ValueError("VolSurfaceShortName is required.")
        params = {"volsurface_shortname": VolSurfaceShortName}
        dataMap = fetch_data("ktVolSurface2", params=params, DataServer=DataServer)

        vol_data = dataMap['Data']
        vol_surface_data = {}
        key_desc_dic = {}
        yld_curve_data = vol_data['YieldCurve']
        for currency, curve_data in yld_curve_data.items():
            ask_arr = to_percent(curve_data['Ask'])
            bid_arr = to_percent(curve_data['Bid'])
            tenors = curve_data['Tenors']
            cur_yld_curve_data = []
            for ask, bid, tenor in zip(ask_arr, bid_arr, tenors):
                cur_yld_curve_data.append([tenor, bid, ask])
            vol_surface_data[f'YieldCurveData({currency})'] = cur_yld_curve_data
            key_desc_dic[f'YieldCurveData({currency})'] = f'{currency}曲线数据'
        ask_points_data = vol_data['Points']['Ask']
        bid_points_data = vol_data['Points']['Bid']
        points_tenor = vol_data['Points']['Tenors']
        points_data = []
        for ask, bid, tenor in zip(ask_points_data, bid_points_data, points_tenor):
            points_data.append([tenor, bid, ask])
        vol_surface_data['ForwardPointsData'] = points_data
        key_desc_dic['ForwardPointsData'] = '远期曲线数据'
        vol_surface_data['SpotAsk'] = vol_data['SpotAsk']
        key_desc_dic['SpotAsk'] = '即期Ask价格'
        vol_surface_data['SpotBid'] = vol_data['SpotBid']
        key_desc_dic['SpotBid'] = '即期Bid价格'
        delta_strings = vol_data['Vol']['DeltaStrings']
        tenors = vol_data['Vol']['Tenors']
        vol_bids = to_percent_2d(vol_data['Vol']['Bid'])
        vol_asks = to_percent_2d(vol_data['Vol']['Ask'])
        # vol_bid_tenor_delta_arr = []
        temp_bid_deltas = ['BidVolatilities/Tenors/DeltaStrings']
        temp_bid_deltas.extend(delta_strings)
        # vol_bid_tenor_delta_arr.append(temp_bid_deltas)
        # for tenor, bids in zip(tenors, vol_bids):
        #     temp_arr = [tenor]
        #     temp_arr.extend(bids)
        #     vol_bid_tenor_delta_arr.append(temp_arr)
        vol_bid_tenor_delta_arr = [temp_bid_deltas]
        i_bid = 0

        for tenor in tenors:
            temp_tenor_bids = [tenor]
            for bids in vol_bids:
                temp_tenor_bids.append(bids[i_bid])
            i_bid = i_bid + 1
            vol_bid_tenor_delta_arr.append(temp_tenor_bids)


        # vol_ask_tenor_delta_arr = []
        temp_ask_deltas = ['AskVolatilities/Tenors/DeltaStrings']
        temp_ask_deltas.extend(delta_strings)
        # vol_ask_tenor_delta_arr.append(temp_ask_deltas)
        # for tenor, asks in zip(tenors, vol_asks):
        #     temp_arr = [tenor]
        #     temp_arr.extend(asks)
        #     vol_ask_tenor_delta_arr.append(temp_arr)
        vol_ask_tenor_delta_arr = [temp_ask_deltas]
        i_ask = 0
        for tenor in tenors:
            temp_tenor_asks = [tenor]
            for asks in vol_asks:
                temp_tenor_asks.append(asks[i_ask])
            i_ask = i_ask + 1
            vol_ask_tenor_delta_arr.append(temp_tenor_asks)
        vol_surface_data['VolatilityAskData'] = vol_ask_tenor_delta_arr
        key_desc_dic['VolatilityAskData'] = '波动率Ask数据'
        vol_surface_data['VolatilityBidData'] = vol_bid_tenor_delta_arr
        key_desc_dic['VolatilityBidData'] = '波动率Bid数据'
        vol_surface_data['KeyDescription'] = key_desc_dic
        return vol_surface_data
    except Exception as e:
        return ("unknown data retured!")

# @xl_func("int, int: dataframe<index=True>",
#          auto_resize=True)
# def random_dataframe(rows, columns):
#     """
#     Creates a DataFrame of random numbers.

#     :param rows: Number of rows to create the DataFrame with.
#     :param columns: Number of columns to create the DataFrame with.
#     """
#     import pandas as pa
#     import numpy as np

#     data = np.random.rand(rows, columns)
#     column_names = [chr(ord('A') + x) for x in range(columns)]
#     df = pa.DataFrame(data, columns=column_names)

#     return df
def to_percent(arr):
    return [item / 100 for item in arr]


def to_percent_2d(arr):
    return [to_percent(item) for item in arr]

# get market data from mcp server using identifiers and key(field name)
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("key", "str")
def McpGet1(identifiers, key):
    result = mcp_server.McpGet1(identifiers, key)
    return result