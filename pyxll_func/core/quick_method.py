from mcp.tool.quick_method import *
from pyxll import RTD, xl_func, xl_arg, xl_return, xl_app, xlfCaller, plot


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args", "var[][]")
@xl_arg("key1", "str")
@xl_arg("val1", "var")
@xl_arg("key2", "str")
@xl_arg("val2", "var")
@xl_arg("key3", "str")
@xl_arg("val3", "var")
@xl_arg("key4", "str")
@xl_arg("val4", "var")
@xl_arg("key5", "str")
@xl_arg("val5", "var")
@xl_arg("key6", "str")
@xl_arg("val6", "var")
@xl_arg("key7", "str")
@xl_arg("val7", "var")
@xl_arg("key8", "str")
@xl_arg("val8", "var")
@xl_arg("key9", "str")
@xl_arg("val9", "var")
@xl_arg("key10", "str")
@xl_arg("val10", "var")
def McpVOPrice(args1, key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7, val7, key8, val8,
               key9, val9, key10, val10):
    return QmVanillaOption.price(
        QmUtils.parse_qm_args(args1,
                              [key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7, val7, key8,
                               val8, key9, val9, key10, val10]))


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args", "var[][]")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
@xl_arg("key1", "str")
@xl_arg("val1", "var")
@xl_arg("key2", "str")
@xl_arg("val2", "var")
@xl_arg("key3", "str")
@xl_arg("val3", "var")
@xl_arg("key4", "str")
@xl_arg("val4", "var")
@xl_arg("key5", "str")
@xl_arg("val5", "var")
@xl_arg("key6", "str")
@xl_arg("val6", "var")
@xl_arg("key7", "str")
@xl_arg("val7", "var")
@xl_arg("key8", "str")
@xl_arg("val8", "var")
@xl_arg("key9", "str")
@xl_arg("val9", "var")
@xl_arg("key10", "str")
@xl_arg("val10", "var")
def McpVODelta(args1, isCcy2, isAmount, key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7,
               val7, key8, val8,
               key9, val9, key10, val10):
    return QmVanillaOption.delta(
        QmUtils.parse_qm_args(args1,
                              [key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7, val7, key8,
                               val8, key9, val9, key10, val10]), isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args", "var[][]")
@xl_arg("key1", "str")
@xl_arg("val1", "var")
@xl_arg("key2", "str")
@xl_arg("val2", "var")
@xl_arg("key3", "str")
@xl_arg("val3", "var")
@xl_arg("key4", "str")
@xl_arg("val4", "var")
@xl_arg("key5", "str")
@xl_arg("val5", "var")
@xl_arg("key6", "str")
@xl_arg("val6", "var")
@xl_arg("key7", "str")
@xl_arg("val7", "var")
@xl_arg("key8", "str")
@xl_arg("val8", "var")
@xl_arg("key9", "str")
@xl_arg("val9", "var")
@xl_arg("key10", "str")
@xl_arg("val10", "var")
def McpVOMarketValue(args1, key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7, val7, key8,
                     val8,
                     key9, val9, key10, val10):
    return QmVanillaOption.MarketValue(
        QmUtils.parse_qm_args(args1,
                              [key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7, val7, key8,
                               val8, key9, val9, key10, val10]))


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args", "var[][]")
@xl_arg("key1", "str")
@xl_arg("val1", "var")
@xl_arg("key2", "str")
@xl_arg("val2", "var")
@xl_arg("key3", "str")
@xl_arg("val3", "var")
@xl_arg("key4", "str")
@xl_arg("val4", "var")
@xl_arg("key5", "str")
@xl_arg("val5", "var")
@xl_arg("key6", "str")
@xl_arg("val6", "var")
@xl_arg("key7", "str")
@xl_arg("val7", "var")
@xl_arg("key8", "str")
@xl_arg("val8", "var")
@xl_arg("key9", "str")
@xl_arg("val9", "var")
@xl_arg("key10", "str")
@xl_arg("val10", "var")
def McpVOPV(args1, key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7, val7, key8, val8,
            key9, val9, key10, val10):
    return QmVanillaOption.PresentValue(
        QmUtils.parse_qm_args(args1,
                              [key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7, val7, key8,
                               val8, key9, val9, key10, val10]))


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args", "var[][]")
@xl_arg("key1", "str")
@xl_arg("val1", "var")
@xl_arg("key2", "str")
@xl_arg("val2", "var")
@xl_arg("key3", "str")
@xl_arg("val3", "var")
@xl_arg("key4", "str")
@xl_arg("val4", "var")
@xl_arg("key5", "str")
@xl_arg("val5", "var")
@xl_arg("key6", "str")
@xl_arg("val6", "var")
@xl_arg("key7", "str")
@xl_arg("val7", "var")
@xl_arg("key8", "str")
@xl_arg("val8", "var")
@xl_arg("key9", "str")
@xl_arg("val9", "var")
@xl_arg("key10", "str")
@xl_arg("val10", "var")
def McpVOStrikeFromPrice(args1, key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7, val7,
                         key8, val8,
                         key9, val9, key10, val10):
    args_list = QmUtils.parse_qm_args(args1,
                                      [key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7,
                                       val7, key8,
                                       val8, key9, val9, key10, val10])
    data = args_list[1]
    # 遍历列表以查找'Price'
    for item in data:
        if item[0].lower() == 'premium' or item[0].lower() == 'price':
            target_price = item[1]
            break  # 找到'Price'后就不再继续循环
        # 遍历列表以查找'Spot'
    for item in data:
        if item[0].lower() == 'forwardpx':
            mid_price = item[1]
            break  # 找到'Spot'后就不再继续循环
    # 通过二分法找到strike，需要设定strike的上下限
    if mid_price == None:
        low = 0
        high = 100000
    else:
        low = mid_price * 0.5
        high = mid_price * 1.5
    return QmVanillaOption.StrikeImpliedFromPrice(target_price, args_list, low, high)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args", "var[][]")
@xl_arg("key1", "str")
@xl_arg("val1", "var")
@xl_arg("key2", "str")
@xl_arg("val2", "var")
@xl_arg("key3", "str")
@xl_arg("val3", "var")
@xl_arg("key4", "str")
@xl_arg("val4", "var")
@xl_arg("key5", "str")
@xl_arg("val5", "var")
@xl_arg("key6", "str")
@xl_arg("val6", "var")
@xl_arg("key7", "str")
@xl_arg("val7", "var")
@xl_arg("key8", "str")
@xl_arg("val8", "var")
@xl_arg("key9", "str")
@xl_arg("val9", "var")
@xl_arg("key10", "str")
@xl_arg("val10", "var")
def McpVOObject(args1, key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7, val7, key8, val8,
                key9, val9, key10, val10):
    return QmVanillaOption.gen_instance(
        QmUtils.parse_qm_args(args1,
                              [key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7, val7, key8,
                               val8, key9, val9, key10, val10]))


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args", "var[][]")
@xl_arg("key1", "str")
@xl_arg("val1", "var")
@xl_arg("key2", "str")
@xl_arg("val2", "var")
@xl_arg("key3", "str")
@xl_arg("val3", "var")
@xl_arg("key4", "str")
@xl_arg("val4", "var")
@xl_arg("key5", "str")
@xl_arg("val5", "var")
@xl_arg("key6", "str")
@xl_arg("val6", "var")
@xl_arg("key7", "str")
@xl_arg("val7", "var")
@xl_arg("key8", "str")
@xl_arg("val8", "var")
@xl_arg("key9", "str")
@xl_arg("val9", "var")
@xl_arg("key10", "str")
@xl_arg("val10", "var")
def McpFwdPrice(args1, key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7, val7, key8, val8,
                key9, val9, key10, val10):
    return QmFXForward2.price(
        QmUtils.parse_qm_args(args1,
                              [key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7, val7, key8,
                               val8, key9, val9, key10, val10]))


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args", "var[][]")
@xl_arg("key1", "str")
@xl_arg("val1", "var")
@xl_arg("key2", "str")
@xl_arg("val2", "var")
@xl_arg("key3", "str")
@xl_arg("val3", "var")
@xl_arg("key4", "str")
@xl_arg("val4", "var")
@xl_arg("key5", "str")
@xl_arg("val5", "var")
@xl_arg("key6", "str")
@xl_arg("val6", "var")
@xl_arg("key7", "str")
@xl_arg("val7", "var")
@xl_arg("key8", "str")
@xl_arg("val8", "var")
@xl_arg("key9", "str")
@xl_arg("val9", "var")
@xl_arg("key10", "str")
@xl_arg("val10", "var")
def McpFwdMarketValue(args1, key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7, val7, key8,
                      val8,
                      key9, val9, key10, val10):
    return QmFXForward2.MarketValue(
        QmUtils.parse_qm_args(args1,
                              [key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7, val7, key8,
                               val8, key9, val9, key10, val10]))


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args", "var[][]")
@xl_arg("key1", "str")
@xl_arg("val1", "var")
@xl_arg("key2", "str")
@xl_arg("val2", "var")
@xl_arg("key3", "str")
@xl_arg("val3", "var")
@xl_arg("key4", "str")
@xl_arg("val4", "var")
@xl_arg("key5", "str")
@xl_arg("val5", "var")
@xl_arg("key6", "str")
@xl_arg("val6", "var")
@xl_arg("key7", "str")
@xl_arg("val7", "var")
@xl_arg("key8", "str")
@xl_arg("val8", "var")
@xl_arg("key9", "str")
@xl_arg("val9", "var")
@xl_arg("key10", "str")
@xl_arg("val10", "var")
def McpFwdPV(args1, key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7, val7, key8, val8,
             key9, val9, key10, val10):
    return QmFXForward2.PresentValue(
        QmUtils.parse_qm_args(args1,
                              [key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7, val7, key8,
                               val8, key9, val9, key10, val10]))


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args", "var[][]")
@xl_arg("key1", "str")
@xl_arg("val1", "var")
@xl_arg("key2", "str")
@xl_arg("val2", "var")
@xl_arg("key3", "str")
@xl_arg("val3", "var")
@xl_arg("key4", "str")
@xl_arg("val4", "var")
@xl_arg("key5", "str")
@xl_arg("val5", "var")
@xl_arg("key6", "str")
@xl_arg("val6", "var")
@xl_arg("key7", "str")
@xl_arg("val7", "var")
@xl_arg("key8", "str")
@xl_arg("val8", "var")
@xl_arg("key9", "str")
@xl_arg("val9", "var")
@xl_arg("key10", "str")
@xl_arg("val10", "var")
def McpCFPrice(args1, key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7, val7, key8, val8,
               key9, val9, key10, val10):
    return QmCustomForward.price(
        QmUtils.parse_qm_args(args1,
                              [key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7, val7, key8,
                               val8, key9, val9, key10, val10]))


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args", "var[][]")
@xl_arg("key1", "str")
@xl_arg("val1", "var")
@xl_arg("key2", "str")
@xl_arg("val2", "var")
@xl_arg("key3", "str")
@xl_arg("val3", "var")
@xl_arg("key4", "str")
@xl_arg("val4", "var")
@xl_arg("key5", "str")
@xl_arg("val5", "var")
@xl_arg("key6", "str")
@xl_arg("val6", "var")
@xl_arg("key7", "str")
@xl_arg("val7", "var")
@xl_arg("key8", "str")
@xl_arg("val8", "var")
@xl_arg("key9", "str")
@xl_arg("val9", "var")
@xl_arg("key10", "str")
@xl_arg("val10", "var")
def McpCFStrikeImpliedFromPrice(args1, key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7,
                                val7, key8, val8,
                                key9, val9, key10, val10):
    return QmCustomForward.strike_from_price(args1,
                                             [key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6,
                                              key7, val7, key8, val8, key9, val9, key10, val10])


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("args", "var[][]")
@xl_arg("key1", "str")
@xl_arg("val1", "var")
@xl_arg("key2", "str")
@xl_arg("val2", "var")
@xl_arg("key3", "str")
@xl_arg("val3", "var")
@xl_arg("key4", "str")
@xl_arg("val4", "var")
@xl_arg("key5", "str")
@xl_arg("val5", "var")
@xl_arg("key6", "str")
@xl_arg("val6", "var")
@xl_arg("key7", "str")
@xl_arg("val7", "var")
@xl_arg("key8", "str")
@xl_arg("val8", "var")
@xl_arg("key9", "str")
@xl_arg("val9", "var")
@xl_arg("key10", "str")
@xl_arg("val10", "var")
def McpRangeForwardStrikes(args1, key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7,
                           val7, key8, val8,
                           key9, val9, key10, val10):
    strike2 = 7
    for arr in args1:
        if len(arr) >= 2:
            if arr[0].lower() == 'spotpx':
                strike2 = float(arr[1])
    strike1 = None
    for i in range(1000):
        kvs = [key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6,
               key7, val7, key8, val8, key9, val9, key10, val10]
        kvs.extend(['Strike2', strike2])
        strike1 = QmCustomForward.strike_from_price(args1, kvs)
        # print(f"McpRangeForwardPrice: {strike1}, {strike2}")
        if abs(strike2 - strike1) <= 0.000001:
            break
        strike2 += (strike1 - strike2) / 2
    return [[strike1, strike2]]


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args", "var[][]")
@xl_arg("key1", "str")
@xl_arg("val1", "var")
@xl_arg("key2", "str")
@xl_arg("val2", "var")
@xl_arg("key3", "str")
@xl_arg("val3", "var")
@xl_arg("key4", "str")
@xl_arg("val4", "var")
@xl_arg("key5", "str")
@xl_arg("val5", "var")
@xl_arg("key6", "str")
@xl_arg("val6", "var")
@xl_arg("key7", "str")
@xl_arg("val7", "var")
@xl_arg("key8", "str")
@xl_arg("val8", "var")
@xl_arg("key9", "str")
@xl_arg("val9", "var")
@xl_arg("key10", "str")
@xl_arg("val10", "var")
def McpCFObject(args1, key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7, val7, key8, val8,
                key9, val9, key10, val10):
    return QmCustomForward.gen_instance(
        QmUtils.parse_qm_args(args1,
                              [key1, val1, key2, val2, key3, val3, key4, val4, key5, val5, key6, val6, key7, val7, key8,
                               val8, key9, val9, key10, val10]))
