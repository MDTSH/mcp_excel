import re
import time

from mdp.ws.quote_client import md_client

# ATM,25DC,25DP，10DC,10DP,25DR,25DB,10DR,10DB

# mp_callback {'0': 'GBPCNY.FXS.FR007.3Y', 'TRADE_DATE': '2021-04-27', 'GN_TXT16_2': 'CNY', 'IMP_VOLT': 0.3869, 'INTRST_RTE': 2.7716, 'SWAP_SPRD': 6695.95, 'DATE_VALID': '2021-04-27', 'EXCHCODE': 'cfx', 'UN_SYMBOL': 'GBP.CNY', 'TENOR': '3Y', 'SPOT_PRICE': 9.0202, 'DOMAINTYPE': 'MarketPrice', 'DSPLY_NAME': 'GBPCNY.FXS.FR007.3Y'}
# mp_callback image {'is_image': False, 'Data': {'0': 'GBPCNY.FXS.FR007.3Y', 'TRADE_DATE': '2021-04-27', 'GN_TXT16_2': 'CNY', 'IMP_VOLT': 0.3869, 'INTRST_RTE': 2.7716, 'SWAP_SPRD': 6695.95, 'DATE_VALID': '2021-04-27', 'EXCHCODE': 'cfx', 'UN_SYMBOL': 'GBP.CNY', 'TENOR': '3Y', 'SPOT_PRICE': 9.0202, 'DOMAINTYPE': 'MarketPrice', 'DSPLY_NAME': 'GBPCNY.FXS.FR007.3Y'}, 'BidList': [], 'AskList': [], 'AllList': []}

default_tenors = ["1D", "1W", "2W", "3W", "1M", "2M", "3M", "6M", "9M", "1Y", "18M", "2Y", "3Y"]
# default_tenors = ["1D"]
default_pairs = ["USDCNY"]
default_vol_types = ["ATM", "25DB", "10DB", "25DR", "10DR"]
default_rate_types = ["FR007", "Shibor3M", "Shibor"]


def std_pair(pair):
    return re.sub("\\W", "", pair)


class MdpDataWrapper():

    def __init__(self):
        self.data_dict = {}

    def init_data(self):
        for pair in default_pairs:
            for vt in default_vol_types:
                for tenor in default_tenors:
                    topic = pair + "." + vt + "." + tenor
                    md_client.subscribeMarketPrice(topic, self.mp_vol_callback)
            for rt in default_rate_types:
                for tenor in default_tenors:
                    topic = pair + ".FXS." + rt + "." + tenor
                    md_client.subscribeMarketPrice(topic, self.mp_rate_callback)

    def get_default_tenors(self):
        return default_tenors;

    def vol_by_type(self, pair, vol_type):
        item = self.get_item(pair, vol_type)
        print("vol_by_type", pair, vol_type, item)
        mid_list = []
        for tenor in default_tenors:
            v = 0
            if tenor in item:
                v = item[tenor]["MID_IV"]
            mid_list.append(v)
        return {
            "MID_IV": mid_list,
            "DATE_VALID": item["DATE_VALID"],
            "TIME_VALID": item["TIME_VALID"],
        }

    def rate_by_type(self, pair, rate_type):
        item = self.get_item(pair, rate_type)
        print("rate_by_type", pair, rate_type, item)
        vol_list = []
        rate_list = []
        for tenor in default_tenors:
            if tenor in item:
                vol_list.append(item[tenor]["IMP_VOLT"])
                rate_list.append(item[tenor]["INTRST_RTE"])
            else:
                vol_list.append(0)
                rate_list.append(0)
        return {
            "IMP_VOLT": vol_list,
            "INTRST_RTE": rate_list,
            "DATE_VALID": item["DATE_VALID"],
            # "TIME_VALID": item["TIME_VALID"],
            "SPOT_PRICE": item["SPOT_PRICE"],
        }

    def get_item(self, pair, t):
        if pair not in self.data_dict:
            self.data_dict[pair] = {}
        pair_item = self.data_dict[pair]
        item = None
        if t not in pair_item:
            item = {}
            pair_item[t] = item
            item["DATE_VALID"] = ""
            item["TIME_VALID"] = ""
            item["SPOT_PRICE"] = ""
        item = pair_item[t]
        return item

    def mp_rate_callback(self, data):
        image = md_client.getCacheImage(data)
        data = image["Data"]
        pair: str = std_pair(data["UN_SYMBOL"])
        tenor: str = data["TENOR"]
        rt: str = data["DSPLY_NAME"]
        topics = rt.split(".")
        rt = topics[2]

        item = self.get_item(pair, rt)
        item["DATE_VALID"] = data["DATE_VALID"]
        # item["TIME_VALID"] = data["TIME_VALID"]
        item["SPOT_PRICE"] = data["SPOT_PRICE"]
        item[tenor] = {
            "IMP_VOLT": data["IMP_VOLT"],
            "INTRST_RTE": data["INTRST_RTE"]
        }
        # print("rate:", data)

    def mp_vol_callback(self, data):
        image = md_client.getCacheImage(data)
        data = image["Data"]
        pair: str = std_pair(data["UN_SYMBOL"])
        tenor: str = data["TENOR"]
        vt: str = data["DSPLY_NAME"]
        topics = vt.split(".")
        vt = topics[1]

        item = self.get_item(pair, vt)
        item["DATE_VALID"] = data["DATE_VALID"]
        item["TIME_VALID"] = data["TIME_VALID"]
        item[tenor] = {
            "BID": data["BID"],
            "ASK": data["ASK"],
            "MID_IV": data["MID_IV"],
        }
        # print("vol:", data)


mdp_data_wrapper = MdpDataWrapper()
mdp_data_wrapper.init_data()

# time.sleep(2)
#
# vols = mdp_data_wrapper.vol_by_type("USDCNY", "ATM")
# print("ATM", vols)
# vols = mdp_data_wrapper.vol_by_type("USDCNY", "10DR")
# print("10DR", vols)
# rates = mdp_data_wrapper.rate_by_type("USDCNY", "Shibor3M")
# print("Shibor3M", rates)
# rates = mdp_data_wrapper.rate_by_type("USDCNY", "Shibor")
# print("Shibor", rates)
