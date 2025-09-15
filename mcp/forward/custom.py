from mcp.utils.excel_utils import FieldName
from mcp.utils.mcp_utils import *
from mcp.wrapper import is_vol_surface, mcp_logging, McpFXVolSurface2
from mcp.forward.fwd_wrapper import *


class GuessObject:

    def __init__(self, low, high, val=0):
        self.low = low
        self.high = high
        self.value = val
        self.rg_list = None
        self.val_list = {}

    def split_range(self, count):
        d_step = (self.high - self.low) / count
        self.rg_list = [self.low + i * d_step for i in range(count)]
        self.rg_list.append(self.high)
        return self.rg_list

    def add_guess_value(self, guess, val):
        self.val_list[guess] = val

    def find_lower_range(self, count):
        result_list = []
        for i in range(1, len(self.rg_list)):
            lower = self.rg_list[i - 1]
            upper = self.rg_list[i]
            val = abs(self.val_list[lower] + self.val_list[upper])
            result_list.append(GuessObject(lower, upper, val))

        return sort_reduce(result_list, count)

    def print_values(self):
        vals = [self.val_list[item] for item in self.rg_list]
        print("GuessObject:", self.rg_list, vals)


def sort_reduce(result_list, count):
    result_list.sort(key=lambda item: item.value)
    return result_list[0:count]


class McpBaseCompound(PayoffSpec):

    def __init__(self):
        pass

    def price(self, price_method=None):
        pass

    def copy(self, args, guess_strike):
        return self

    def guess_strike_args(self, args):
        tolerance = 0.1
        if FieldName.Tolerance in args:
            tolerance = float(args[FieldName.Tolerance])
        deltaRHS = True
        if FieldName.DeltaRHS in args:
            deltaRHS = str(args[FieldName.DeltaRHS]).lower() == "true"
        maxNumIterations = 50
        if FieldName.MaxNumIterations in args:
            maxNumIterations = int(args[FieldName.MaxNumIterations])
        return deltaRHS, tolerance, maxNumIterations

    def guess_strike(self, low, high, price, args):
        # print("guess_strike:", low, high, price, args)
        dt_start = datetime.now()
        deltaRHS, tolerance, maxNumIterations = self.guess_strike_args(args)
        strike = None
        ins_temp = self.copy(args, low)
        d_low = ins_temp.price()
        ins_temp.del_ref()
        d_low = price - d_low
        ins_temp = self.copy(args, high)
        d_high = ins_temp.price()
        ins_temp.del_ref()
        d_high = price - d_high
        #print(f"low={low},high={high},price={price}")
        for i in range(maxNumIterations):
            # try:
            mid = (high + low) / 2
            ins_temp = self.copy(args, mid)
            d_mid = price - ins_temp.price()
            ins_temp.del_ref()
            # print(f"{i}: low={low}, mid={mid}, high={high}, d={d_low},{d_mid},{d_high}")
            if abs(d_mid) <= tolerance:
                strike = mid
                break
            if d_mid * d_high > 0:
                high = mid
                d_high = d_mid
            else:
                low = mid
                d_low = d_mid
                # print("guess_strike:", low, high)
                # except:
                #     print(f"guess_strike except: {low}, {high}")
                #     traceback.print_exc()
                # raise Exception('guess_strike except')
        dt_end = datetime.now()
        # print("guess_strike use %s s, %s" % (dt_end - dt_start, args))
        return strike

    # def guess_strike2(self, low, high, price, args):
    #     count = 9
    #     deltaRHS, tolerance, maxNumIterations = self.guess_strike_args(args)
    #     guess_list = [GuessObject(low, high)]
    #     iterations = 0
    #     guess_result = None
    #     find_val = False
    #     while len(guess_list) > 0:
    #         temp_list = guess_list
    #         guess_list = []
    #         for guess in temp_list:
    #             rg_list = guess.split_range(count)
    #             for rg in rg_list:
    #                 val_rg = self.copy(args, rg).price()
    #                 val_rg = price - val_rg
    #                 if abs(val_rg) <= tolerance:
    #                     find_val = True
    #                     guess_result = rg
    #                 guess.add_guess_value(rg, val_rg)
    #             guess.print_values()
    #             if not find_val:
    #                 guess_list.extend(guess.find_lower_range(2))
    #         iterations += 1
    #         if find_val or iterations >= maxNumIterations:
    #             break
    #         guess_list = sort_reduce(guess_list, 2)
    #         print("cur guess_list:", iterations, guess_list[0].low, guess_list[0].high,
    #               guess_list[1].low, guess_list[1].high)
    #     return guess_result

    def strike_from_price(self, args):
        return None

    def floor_guess_price(self):
        return self.spotPx * 0.8

    def ceiling_guess_price(self):
        return self.spotPx * 1.2

    def dispose(self):
        pass


class McpVanillaCompound(McpBaseCompound):

    def __init__(self):
        self.vanillas = []
        self.buy_sells = []
        self.leverages = []
        # self.payoff_wrapper = None

    def price(self, price_method=None):
        price = 0.0
        pxs = []
        for i in range(len(self.vanillas)):
            fxv = self.vanillas[i]
            sub_price = fxv.price(price_method)
            # print("Leg", i, sub_price)
            pxs.append(sub_price)
            price += sub_price
        # print(price, ",", pxs)
        return price

    def Price(self, price_method=None, is_amount=True):
        return self.price(price_method)

    def greek_sum(self, name, *args):
        vf = 0.0
        for option in self.vanillas:
            if hasattr(option, name):
                vf = vf + getattr(option, name)(*args)
        return vf

    def Delta(self, *args):
        return self.greek_sum('Delta', *args)

    def Vega(self, *args):
        return self.greek_sum('Vega', *args)

    def Gamma(self, *args):
        return self.greek_sum('Gamma', *args)

    def Theta(self, *args):
        return self.greek_sum('Theta', *args)

    def Vanna(self, *args):
        return self.greek_sum('Vanna', *args)

    def Volga(self, *args):
        return self.greek_sum('Volga', *args)

    def Rho(self, *args):
        return self.greek_sum('Rho', *args)

    def ForwardDelta(self, *args):
        return self.greek_sum('ForwardDelta', *args)

    def delta(self, delta_rhs, price_method=None):
        vf = 0.0
        for option in self.vanillas:
            vf = vf + option.delta(delta_rhs, price_method)
        return vf

    def rho(self, is_demestic_ccy, price_method=None):
        vf = 0.0
        for option in self.vanillas:
            vf = vf + option.rho(is_demestic_ccy, price_method)
        return vf

    def gamma(self, price_method=None):
        vf = 0.0
        for option in self.vanillas:
            vf = vf + option.gamma(price_method)
        return vf

    def theta(self, price_method=None):
        vf = 0.0
        for option in self.vanillas:
            vf = vf + option.theta(price_method)
        return vf

    def vega(self, price_method=None):
        vf = 0.0
        for option in self.vanillas:
            vf = vf + option.vega(price_method)
        return vf

    def vanna(self):
        vf = 0.0
        for option in self.vanillas:
            vf = vf + option.vanna()
        return vf

    def volga(self):
        vf = 0.0
        for option in self.vanillas:
            vf = vf + option.volga()
        return vf

    def forward_delta(self, delta_rhs):
        vf = 0.0
        for option in self.vanillas:
            vf = vf + option.forward_delta(delta_rhs)
        return vf

    def legs(self):
        return [leg.get_field_dict() for leg in self.vanillas]

    def get_vol(self, vs, strike, expiry_date, side=MktDataSide.Mid):
        if not is_vol_surface(vs):
            raise Exception("Invalid VolatilitySurface: " + str(vs))
        # vol = vs.GetVolatility(strike, expiry_date, FXInterpolationType.STRIKE_INTERPOLATION)
        vol = vs.get_strike_vol(strike, expiry_date, side)
        return vol

    def get_rate(self, vs, expiry_date, side_acc=MktDataSide.Mid, side_und=MktDataSide.Mid):
        if not is_vol_surface(vs):
            raise Exception("Invalid VolatilitySurface: " + str(vs))
        acc_rate = vs.get_acc_rate(expiry_date, side_acc)
        und_rate = vs.get_und_rate(expiry_date, side_und)
        return acc_rate, und_rate

    def leg_payoff(self, value_date, spots, leg_num=0):
        leg_nums = []
        if leg_num <= 0 or leg_num > len(self.vanillas):
            leg_nums = range(len(self.vanillas))
        else:
            leg_nums = [leg_num - 1]
        payoffs = []
        for i in leg_nums:
            vanilla = self.vanillas[i]
            payoff = vanilla.payoff_by_spots(value_date, spots)
            payoffs.append(payoff)
        return payoffs

    def payoff2(self, value_date, spot=None, rg=0.03):
        # all_spots = set()
        # leg_args = []
        # for leg in self.vanillas:
        #     spots, pnls = leg.payoff2(value_date, spot, rg)
        #     leg_args.append((leg, spots, pnls))
        #     for item in spots:
        #         all_spots.add(item)
        # for leg, spots, pnls in leg_args:
        #     spot_set = set(spots)
        #     spot_not_cal
        return [], []

    def delta(self, delta_rhs, price_method=None):
        s = 0
        for leg in self.vanillas:
            s += leg.delta(delta_rhs, price_method)
        return s

    def rho(self, is_demestic_ccy, price_method=None):
        s = 0
        for leg in self.vanillas:
            s += leg.rho(is_demestic_ccy, price_method)
        return s

    def gamma(self, price_method=None):
        s = 0
        for leg in self.vanillas:
            s += leg.gamma(price_method)
        return s

    def theta(self, price_method=None):
        s = 0
        for leg in self.vanillas:
            s += leg.theta(price_method)
        return s

    def vega(self, price_method=None):
        s = 0
        for leg in self.vanillas:
            s += leg.vega(price_method)
        return s

    # def del_ref(self):
    #     if self.vanillas is not None:
    #         for leg in self.vanillas:
    #             leg.del_ref()
    #         self.vanillas.clear()
    #         del self.vanillas
    #     if self.payoff_wrapper is not None:
    #         del self.payoff_wrapper.spec
    #         del self.payoff_wrapper


class CfdItemLeg():

    def __init__(self, arg: str = None):
        self.cfd_item = None
        if arg is None:
            self.strike_names = []
            self.strikes_raw = []
            self.strike_name = ''
            self.is_leverage_args = False
            self.other_args = []
            self.buy_sell = BuySell.Buy
            self.leverage = 1
            self.is_leverage_args = False
            self.leg_type = 1
            self.call_put = CallPut.Call
            self.is_mid = False
            return
        args = arg.strip().split("@")
        args2 = args[0].split(",")
        if len(args2) == 2:
            self.is_mid = str(args2[1]).lower() == 'mid'
            ds = args2[0]
        else:
            self.is_mid = False
            ds = args[0]
        #mcp_logging.info(f"CfdItemLeg init: {ds}, is_mid={self.is_mid},  {args2}")
        ss = re.split("\\W+", ds.strip())
        pxs = re.split("\\W+", args[1].strip())
        self.strike_names = [str(item).lower() for item in pxs]
        self.strikes_raw = pxs
        self.strike_name = str(pxs[0]).lower()
        arg_lower = ds.lower()
        self.is_leverage_args = False
        self.other_args = []
        if arg_lower.find("vanilla") >= 0 or arg_lower.find("barrier") >= 0 or arg_lower.find(
                "european") >= 0 or arg_lower.find("american") >= 0 or arg_lower.find("asian") >= 0:
            if len(ss) == 3:
                self.buy_sell = buy_sell_internal(ss[0])
                self.leverage = 1
                raw_leg_type = ss[1].lower()
                self.leg_type = self.get_leg_type(raw_leg_type)
                self.call_put = call_put_internal(ss[2])
            elif len(ss) >= 4:
                self.buy_sell = buy_sell_internal(ss[0])
                # self.leverage = int(ss[1])
                self.leverage, self.is_leverage_args = self.parse_leverage(ss[1])
                raw_leg_type = ss[2].lower()
                self.leg_type = self.get_leg_type(raw_leg_type)
                self.call_put = call_put_internal(ss[3])
            else:
                raise Exception("Leg not enough parameters: " + arg)
            if arg_lower.find("asian") >= 0:
                self.leg_type = FwdDefConst.Dict_LegType["asian"]
                self.other_args = raw_leg_type.split('_')
                print("other_args:", self.other_args)
        elif arg_lower.find('cash') >= 0 or arg_lower.find('asset') >= 0:
            # EuropeanDigital
            if len(ss) == 2:
                self.buy_sell = buy_sell_internal(ss[0])
                self.leverage = 1
                self.leg_type = self.get_leg_type('EuropeanDigital')
                self.call_put = enum_wrapper.parse2(ss[1], 'DigitalType')
            elif len(ss) >= 3:
                self.buy_sell = buy_sell_internal(ss[0])
                self.leverage, self.is_leverage_args = self.parse_leverage(ss[1])
                self.leg_type = self.get_leg_type('EuropeanDigital')
                self.call_put = enum_wrapper.parse2(ss[2], 'DigitalType')
            else:
                print(f"Leg not enough parameters: {ss}, {arg}")
                raise Exception("Leg not enough parameters: " + arg)
        else:
            self.leg_type = 1
            if len(ss) == 2:
                self.buy_sell = buy_sell_internal(ss[0])
                self.leverage = 1
                self.leg_type, self.call_put = self.parse_call_put_fwd(ss[1], self.leg_type)
            elif len(ss) >= 3:
                self.buy_sell = buy_sell_internal(ss[0])
                self.leverage, self.is_leverage_args = self.parse_leverage(ss[1])
                self.leg_type, self.call_put = self.parse_call_put_fwd(ss[2], self.leg_type)
            else:
                raise Exception("Leg not enough parameters: " + arg)
        # print("GfdItemLeg:", self.leg_type, self.buy_sell, self.leverage, self.call_put, self.strike_name)

    def get_leg_type(self, leg_type):
        leg_type = str(leg_type).lower()
        if leg_type in FwdDefConst.Dict_LegType:
            return FwdDefConst.Dict_LegType[leg_type]
        else:
            return 0

    def parse_call_put_fwd(self, s: str, leg_type):
        if s.lower() == "outright":
            return 7, None
        else:
            return leg_type, call_put_internal(s)

    def parse_leverage(self, s):
        is_args = False
        try:
            lvg = float(s)
        except ValueError:
            is_args = True
            lvg = s
        return lvg, is_args


class CfdItem():

    def __init__(self, std_dict=None):
        if std_dict is None:
            self.key = ''
            self.buy_sell = mcp_const.Side_Buy
            self.is_client = False
            self.strikes = []
            self.lower_strikes = []
            self.legs = []
            self.arguments = []
            self.lower_args = []
            return
        # print(f"CfdItem std_dict: {std_dict}")
        self.key = std_dict[FwdDefConst.Field_PackageName]
        val_buy_sell = str(std_dict[FwdDefConst.Field_BuySell]).lower()
        if val_buy_sell.count('buy') > 0:
            self.buy_sell = mcp_const.Side_Buy
        else:
            self.buy_sell = mcp_const.Side_Sell
        # self.is_client = not val_buy_sell.count('bank') > 0
        self.is_client = val_buy_sell.count('client') > 0
        #mcp_logging.info(f"CfdItem init: {self.key}, {val_buy_sell}, {self.buy_sell}, is_client={self.is_client}")
        # self.buy_sell = buy_sell_internal(std_dict[FwdDefConst.Field_BuySell])
        self.strikes = str(std_dict[FwdDefConst.Field_Strikes]).split(",")
        self.strikes = [item.strip() for item in self.strikes]
        self.lower_strikes = [item.lower() for item in self.strikes]
        self.legs = self.parse_legs(std_dict[FwdDefConst.Field_ProductStructure])
        if FwdDefConst.Field_Arguments in std_dict:
            args_val = std_dict[FwdDefConst.Field_Arguments]
            if args_val is None or args_val == "":
                self.arguments = []
                self.lower_args = []
            else:
                self.arguments = str(args_val).split(",")
                self.lower_args = [item.lower() for item in self.arguments]
        else:
            self.arguments = []
            self.lower_args = []
        # print(f"CfdItem lower_args: {self.lower_args}")

    def parse_legs(self, arg: str):
        ss = arg.split("+")
        legs = [CfdItemLeg(item) for item in ss]
        for item in legs:
            item.cfd_item = self
        return legs


class CustomForwardDefine():

    def __init__(self):
        self.key = ""
        self.def_args = {}
        self.version = 0

    def parse(self, std_dicts):
        for std_dict in std_dicts:
            item = CfdItem(std_dict)
            self.key = item.key
            self.def_args[item.buy_sell] = item
        self.version += 1
        # print("GeneralForwardDefine add:", self.get_version(), item.buy_sell)

    def get_by_buy_sell(self, buy_sell):
        # buy_sell = buy_sell_internal(buy_sell)
        if buy_sell in self.def_args:
            return self.def_args[buy_sell]
        return None

    def get_version(self):
        return "%s@%s" % (self.key, self.version)


class CustomForwardRegister():

    def __init__(self):
        self.fwd_def_dict = {}
        self.def_listener_dict = {}

    def add(self, args_dicts):
        #print(f"CustomForwardRegister: {json.dumps(args_dicts)}")
        std_dicts = [lower_key_dict(args_dict) for args_dict in args_dicts]
        return self._add_fwd_def(std_dicts)

    def _add_fwd_def(self, std_dicts):
        if len(std_dicts) < 1:
            return "No custom forward define data"
        std_dict = std_dicts[0]
        key = std_dict[FwdDefConst.Field_PackageName]
        #print(f"CustomForwardRegister: {key}")
        if key not in self.fwd_def_dict:
            self.fwd_def_dict[key] = CustomForwardDefine()
        gfd: CustomForwardDefine = self.fwd_def_dict[key]
        gfd.parse(std_dicts)
        v = gfd.get_version()
        self.notify_def_changed(key, v)
        # print("GeneralForwardRegister add:", key)
        return v

    def get_fwd_def(self, key, buy_sell):
        fwd_def: CustomForwardDefine = self.fwd_def_dict[key]
        return fwd_def.get_by_buy_sell(buy_sell)

    def validate_args(self, args_dict):
        std_dict = lower_key_dict(args_dict)
        if FwdDefConst.Field_PackageName not in std_dict:
            raise Exception("Lack field: " + FwdDefConst.Field_PackageName)
        if FwdDefConst.Field_BuySell not in std_dict:
            raise Exception("Lack field: " + FwdDefConst.Field_BuySell)
        key = std_dict[FwdDefConst.Field_PackageName]
        key = key.split("@")[0]
        if key not in self.fwd_def_dict:
            raise Exception("Forward not define: " + key)
        fwd_def: CustomForwardDefine = self.fwd_def_dict[key]
        buy_sell = std_dict[FwdDefConst.Field_BuySell]
        gfd_item: CfdItem = fwd_def.get_by_buy_sell(buy_sell_internal(buy_sell))
        if gfd_item is None:
            raise Exception("Forward " + str(buy_sell) + " not define: " + key)
        lack_keys = []
        strikes = {}
        for i in range(len(gfd_item.lower_strikes)):
            item = gfd_item.lower_strikes[i]
            item_view = gfd_item.strikes[i]
            if item not in std_dict:
                lack_keys.append(item_view)
                strikes[item] = None
            else:
                strikes[item] = std_dict[item]
        for i in range(len(gfd_item.lower_args)):
            item = gfd_item.lower_args[i]
            item_view = gfd_item.arguments[i]
            if item not in std_dict:
                lack_keys.append(item_view)
                strikes[item] = None
            else:
                strikes[item] = std_dict[item]
        return key, lack_keys, strikes

    def parse_legs_spec_args(self, arr):
        if debug_args_info:
            print("parse_legs_spec_args:", arr)
        result = {}
        if arr is None or len(arr) == 0:
            return result
        # use_spec = str(arr[0][0]).lower() == "y"
        # if not use_spec:
        #     return result
        calc_target = None
        try:
            calc_target = enum_wrapper.parse2(arr[0][0], 'CalculateTarget')
        except:
            pass
        if calc_target is None or calc_target == CalculateTarget.NONE:
            return result
        leg_count = len(arr[0]) - 1
        for row_num in range(1, len(arr)):
            row = arr[row_num]
            field_name = str(row[0]).lower()
            for leg_num in range(leg_count):
                if leg_num not in result:
                    result[leg_num] = {}
                result[leg_num][field_name] = row[leg_num + 1]
        if debug_args_info:
            print("parse_legs_spec_args: result=", result)
        return result

    def parse_legs_spec_args2(self, raw_dict):
        result = {}
        # std_dict = lower_key_dict(raw_dict)
        for key in raw_dict:
            lower_key = key.lower()
            match = re.search(r'leg\d+', lower_key)
            if match is not None:
                group = match.group()
                leg_num = int(group.replace('leg', '')) - 1
                field_name = lower_key.replace(group, '')
                if leg_num not in result:
                    result[leg_num] = {}
                result[leg_num][field_name] = raw_dict[key]
                # print(f"parse_legs_spec_args2 match: {match}, {leg_num}, {field_name}")
        # print(f"parse_legs_spec_args2 result: {result}")
        return result

    def create_cache_result(self, key, buy_sell, strikes_dict, raw_result):
        keys = []
        keys.extend(raw_result["keys"])
        vals = []
        vals.extend(raw_result["vals"])
        d = {}
        raw_dict = raw_result["dict"]
        for item in raw_dict:
            d[item] = raw_dict[item]
        gfd_item: CfdItem = self.get_fwd_def(key, buy_sell)
        for i in range(len(gfd_item.lower_strikes)):
            item = gfd_item.lower_strikes[i]
            item_view = gfd_item.strikes[i]
            if item in strikes_dict:
                keys.append(item_view)
                v = strikes_dict[item]
                vals.append(v)
                d[item_view] = v

        return {
            "keys": keys,
            "vals": vals,
            "dict": d,
        }

    def add_def_listener(self, key, f):
        if key not in self.def_listener_dict:
            self.def_listener_dict[key] = []
        listeners: list = self.def_listener_dict[key]
        if listeners.count(f) == 0:
            listeners.append(f)
            if key in self.fwd_def_dict:
                gfd: CustomForwardDefine = self.fwd_def_dict[key]
                f(gfd.get_version())

    def remove_def_listener(self, key, f):
        if key in self.def_listener_dict:
            listeners: list = self.def_listener_dict[key]
            if listeners.count(f) > 0:
                listeners.remove(f)

    def notify_def_changed(self, key, data):
        if key in self.def_listener_dict:
            listeners: list = self.def_listener_dict[key]
            for f in listeners:
                f(data)


general_fwd_register = CustomForwardRegister()


class McpCustomForward(McpVanillaCompound):
    ins_count = 0
    del_count = 0

    # def __del__(self):
    #     # if self.volSurface is not None:
    #     try:
    #         if hasattr(self, "volSurface"):
    #             del self.volSurface
    #         if hasattr(self, "accCurve"):
    #             del self.accCurve
    #         if hasattr(self, "undCurve"):
    #             del self.undCurve
    #     except:
    #         pass
    #     if hasattr(self, "vanillas"):
    #         for leg in self.vanillas:
    #             try:
    #                 leg.del_ref()
    #             except:
    #                 pass
    #         self.vanillas.clear()
    #         del self.vanillas
    #     McpCustomForward.del_count += 1
    #     # if debug_del_info:
    #     #     print("McpCustomForward ins del: ", self._ins_id)
    #     print(
    #         f"CustomForward del: id={self._del_id}, ins={McpCustomForward.ins_count}, del={McpCustomForward.del_count}")

    # def __init__(self, key, buy_sell, strikes_dict, args: list):
    def __init__(self, *args):
        super().__init__()
        self.print_info = False
        # print(f"McpCustomForward args: {args}")
        McpCustomForward.ins_count += 1
        self._del_id = McpCustomForward.ins_count
        if debug_del_info:
            print("McpCustomForward ins new: ", self._del_id)

        # self.payoff_wrapper = PayoffWrapper(self, None, False, False)

        key = args[-3]
        strikes_dict = args[-2]
        buy_sell = args[2]
        self.amts = []

        self.leg_args = args[-1]

        self.key = key
        strikes_dict = lower_key_dict(strikes_dict)
        self.strikes_dict = strikes_dict
        self.args = args
        self.buy_sell = buy_sell

        self.referenceDate = args[0]
        self.spotPxStr = args[1]
        self.buySell = args[2]
        self.expiryDate = args[3]
        self.volSurface = args[4]
        self.settlementDate = args[5]
        self.priceSettlementDate = args[6]
        self.calendar = args[7]
        self.notional = args[8]
        self.legs_forward, self.legs_acc_rate, self.legs_und_rate, self.legs_vol = None, None, None, None

        if len(args) == 20:
            self.dayCounter = args[9]
            self.undDayCounter = args[10]
            legs_args = [self.legs_float_args(item) for item in args[11:15]]
            self.legs_forward, self.legs_acc_rate, self.legs_und_rate, self.legs_vol = tuple(legs_args)
            # print(f"legs_args: {legs_args}")
            self.accCurve = None
            self.undCurve = None
            self.calculatedTarget = enum_wrapper.parse2(args[15])
            self.pair = args[16]
        elif len(args) == 16:
            self.dayCounter = args[9]
            self.undDayCounter = args[10]
            self.accCurve = args[11]
            self.undCurve = args[12]
        else:
            logging.info(f"Invalid args length: {len(args)}, {args}")
            raise Exception(f"Invalid args length: {len(args)}")

        if self.undDayCounter == DayCounter.NONE:
            self.undDayCounter = self.dayCounter

        item: CfdItem = general_fwd_register.get_fwd_def(key, buy_sell)
        self.gfd_item = item

        self.strikes = [self.strikes_dict[key] for key in item.lower_strikes]
        spot_bid, spot_ask = self.parse_spot(self.spotPxStr)
        self.spotPx = (spot_bid + spot_ask) / 2

        day_counter = McpDayCounter(self.undDayCounter)
        # time_to_expiry = day_counter.YearFraction(self.referenceDate, self.expiryDate)
        time_to = day_counter.YearFraction(self.priceSettlementDate, self.settlementDate)

        for i in range(len(item.legs)):
            gfd_leg: CfdItemLeg = item.legs[i]
            leverage = gfd_leg.leverage
            if gfd_leg.is_leverage_args:
                leverage = strikes_dict[gfd_leg.leverage.lower()]
            strike = strikes_dict[gfd_leg.strike_name]
            # vol = self.get_vol(self.volSurface, strike, self.expiryDate)
            side_spot, side_acc, side_und, side_vol = ForwardUtils.bid_ask_sign(gfd_leg.buy_sell, gfd_leg.call_put,
                                                                                item.is_client, gfd_leg.is_mid)
            # print(f"len={i},", side_spot, side_acc, side_und, side_vol)
            spot_leg = self.leg_spot(side_spot, spot_bid, spot_ask)
            if isinstance(self.volSurface, McpFXVolSurface2):
                mkt_vol2: McpFXVolSurface2 = self.volSurface
                acc_rate = mkt_vol2.get_acc_rate(self.expiryDate, side_acc)
                und_rate = mkt_vol2.get_und_rate(self.expiryDate, side_und)
                forward = mkt_vol2.get_forward_rate(self.expiryDate, side_spot)
            else:
                acc_rate, und_rate = self.get_rate(self.volSurface, self.settlementDate, side_acc, side_und)
                forward = self.volSurface.get_forward_rate(self.settlementDate, side_spot)
                forward, und_rate = self.volSurface.calc_all(spot_leg, time_to, acc_rate, und_rate, forward)
            vol = self.get_vol(self.volSurface, strike, self.expiryDate, side_vol)
            # print("vol:",vol,"rates:",acc_rate,und_rate)
            vol, acc_rate, und_rate, forward, ul_vol, ul_acc_rate, ul_und_rate, ul_forward = self.use_leg_args(i, vol,
                                                                                                               acc_rate,
                                                                                                               und_rate,
                                                                                                               forward)
            # print(f"ul_vol: {ul_vol}, ul_forward: {ul_forward}")
            if not ul_vol and ul_forward:
                vol = self.volSurface.get_strike_vol(strike, self.expiryDate, side_vol, forward)
            # forward, und_rate = self.volSurface.calc_all(spot_leg, time_to, acc_rate, und_rate, forward)
            leg = None
            if 2 <= gfd_leg.leg_type <= 5:
                barrier = strikes_dict[gfd_leg.strike_names[1]]
                self.strikes.extend([
                    barrier,
                    barrier + FwdDefConst.Barrier_Offset,
                    barrier - FwdDefConst.Barrier_Offset
                ])
                # self.strikes.append(barrier - 0.00001)
                # self.strikes.append(barrier + 0.00001)
                rebate = 0.0
                pricing_method = PricingMethod.BLACKSCHOLES
                arg_leg = [gfd_leg.call_put, gfd_leg.leg_type, self.referenceDate, spot_leg,
                           gfd_leg.buy_sell, self.expiryDate, self.settlementDate, strike, barrier,
                           acc_rate, und_rate, vol, rebate, leverage * self.notional, pricing_method,
                           MAdjustmentTable(), False, self.calendar, self.dayCounter]
                leg = McpVanillaBarriers(*arg_leg)
            elif gfd_leg.leg_type == 7:
                fwd = self.get_leg_float_arg(i, FwdDefConst.Field_Forward)
                if fwd is None and self.legs_forward is not None:
                    fwd = self.legs_forward
                if fwd is None:
                    pricing_method = FxFwdPricingMethod.INTERESTPARITY
                    fwd = -1
                else:
                    pricing_method = FxFwdPricingMethod.MARKETFWD
                arg_leg = [strike, spot_leg, acc_rate, und_rate, fwd,
                           self.referenceDate, self.expiryDate, self.settlementDate,
                           self.calendar, self.dayCounter, pricing_method,
                           gfd_leg.buy_sell, leverage * self.notional]
                leg = McpFXForward(*arg_leg)
            elif 8 <= gfd_leg.leg_type <= 11:
                pricing_method = PricingMethod.BINOMIAL
                pricing_method = self.use_leg_pricing_method(i, pricing_method)
                avg_method, strike_type = self.get_asian_type(gfd_leg.leg_type)
                arg_leg = [gfd_leg.call_put, self.referenceDate, strike, spot_leg,
                           vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                           gfd_leg.buy_sell, avg_method, strike_type, pricing_method,
                           leverage * self.notional, 10, 10000, self.calendar, self.dayCounter,
                           self.priceSettlementDate]
                leg = McpAsianOption(*arg_leg)
            elif gfd_leg.leg_type == 12:
                pricing_method = PricingMethod.BLACKSCHOLES
                fixing_freq = enum_wrapper.parse2(gfd_leg.other_args[1], "Frequency")
                avg_method = enum_wrapper.parse2(gfd_leg.other_args[2], "AverageMethod")
                strike_type = enum_wrapper.parse2(gfd_leg.other_args[3], "StrikeType")
                arg_leg = [gfd_leg.call_put, self.referenceDate, spot_leg, spot_leg,
                           self.referenceDate, self.settlementDate, self.settlementDate,
                           strike, acc_rate, und_rate, vol,
                           self.referenceDate, fixing_freq, DateAdjusterRule.ModifiedFollowing,
                           True, False, True,
                           self.calendar, DayCounter.Act365Fixed, avg_method, strike_type,
                           pricing_method, gfd_leg.buy_sell, leverage * self.notional,
                           10, 100000]
                # print("custom McpAsianOption:",arg_leg)
                leg = McpAsianOption(*arg_leg)
            elif gfd_leg.leg_type == 13:
                barrier = strikes_dict[gfd_leg.strike_names[1]]
                payoff_arg = strikes_dict[gfd_leg.strike_names[2]]
                arg_leg = [
                    self.referenceDate,
                    gfd_leg.call_put,
                    gfd_leg.buy_sell,
                    spot_leg,
                    strike,
                    vol,
                    self.expiryDate,
                    self.settlementDate,
                    acc_rate,
                    und_rate,
                    leverage * self.notional,
                    self.priceSettlementDate,
                    payoff_arg,
                    self.calendar,
                    self.dayCounter,
                    barrier,
                    False,
                ]
                leg = McpEuropeanDigital(*arg_leg)
                barrier = leg.tn_points
                self.strikes.extend(leg.payoff_strikes())
            else:
                pricing_method = 1
                opt_type = 0
                if gfd_leg.leg_type == 6:
                    pricing_method = 2
                    opt_type = 1
                pricing_method = self.use_leg_pricing_method(i, pricing_method)
                if vol <= 0:
                    print(f"vol is not positive: {vol}, {self.expiryDate}")
                    # vol = 0.000001
                arg_leg = [
                    gfd_leg.call_put,
                    self.referenceDate,
                    spot_leg,
                    self.expiryDate,
                    self.settlementDate,
                    strike,
                    acc_rate,
                    und_rate,
                    forward,
                    vol,
                    self.priceSettlementDate,
                    self.calendar,
                    self.dayCounter,
                    opt_type,
                    pricing_method,
                    gfd_leg.buy_sell,
                    leverage * self.notional,
                    1000,
                    1,
                    self.calculatedTarget,
                    self.pair,
                    10000,
                    1,
                ]
                leg = McpVanillaOption(*arg_leg)
                forward = leg.GetForward()
                # leg.timeToExpiry = time_to
                # leg.forward = forward
            leg.timeToSettlement = time_to
            leg.forward = forward
            # print("General arg_leg:", arg_leg)
            self.vanillas.append(leg)
            self.amts.append(leverage * self.notional)
            # self.strikes.append(strike)

    # def del_ref(self):
    #     super().del_ref()

    def max_leg_amount(self):
        return max(self.amts)

    def pips(self):
        return ForwardUtils.premium_to_pips(self.max_leg_amount(), self.price())

    def legs_float_args(self, s):
        try:
            return float(s)
        except:
            return None

    def parse_spot(self, spot_px):
        s = str(spot_px)
        if s.count('/') > 0:
            ss = s.split('/')
            spot_bid = float(ss[0])
            spot_ask = float(ss[1])
        else:
            spot_bid = float(s)
            spot_ask = spot_bid
        return spot_bid, spot_ask

    def leg_spot(self, side_spot, spot_bid, spot_ask):
        if side_spot == MktDataSide.Bid:
            return spot_bid
        elif side_spot == MktDataSide.Ask:
            return spot_ask
        else:
            return (spot_bid + spot_ask) / 2

    def get_asian_type(self, leg_type):
        if leg_type == 8:
            avg_method = AverageMethod.Geometric
            strike_type = StrikeType.Fixed
        elif leg_type == 8:
            avg_method = AverageMethod.Arithmetic
            strike_type = StrikeType.Fixed
        elif leg_type == 9:
            avg_method = AverageMethod.Geometric
            strike_type = StrikeType.Floating
        elif leg_type == 10:
            avg_method = AverageMethod.Arithmetic
            strike_type = StrikeType.Floating
        return avg_method, strike_type

    def get_rate(self, vs, expiryDate, side_acc=MktDataSide.Mid, side_und=MktDataSide.Mid):
        if self.accCurve is not None and self.undCurve is not None:
            acc_rate = self.accCurve.ZeroRate(expiryDate)
            und_rate = self.undCurve.ZeroRate(expiryDate)
        else:
            acc_rate, und_rate = super().get_rate(vs, expiryDate, side_acc, side_und)
        return acc_rate, und_rate

    # def bid_ask_sign(self, buy_sell, call_put):
    #     if (buy_sell == mcp_const.Side_Buy and call_put == mcp_const.Call_Option) or (
    #             buy_sell == mcp_const.Side_Sell and call_put == mcp_const.Put_Option):
    #         side_spot = MktDataSide.Bid
    #         side_acc = MktDataSide.Bid
    #         side_und = MktDataSide.Ask
    #     else:
    #         side_spot = MktDataSide.Ask
    #         side_acc = MktDataSide.Ask
    #         side_und = MktDataSide.Bid
    #     if buy_sell == mcp_const.Side_Buy:
    #         side_vol = MktDataSide.Bid
    #     else:
    #         side_vol = MktDataSide.Ask
    #
    #     return side_spot, side_acc, side_und, side_vol

    # def get_rate2(self, vs, expiryDate, buy_sell, call_put):
    #     if self.accCurve is not None and self.undCurve is not None:
    #         acc_rate = self.accCurve.ZeroRate(expiryDate)
    #         und_rate = self.undCurve.ZeroRate(expiryDate)
    #     else:
    #         if call_put is None:
    #             side_acc = MktDataSide.Mid
    #             side_und = MktDataSide.Mid
    #         else:
    #             _, side_acc, side_und, _ = self.bid_ask_sign(buy_sell, call_put)
    #         acc_rate, und_rate = super().get_rate(vs, expiryDate, side_acc, side_und)
    #     return acc_rate, und_rate

    def leg_args_choose(self, leg, key, val_legs, val_calc):
        val = None
        val_use_leg = False
        if key in leg:
            try:
                val = float(leg[key])
                val_use_leg = True
            except:
                pass
        if val is None:
            val = val_legs
            val_use_leg = True
        if val is None:
            val = val_calc
            val_use_leg = False
        # print(f"leg_args_choose: {val}, {key}, legs={val_legs}, calc={val_calc}, leg={leg}")
        return val, val_use_leg

    def use_leg_args(self, i, vol, acc_rate, und_rate, forward):
        # legs_args = strikes_dict[FwdDefConst.Field_Legs_Args]
        legs_args = self.leg_args
        leg = {}
        if legs_args is not None:
            if i in legs_args:
                leg = legs_args[i]
        acc_rate, ul_acc_rate = self.leg_args_choose(leg, FwdDefConst.Field_AccRate, self.legs_acc_rate, acc_rate)
        und_rate, ul_und_rate = self.leg_args_choose(leg, FwdDefConst.Field_UndRate, self.legs_und_rate, und_rate)
        forward, ul_forward = self.leg_args_choose(leg, FwdDefConst.Field_Forward, self.legs_forward, forward)
        vol, ul_vol = self.leg_args_choose(leg, FwdDefConst.Field_Volatility, self.legs_vol, vol)
        return vol, acc_rate, und_rate, forward, ul_vol, ul_acc_rate, ul_und_rate, ul_forward
        # if FwdDefConst.Field_AccRate in leg:
        #     try:
        #         v = float(leg[FwdDefConst.Field_AccRate])
        #         acc_rate = v
        #     except:
        #         if self.legs_acc_rate is not None:
        #             acc_rate = self.legs_acc_rate
        # if FwdDefConst.Field_UndRate in leg:
        #     try:
        #         v = float(leg[FwdDefConst.Field_UndRate])
        #         und_rate = v
        #     except:
        #         if self.legs_und_rate is not None:
        #             und_rate = self.legs_und_rate
        # if FwdDefConst.Field_Volatility in leg:
        #     try:
        #         v = float(leg[FwdDefConst.Field_Volatility])
        #         vol = v
        #     except:
        #         if self.legs_vol is not None:
        #             vol = self.legs_vol
        # if FwdDefConst.Field_Forward in leg:
        #     try:
        #         v = float(leg[FwdDefConst.Field_Forward])
        #         forward = v
        #     except:
        #         if self.legs_forward is not None:
        #             forward = self.legs_forward

    def get_leg_float_arg(self, i, key):
        result = None
        # legs_args = strikes_dict[FwdDefConst.Field_Legs_Args]
        legs_args = self.leg_args
        if legs_args is not None:
            if i in legs_args:
                leg = legs_args[i]
                if key in leg:
                    try:
                        v = float(leg[key])
                        result = v
                    except:
                        pass
        return result

    def use_leg_pricing_method(self, i, pricing_method):
        # legs_args = strikes_dict[FwdDefConst.Field_Legs_Args]
        legs_args = self.leg_args
        if legs_args is not None:
            if i in legs_args:
                leg = legs_args[i]
                if FwdDefConst.Field_PricingMethod in leg:
                    pricing_method = enum_wrapper.parse2(leg[FwdDefConst.Field_PricingMethod])
        return pricing_method

    def payoff_strikes(self):
        return self.strikes

    def payoff_copy(self, value_date, spot):
        args_new = list(self.args)
        args_new[0] = value_date
        args_new[1] = spot
        args_new[6] = self.calendar.AddBusinessDays(value_date, 2)
        obj = McpCustomForward(*args_new)
        # print(f"payoff_copy:{spot}, {value_date}, {args_new[6]}, {obj.price()}, {args_new}")
        return obj
        # return McpCustomForward(self.key, self.buySell, self.strikes_dict, args_new)

    def copy(self, args, guess_strike):
        std_args = lower_key_dict(args)
        strikes_dict = {}
        for key in self.strikes_dict:
            strikes_dict[key] = self.strikes_dict[key]
        if ('cap seagull' in self.gfd_item.key.lower()):
            if ('strike1_2_gap' in std_args):
                strike1_2_gap = std_args['strike1_2_gap']
            else:
                strike1_2_gap = 5
            strikes_dict['strike3'] =  std_args[key]
            strikes_dict['strike2'] =  guess_strike
            strikes_dict['strike1'] =  guess_strike - strike1_2_gap/10000.0 
        else:
            for key in self.gfd_item.lower_strikes:
                if key in std_args:
                    strikes_dict[key] = std_args[key]
                else:
                    strikes_dict[key] = guess_strike
        args_new = list(self.args)
        args_new[-2] = strikes_dict
        return McpCustomForward(*args_new)
        # return McpCustomForward(self.key, self.buySell, strikes_dict, self.args)

    def copy2(self, spotPx, reference_date):
        # args = [reference_date, spotPx, self.buySell, self.expiryDate, self.volSurface, self.settlementDate,
        #         self.priceSettlementDate, self.calendar, self.notional]
        # return McpCustomForward(self.key, self.buySell, self.strikes_dict, args)
        return self.payoff_copy(reference_date, spotPx)

    def max_guess_strike(self, args):
        result = self.spotPx
        std_dict = lower_key_dict(args)
        for key in self.gfd_item.lower_strikes:
            if key in std_dict:
                result = max(result, std_dict[key])
        return result * 2

    def strike_from_price(self, args):
        std_args = lower_key_dict(args)
        if 'pips' in std_args:
            std_args[FieldName.Price.lower()] = ForwardUtils.pips_to_premium(self.max_leg_amount(), std_args['pips'])
        elif 'premium' in std_args:
            std_args[FieldName.Price.lower()] = std_args['premium']
        price = std_args[FieldName.Price.lower()]
        lower = self.floor_guess_price();
        lower_key = "lowerguess"
        if lower_key in std_args:
            lower = std_args[lower_key]
        upper = self.ceiling_guess_price()
        upper_key = "upperguess"
        if upper_key in std_args:
            upper = std_args[upper_key]
        guessResult = self.guess_strike(lower, upper, price, args)
        return guessResult


    def segull_strike_from_price(self, args):
        # Segull有三个strike，先根据最大的strike3的初始值，然后strike2，strike1=strike2-pipGaps 来算
        # 如果算不出来，则递增strike3，重新计算
        strike3_min = args['strike3_min']
        strike2_max = args['strike2_max']
        for pip in range(0,10000,100):
            strike3 = strike3_min + pip / 10000.0
            std_args = lower_key_dict(args)
            if 'pips' in std_args:
                std_args[FieldName.Price.lower()] = ForwardUtils.pips_to_premium(self.max_leg_amount(), std_args['pips'])
            elif 'premium' in std_args:
                std_args[FieldName.Price.lower()] = std_args['premium']
            price = std_args[FieldName.Price.lower()]
            lower = strike3 * 0.8 #self.floor_guess_price();
            lower_key = "lowerguess"
            if lower_key in std_args:
                lower = std_args[lower_key]
            upper = strike2_max #self.ceiling_guess_price()
            upper_key = "upperguess"
            if upper_key in std_args:
                upper = std_args[upper_key]
            args['strike3']  = strike3
            guessResult = self.guess_strike(lower, upper, price, args)
            if guessResult != None:
                break
        if guessResult != None:
            return f"{guessResult:.5f}/{strike3:.5f}"
        else:
            return "Cannot find root!"

    def prices(self, value_dates, spots, pricing_method=None):
        prices = []
        for date in value_dates:
            sub = []
            for spot in spots:
                # args = [item for item in self.args]
                args = list(self.args)
                # args[1] = spot
                args[3] = date
                strikes_dict = {}
                for key in self.strikes_dict:
                    strikes_dict[key] = self.strikes_dict[key]
                for key in self.gfd_item.lower_strikes:
                    strikes_dict[key] = spot
                # forward = McpCustomForward(self.key, self.buy_sell, strikes_dict, args)
                args[-2] = strikes_dict
                forward = McpCustomForward(*args)
                sub.append(forward.price())
                forward.del_ref()
            prices.append(sub)
        return prices

    def prices_from_strikes(self, strikes, pricing_method=None):
        prices = []
        for strike in strikes:
            fwd = self.copy({}, strike)
            prices.append(fwd.price())
            fwd.del_ref()
        return prices

    def implied_strikes(self, impl_args, value_dates, field, data):
        strikes = []
        field = str(field).lower()
        for date in value_dates:
            sub = []
            for leverage in data:
                args = [item for item in self.args]
                args[3] = date
                strikes_dict = {}
                for key in self.strikes_dict:
                    strikes_dict[key] = self.strikes_dict[key]
                strikes_dict[field] = leverage
                try:
                    # forward = McpCustomForward(self.key, self.buy_sell, strikes_dict, args)
                    args = list(self.args)
                    # args[1] = spot
                    args[3] = date
                    # forward = McpCustomForward(self.key, self.buy_sell, strikes_dict, args)
                    args[-2] = strikes_dict
                    forward = McpCustomForward(*args)
                    sub.append(forward.strike_from_price(impl_args))
                    forward.del_ref()
                except:
                    sub.append(0)
                    # traceback.print_exc()
            strikes.append(sub)
        return strikes


class McpPortfolio():
    def __init__(self, options):
        self.options = options

    def __del__(self):
        self.del_ref()
        if debug_del_info:
            print("pf del")

    def price(self, price_method=None):
        vf = 0.0
        for option in self.options:
            vf = vf + option.price(price_method)
        return vf

    def delta(self, delta_rhs, price_method=None):
        vf = 0.0
        for option in self.options:
            vf = vf + option.delta(delta_rhs, price_method)
        return vf

    def rho(self, is_demestic_ccy, price_method=None):
        vf = 0.0
        for option in self.options:
            vf = vf + option.rho(is_demestic_ccy, price_method)
        return vf

    def gamma(self, price_method=None):
        vf = 0.0
        for option in self.options:
            vf = vf + option.gamma(price_method)
        return vf

    def theta(self, price_method=None):
        vf = 0.0
        for option in self.options:
            vf = vf + option.theta(price_method)
        return vf

    def vega(self, price_method=None):
        vf = 0.0
        for option in self.options:
            vf = vf + option.vega(price_method)
        return vf

    def copy(self, spotPx, reference_date):
        noptions = []
        for option in self.options:
            if isinstance(option, McpCustomForward):
                noption = option.copy2(spotPx, reference_date)
            else:
                noption = option.copy(spotPx, reference_date)
            noptions.append(noption)
        return McpPortfolio(noptions)

    def del_ref(self):
        for opt in self.options:
            opt.del_ref()
        self.options.clear()
        del self.options

    def SpotLadder(self, spotPx, reference_date, changes, diff=False):
        columns = ['Rate', 'Price', 'Delta(L)', 'Delta(R)', 'Gamma', 'Vega', 'Theta', 'Rho(L)', 'Rho(R)']
        data = self.spot_ladder(spotPx, reference_date, changes, columns, diff)
        df = pd.DataFrame(data, columns=columns)
        df.insert(0, "Changes", changes)
        return df

    def spot_ladder(self, spotPx, reference_date, changes, columns, diff=False, price_method=None):
        values = []
        zero_row = self.spot_ladder_row(spotPx, reference_date, 0.0, columns, price_method)
        for change in changes:
            raw_row = self.spot_ladder_row(spotPx, reference_date, change, columns, price_method)
            if diff and abs(change) > 1e-15:
                row = []
                for i in range(len(zero_row)):
                    row.append(raw_row[i] - zero_row[i])
            else:
                row = raw_row
            values.append(row)
        return values

    def spot_ladder_row(self, spotPx, reference_date, change, columns, price_method):
        value_row = []
        sub_spot = spotPx * (1 + change)
        sub_portfolio = self.copy(sub_spot, reference_date)
        for column in columns:
            if column == 'Rate':
                value_row.append(sub_spot)
            elif column == 'Price':
                value_row.append(sub_portfolio.price(price_method))
                # value_row.append(0)
            elif column == 'Delta(L)':
                value_row.append(sub_portfolio.delta(False, price_method))
                # value_row.append(0)
            elif column == 'Delta(R)':
                value_row.append(sub_portfolio.delta(True, price_method))
                # value_row.append(0)
            elif column == 'Gamma':
                value_row.append(sub_portfolio.gamma(price_method))
                # value_row.append(0)
            elif column == 'Vega':
                value_row.append(sub_portfolio.vega(price_method))
                # value_row.append(0)
            elif column == 'Theta':
                value_row.append(sub_portfolio.theta(price_method))
                # value_row.append(0)
            elif column == 'Rho(L)':
                value_row.append(sub_portfolio.rho(False, price_method))
                # value_row.append(0)
            elif column == 'Rho(R)':
                value_row.append(sub_portfolio.rho(True, price_method))
                # value_row.append(0)
        # sub_portfolio.del_ref()
        return value_row
