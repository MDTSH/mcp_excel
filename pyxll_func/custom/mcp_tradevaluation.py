import traceback

from pyxll import RTD, xl_func, xl_arg, xl_return, xl_app, xlfCaller, plot, _log
from datetime import datetime, timedelta
from pyxll import xl_func, get_type_converter

from mcp.forward.fwd_wrapper import McpVanillaOption
from mcp.tool.quick_method import QmVanillaOption, QmUtils


def excel_date_to_string(excel_date):
    if isinstance(excel_date, float):
        # Excel的日期从1900-01-01开始
        base_date = datetime(1899, 12, 30)
        # 将Excel日期转换为timedelta
        delta_days = timedelta(days=float(excel_date))
        # 计算日期
        date_obj = base_date + delta_days
        # 格式化日期字符串
        date_string = date_obj.strftime('%Y-%m-%d')
        return date_string
    else:
        return excel_date


@xl_func(macro=False, recalc_on_open=True, thread_safe=False, auto_resize=True)
@xl_arg("args", "var[][]")
@xl_arg("data", "var[][]")
def McpVoGreeks1(args, data):
    result = []
    for row in data:
        try:
            args2 = []
            OptionExpiryNature = str(row[1])
            t_buy_sell = str(row[2])
            BuySell = 'Sell'
            if t_buy_sell.lower() == 'b' or t_buy_sell.lower() == 'buy':
                BuySell = 'Buy'
            Pair = str(row[3]) + str(row[5])
            CallPut = str(row[4])
            Tenor = str(row[6])
            FaceAmount = row[7]
            StrikePx = row[8]
            expiryDate = excel_date_to_string(row[10])
            PremiumDate = excel_date_to_string(row[12])
            settlementDate = excel_date_to_string(row[11])
            args2.append('OptionExpiryNature')
            args2.append(OptionExpiryNature)
            args2.append('BuySell')
            args2.append(BuySell)
            args2.append('Pair')
            args2.append(Pair)
            args2.append('CallPut')
            args2.append(CallPut)
            args2.append('FaceAmount')
            args2.append(FaceAmount)
            args2.append('StrikePx')
            args2.append(StrikePx)
            args2.append('expiryDate')
            args2.append(expiryDate)
            args2.append('PremiumDate')
            args2.append(PremiumDate)
            args2.append('DeliveryDate')
            args2.append(settlementDate)
            vo: McpVanillaOption = QmVanillaOption.gen_instance(QmUtils.parse_qm_args(args, args2))
            if isinstance(vo, McpVanillaOption):
                delta = vo.Delta(False, True)
                gamma = vo.Gamma(False, True)
                theta = vo.Theta(False, True)
                vega = vo.Vega(False, True)
                rho = vo.Rho(False, True)
                market_value = vo.MarketValue(True)
                #result.append(f'{delta}, {vega}, {market_value}')
                result.append([delta, gamma, theta, vega, rho,  market_value])
            else:
                result.append([vo, None, None, None, None,  None])
        except:
            traceback.print_exc()
            raise Exception("Process error.")
    return result


@xl_func(macro=False, recalc_on_open=True, thread_safe=False, auto_resize=True)
@xl_arg("args", "var[][]")
@xl_arg("data", "var[][]")
@xl_arg("greek_types", "str[]")  # 新增参数接收要返回的Greeks类型列表
def McpVoGreeks(args, data, greek_types):
    # 创建一个字典映射Greeks名称到计算方法，包括货币单位参数
    greeks_calculators = {
        "Price(CNY)": lambda vo: vo.Price(True),
        "Premium": lambda vo: vo.Price(False),
        "MarketValue": lambda vo: vo.MarketValue(True),
        "forward delta(%)-CNY": lambda vo: vo.ForwardDelta(True, False),
        "forward delta(%)-USD": lambda vo: vo.ForwardDelta(False, False),
        "ForwardDelta-CNY": lambda vo: vo.ForwardDelta(True, True),
        "ForwardDelta-USD": lambda vo: vo.ForwardDelta(False, True),
        "Delta%(CNY)": lambda vo: vo.Delta(True, False),
        "Delta%(USD)": lambda vo: vo.Delta(False, False),
        "Delta-CNY": lambda vo: vo.Delta(True, True),
        "Delta-USD": lambda vo: vo.Delta(False, True),
        "Vega(CNY)": lambda vo: vo.Vega(True, True),
        "Vega(USD)": lambda vo: vo.Vega(False, True),
        "Gamma(CNY)": lambda vo: vo.Gamma(True, True),
        "Gamma(USD)": lambda vo: vo.Gamma(False, True),
        "Theta(CNY)": lambda vo: vo.Theta(True, True),
        "Theta(USD)": lambda vo: vo.Theta(False, True),
        "Vanna(CNY)": lambda vo: vo.Vanna(True, True),
        "Vanna(USD)": lambda vo: vo.Vanna(False, True),
        "Volga(CNY)": lambda vo: vo.Volga(True, True),
        "Volga(USD)": lambda vo: vo.Volga(False, True),
        "Rho(CNY)": lambda vo: vo.Rho(True, True),
        "Rho(USD)": lambda vo: vo.Rho(False, True),
        "Phi(CNY)": lambda vo: vo.Phi(True, True),
        "Phi(USD)": lambda vo: vo.Phi(False, True)
    }
    result = []
    for row in data:
        try:
            args2 = []
            OptionExpiryNature = str(row[1])
            # 设置美式的用BSPDE定价方法
            if OptionExpiryNature == 'American':
                for sublist in args:
                    if sublist[0] == 'PricingMethod':
                        sublist[1] = 'BSPDE'
                        break  # 找到后退出循环

            t_buy_sell = str(row[2])
            BuySell = 'Sell'
            if t_buy_sell.lower() == 'b' or t_buy_sell.lower() == 'buy':
                BuySell = 'Buy'
            Pair = str(row[3]) + str(row[5])
            CallPut = str(row[4])
            Tenor = str(row[6])
            FaceAmount = row[7]
            StrikePx = row[8]
            expiryDate = excel_date_to_string(row[10])
            PremiumDate = excel_date_to_string(row[12])
            for sublist in args:
                if sublist[0] == 'ReferenceDate':
                    PremiumDate = sublist[1]
                    break  # 找到后退出循环
            #PremiumDate = args['ReferenceDate']
            settlementDate = excel_date_to_string(row[11])
            args2.append('OptionExpiryNature')
            args2.append(OptionExpiryNature)
            args2.append('BuySell')
            args2.append(BuySell)
            args2.append('Pair')
            args2.append(Pair)
            args2.append('CallPut')
            args2.append(CallPut)
            args2.append('FaceAmount')
            args2.append(FaceAmount)
            args2.append('StrikePx')
            args2.append(StrikePx)
            args2.append('ExpiryDate')
            args2.append(expiryDate)
            args2.append('PremiumDate')
            args2.append(PremiumDate)
            args2.append('DeliveryDate')
            args2.append(settlementDate)
            vo: McpVanillaOption = QmVanillaOption.gen_instance( QmUtils.parse_qm_args(args, args2))
            if isinstance(vo, McpVanillaOption):
                # 为每个请求的greek类型计算值
                row = []
                for greek_type in greek_types:
                    greek_type = greek_type.strip()  # 去除可能的空格
                    if greek_type in greeks_calculators:
                        value = greeks_calculators[greek_type](vo)
                        row.append(value)
                    else:
                        row.append(None)  # 如果输入了不支持的greek类型，返回None
                result.append(row)
            else:
                # 如果不是有效option，返回与输入长度相同的None列表
                result.append([None] * len(greek_types))
        except:
            traceback.print_exc()
            raise Exception("Process error.")
    return result

@xl_func(macro=False, recalc_on_open=True, thread_safe=False, auto_resize=True)
@xl_arg("args", "var[][]")
@xl_arg("data", "var[][]")
@xl_arg("spotChange", "var[]")
def McpVoReport4(args, data, spotChange):
    init_spot = args[1][1]
    result = []
    for _spotchange in spotChange:
        spot = init_spot * (1 + _spotchange)
        args[1][1] = spot
        delta = 0
        vega = 0
        market_value = 0
        B_Call_Amt = 0
        B_Put_Amt = 0
        S_Call_Amt = 0
        S_Put_Amt = 0 
        #forward = args[7][1].GetForward()
        for row in data:
            try:
                args2 = []
                OptionExpiryNature = str(row[1])
                t_buy_sell = str(row[2])
                BuySell = 'Sell'
                if t_buy_sell.lower() == 'b' or t_buy_sell.lower() == 'buy':
                    BuySell = 'Buy'
                Pair = str(row[3]) + str(row[5])
                CallPut = str(row[4])
                Tenor = str(row[6])
                FaceAmount = row[7]
                StrikePx = row[8]
                expiryDate = excel_date_to_string(row[10])
                PremiumDate = excel_date_to_string(row[12])
                settlementDate = excel_date_to_string(row[11])
                args2.append('OptionExpiryNature')
                args2.append(OptionExpiryNature)
                args2.append('BuySell')
                args2.append(BuySell)
                args2.append('Pair')
                args2.append(Pair)
                args2.append('CallPut')
                args2.append(CallPut)
                args2.append('FaceAmount')
                args2.append(FaceAmount)
                args2.append('StrikePx')
                args2.append(StrikePx)
                args2.append('expiryDate')
                args2.append(expiryDate)
                args2.append('PremiumDate')
                args2.append(PremiumDate)
                args2.append('DeliveryDate')
                args2.append(settlementDate)
                volatility = args[7][1].GetVolatility(StrikePx, expiryDate, 'MID')
                args2.append('Volatility')
                args2.append(volatility)
                #### 
                forward = args[7][1].GetForward(expiryDate)
                forward = forward * (1 + _spotchange)
                args2.append('ForwardPx')
                args2.append(forward)

                vo: McpVanillaOption = QmVanillaOption.gen_instance(QmUtils.parse_qm_args(args, args2))
                if BuySell == 'Buy' and CallPut == 'Call':
                    if spot < StrikePx:  #价內
                        B_Call_Amt = B_Call_Amt + FaceAmount
                elif  BuySell == 'Buy' and CallPut == 'Put':
                    if spot > StrikePx:  #价內
                        B_Put_Amt = B_Put_Amt + FaceAmount
                elif  BuySell == 'Sell' and CallPut == 'Call':
                    if spot < StrikePx:  #价內
                        S_Call_Amt = S_Call_Amt + FaceAmount
                elif BuySell == 'Sell' and CallPut == 'Put':
                    if spot > StrikePx:  #价內
                        S_Put_Amt = S_Put_Amt + FaceAmount 
                else:
                    pass

                if isinstance(vo, McpVanillaOption):
                    delta = vo.Delta(False, True) + delta
                    vega = vo.Vega(False, True) + vega
                    market_value = vo.MarketValue(True) + market_value
                    #result.append(f'{delta}, {vega}, {market_value}')
                else:
                    result.append([vo, None, None, None, None,  None, None])
            except:
                traceback.print_exc()
                raise Exception("Process error.")
            
        result.append([delta / 10000, vega/ 10000,B_Call_Amt/ 10000,B_Put_Amt/ 10000,S_Call_Amt/ 10000, S_Put_Amt/ 10000, market_value/ 10000])

    return result