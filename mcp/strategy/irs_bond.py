from mcp.utils.enums import ExchangePrincipal, ResidualType, AmortisationType, DateAdjusterRule
from mcp.mcp import MVanillaSwap, MFixedRateBond, MCalendar
from mcp.tool.tools_main import McpVanillaSwap, McpFixedRateBond
from mcp.xscript.utils import SttUtils


class DefCacheDic:
    def __init__(self):
        self.asset_def_dic = {}
        self.contract_def_dic = {}
        self.portfolio_dic = {}

    def add_portfolio(self, key, val):
        self.portfolio_dic[key] = val

    def add_asset(self, key, val):
        self.asset_def_dic[key] = val

    def add_contract(self, key, val):
        self.contract_def_dic[key] = val

    def get_contract_def(self, assetid):
        if assetid is None:
            raise Exception(f"Asset id is none.")
        t_arr = assetid.split("-")
        asset = t_arr[0]
        asset_args = {}
        if len(t_arr) == 2:
            if assetid not in self.contract_def_dic or asset not in self.asset_def_dic:
                raise Exception(f"{assetid}, not define.")
            asset_args = self.asset_def_dic[asset]
        else:
            if assetid not in self.contract_def_dic:
                raise Exception(f"{assetid}, not define.")

        contract_args = self.contract_def_dic[assetid]
        args = {}
        args.update(asset_args)
        args.update(contract_args)
        print(f'{assetid} args: {args}')
        return args


cache = DefCacheDic()


class VanillaSwapContractDef:
    def __init__(self, asset, args):
        cache.add_asset(asset, args)


class VanillaSwapGroupDef:
    def __init__(self, assetid, args):
        cache.add_contract(assetid, args)


class FixedRateBondGroupDef:
    def __init__(self, assetid, args):
        cache.add_contract(assetid, args)

class FIPortfolioDef:
    def __init__(self, assetid_list, yld_list, amount_list):
        self.assetid_list = assetid_list
        self.yld_list = yld_list
        self.amount_list = amount_list

class CallObj:
    def __init__(self):

        pass

    def call_portfolio_duration(self, obj: FIPortfolioDef, yld_list):
        result = 0
        total_sum = 0
        total_amount = 0
        for assetid, amount, yld in zip(obj.assetid_list, obj.amount_list, yld_list):
            args = [assetid, 'Duration', yld]
            single_val = self.call(args)
            total_sum = total_sum + single_val[0] * amount
            total_amount = total_amount + amount
            # result = result + single_val[0]
        result = total_sum / total_amount
        return result

    def call_portfolio_dv01(self, obj: FIPortfolioDef, yld_list):
        result = 0
        for assetid, amount, yld in zip(obj.assetid_list, obj.amount_list, yld_list):
            args = [assetid, 'DV01', yld]
            single_val = self.call(args)
            result = result + single_val[0]
        return result

    def call_portfolio_krd(self, obj: FIPortfolioDef, yld_list, curve, tenors):
        result = []
        sum = None
        total_sum = 0
        total_amount = 0
        # 初始化一个空的汇总KRD字典
        aggregated_krd = {}
        for assetid, amount, yld in zip(obj.assetid_list, obj.amount_list, yld_list):
            args = [assetid, 'KRDS', [yld, curve, tenors]]
            single_val = self.call(args)
            total_amount = total_amount + amount
            # 遍历每个时间点的KRD值
            i = 0
            for krd_value in single_val[0]:
                if i not in aggregated_krd:
                    aggregated_krd[i] = 0
                aggregated_krd[i] += krd_value * amount
                i = i + 1
        weighted_average_krd = [value / total_amount for timepoint, value in aggregated_krd.items()]
            # if sum is None:
            #     sum = single_val[0]
            # else:
            #     for x, y in zip(sum, single_val[0]):
            #         total_sum = total_sum + x * amount + y * amount
            #     sum = [x + y for x, y in zip(sum, single_val[0])]
        # result.append(sum)
        result.append(weighted_average_krd)
        return result

    def call(self, args):
        assetid = args[0]
        params = cache.get_contract_def(assetid)
        is_bond = True
        if assetid.count('-') > 0:
            is_bond = False
        method = args[1]
        m_param = args[2]
        if is_bond:
            return self.call_bond(params, method, m_param)
        else:
            return self.call_swap(params, method, m_param)

    def call_swap(self, params, methods, m_param):
        args = {'Coupon': m_param, 'Notional': 100.0, 'FloatKeepEndOfMonth': True, 'FloatLongStub': False, 'FloatEndStub': True,
                'FloatAdjStartDate': True, 'FloatAdjEndDate': True
                , 'FloatExchangeNotional': ExchangePrincipal.BOTHENDS, 'FloatResidualType': ResidualType.AbsoluteValue,
                'FloatResidual': 0, 'FloatAmortisationType': AmortisationType.AMRT_NONE}
        args.update(params)
        calender: MCalendar = args['Calendar']
        args['StartDate'] = calender.AddBusinessDays(args['ReferenceDate'], int(args['SwapStartLag']))
        args['RollDate'] = args['StartDate']
        args['EndDate'] = calender.AddPeriod(args['StartDate'], args['Tenor'], DateAdjusterRule.ModifiedFollowing)
        vs: MVanillaSwap = McpVanillaSwap(args)
        # vs.MarketParRate()
        vs_field = ['NPV', 'DV01', 'MarketValue', 'Accrued', 'MDuration', 'Duration']
        vs_func = [vs.NPV, vs.DV01, vs.MarketValue, vs.Accrued, vs.MDuration, vs.Duration]
        method_arr = methods.split(',')
        result = []
        for f, fc in zip(vs_field, vs_func):
            for method in method_arr:
                if method == f:
                    val = fc()
                    result.append(val)
                    break
        return result

    def call_bond(self, params, methods, m_param):
        args = {}
        args.update(params)
        frb: MFixedRateBond = McpFixedRateBond(args)
        method = methods
        if method == 'KRDS':
            return self.call_bond_krds(frb, m_param)
        if method == "DirtyPrice":
            return self.call_bond_dirty(frb, m_param)
        if method == "Accrued":
            return self.call_bond_accrued(frb, m_param)
        if method == "MarketValue":
            return self.call_bond_mv(frb, m_param)
        yld = self.check_bond_yld(frb, m_param)
        # frb.AccruedInterestCHN()
        # frb.PriceCHN()
        frb_field = ['Duration','MDuration', 'DV01']
        frb_func = [frb.DurationCHN, frb.MDurationCHN, frb.PVBPCHN]
        method_arr = methods.split(',')
        # values = frb.KeyRateDuration(bond_curve, tenors)
        result = []
        for f, fc in zip(frb_field, frb_func):
            for method in method_arr:
                if method == f:
                    val = fc(yld)
                    result.append(val)
                    break
        return result

    def call_bond_krds(self, frb: MFixedRateBond, method_param):
        bond_curve = method_param[1]
        tenors = method_param[2]
        values = frb.KeyRateDuration(bond_curve, tenors)
        return [values]

    def call_bond_dirty(self, frb: MFixedRateBond, method_param):
        values = frb.DirtyPriceFromYieldCHN(method_param, True)
        return values

    def call_bond_mv(self, frb: MFixedRateBond, method_param):
        values = frb.PriceCHN(method_param)
        return values

    def call_bond_accrued(self, frb: MFixedRateBond, method_param):
        values = frb.AccruedInterestCHN()
        return values

    def check_bond_yld(self, frb: MFixedRateBond, method_param):
        yld = method_param
        if method_param > 1:
            yld = frb.YieldFromDirtyPriceCHN(method_param, True)
        return yld