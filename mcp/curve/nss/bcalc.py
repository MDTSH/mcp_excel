import argparse
import sys
# from errors import Error
import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta

from scipy.optimize import minimize
from sklearn.metrics import mean_squared_error
from mcp.tools import *
from mcp.tools import McpBondPricer as mcp, InsFixedRateBond, McpPortfolio

from multipledispatch import dispatch


def nelson_siegel_svensson(points, b0, b1, b2, b3, tau, tau2):
    """
    Function that calculate the rates for a serie of points using the 
    Nelson-Siegel-Svensson's model.
    
    Parameters
    ----------
    points : list
        A list that include the times in years to calculate the rates. 
    b0, b1, b2, b3, tau, tau2: float
        Parameters that fit the points with the curve.
    Returns
    -------
    ndarray
        Array with the rates for the times t in the array called points.

    """
    points = np.array(points)
    part1 = b0 + b1 * (1 - np.exp(-points / tau)) / (points / tau)
    part2 = b2 * ((1 - np.exp(-points / tau) / (points / tau)) - np.exp(-points / tau))
    part3 = b3 * ((1 - np.exp(-points / tau2) / (points / tau2)) - np.exp(-points / tau2))
    return part1 + part2 + part3


def optimization_nss(params, points, y):
    """
    Function to optimize the parameters of the Nelson-Siegel-Svensson model.
    
    Parameters
    ----------
    params : list
        Parameters to optimize (b0, b1, b2, b3, tau, tau2)
    points : list
        A list with the initial times in years to fit the curve.
    y : list
        A list with the rates that correspond to each time in the list of points.

    Returns
    -------
    float
        Root mean square error of the real rates with the calculated using 
        the Nelson-Siegel-Svensson model.

    """
    points = np.array(points)
    y_pred = nelson_siegel_svensson(points, params[0], params[1],
                                    params[2], params[3], params[4],
                                    params[5])
    return mean_squared_error(y, y_pred)


def fitNelsonSiegelYld(t, yld, x):
    """
    Function to return Nelson-Siegel-Svensson model result, using t/yld.
    
    Parameters
    ----------
    t : list
        输入的期限，年记的时间, float类型
    yld : list
        收益率，float类型
    x : list
        输入的期限，年记的时间，float类型
        
    Returns
    -------
    list
        模型返回的收益率（yield）

    """
    resutls_nss = minimize(optimization_nss,
                           np.array([0, 0, 0, 0, 1, 1]),
                           (t, yld),
                           bounds=((0, np.inf), (-np.inf, np.inf), (-np.inf, np.inf), (-np.inf, np.inf), (0, np.inf),
                                   (0.0001, np.inf)))
    return nelson_siegel_svensson(x, *resutls_nss.x)


class ParameterCurve:
    """
    构造参数曲线
    
    Parameters
    ----------
    valuation_date : date
        交易日
    instrument_df ： DataFrame[Code', 'Maturity', 'Coupon', 'ClosePx']
        债券信息和价格

    """

    def __init__(self, valuation_date, maturity_dates, ylds):
        self.valuation_date = pd.to_datetime(valuation_date)
        # if type(self.valuation_date) != date:
        #     self.valuation_date = self.valuation_date.date()
        # self.maturity = list(instrument_df['MaturityDates'].dt.date)
        # self.yld = instrument_df['Rates'].tolist()
        self.maturity = pd.to_datetime(maturity_dates).tolist()
        self.yld = pd.Series(ylds).tolist()
        t = [(date - self.valuation_date).days / 365 for date in self.maturity]
        self.d = []
        self.nss_args = minimize(optimization_nss, np.array([0, 0, 0, 0, 1, 1]),
                                 (t,
                                  self.yld),
                                 bounds=(
                                     (0, np.inf), (-np.inf, np.inf), (-np.inf, np.inf), (-np.inf, np.inf),
                                     (0, np.inf),
                                     (0.0001, np.inf)))

    def ytm_tenors(self, tenors):
        cal = McpCalendar()
        vdate = self.valuation_date.strftime('%Y-%m-%d')
        dates = pd.to_datetime([cal.AddPeriod(vdate, tenor) for tenor in tenors])
        return dates, self.Ytm(dates)

    def Ytm(self, dates):
        x = []
        dates = pd.to_datetime(dates)
        for d in dates:
            x.append((d - self.valuation_date).days / 365)
        return nelson_siegel_svensson(x, *self.nss_args.x)

    def X(self):
        return self.maturity

    def Y(self):
        return self.yld

    def duration(self):
        return self.d

    def getHandler(self):
        return self


class bond:
    def __init__(self):
        pass

    def bondc(face, coupon, maturity, discount):
        discounted_final_cf = (face + (coupon * face)) / (1 + discount) ** maturity
        dmac = discounted_final_cf * maturity
        maturity -= 1
        discounted_cf = 0

        while maturity > 0:
            discounted_cf = (coupon * face) + (discounted_cf / (1 + discount) ** maturity)
            dmac = dmac + discounted_cf
            maturity -= 1

        price = discounted_cf + discounted_final_cf
        dmac = dmac / price
        dmod = dmac / (1 + discount)

        mv = price / 100 * face

        #      price, dmac, dmod, Dol Dura,  DV01
        return price, dmac, dmod, mv * dmod, ((mv * dmod) * 0.01)

    def ytm(ValuationDate, MaturityDate, Coupon, CleanPrice):
        if type(ValuationDate) == str:
            ValuationDate = datetime.strptime(ValuationDate, '%Y-%m-%d').date()
        if type(MaturityDate) == str:
            MaturityDate = datetime.strptime(MaturityDate, '%Y-%m-%d').date()
        bond = McpFixedRateBond({
            "ValuationDate": ValuationDate,
            "MaturityDate": MaturityDate,
            "Coupon": Coupon,
        })
        return bond.YieldFromCleanPriceCHN(CleanPrice, False)

    # FrbDirericeFromYieldCHN(BondObject,Yield,isCompounding)
    def price(coupon, maturity):
        return bond.bondc(100, coupon, maturity, 0.0)[0];

    def clean_price(ValuationDate, MaturityDate, Coupon, Yield):
        if type(ValuationDate) == str:
            ValuationDate = datetime.strptime(ValuationDate, '%Y-%m-%d').date()
        if type(MaturityDate) == str:
            MaturityDate = datetime.strptime(MaturityDate, '%Y-%m-%d').date()
        bond = McpFixedRateBond({
            "ValuationDate": ValuationDate,
            "MaturityDate": MaturityDate,
            "Coupon": Coupon,
        })
        return bond.CleanPriceFromYieldCHN(Yield, True, True)

    def dirty_price1(ValuationDate, MaturityDate, Coupon, Yield):
        if type(ValuationDate) == str:
            ValuationDate = datetime.strptime(ValuationDate, '%Y-%m-%d').date()
        if type(MaturityDate) == str:
            MaturityDate = datetime.strptime(MaturityDate, '%Y-%m-%d').date()
        bond = McpFixedRateBond({
            "ValuationDate": ValuationDate,
            "MaturityDate": MaturityDate,
            "Coupon": Coupon,
        })
        return bond.DirtyPriceFromYieldCHN(Yield, True)

    # 根据净价计算全价
    def dirty_price(ValuationDate, MaturityDate, Coupon, CleanPrice):
        if type(ValuationDate) == str:
            ValuationDate = datetime.strptime(ValuationDate, '%Y-%m-%d').date()
        if type(MaturityDate) == str:
            MaturityDate = datetime.strptime(MaturityDate, '%Y-%m-%d').date()
        bond = McpFixedRateBond({
            "ValuationDate": ValuationDate,
            "MaturityDate": MaturityDate,
            "Coupon": Coupon,
        })
        yld = bond.YieldFromCleanPriceCHN(CleanPrice, False)
        return bond.DirtyPriceFromYieldCHN(yld, True)

    # FrbDurationCHN(BondObject,Yield)
    @dispatch(int, object)
    def duration(coupon, maturity):
        return bond.bondc(100, coupon, maturity, 0.0)[1];

    @dispatch(object, object, float, float)
    def duration(ValuationDate, MaturityDate, Coupon, CleanPrice):
        if type(ValuationDate) == str:
            ValuationDate = datetime.strptime(ValuationDate, '%Y-%m-%d').date()
        if type(MaturityDate) == str:
            MaturityDate = datetime.strptime(MaturityDate, '%Y-%m-%d').date()
        bond = McpFixedRateBond({
            "ValuationDate": ValuationDate,
            "MaturityDate": MaturityDate,
            "Coupon": Coupon,
        })
        yld = bond.YieldFromCleanPriceCHN(CleanPrice, False)

        return bond.DurationCHN(yld)

    # FrbMDurationCHN(CBondObject,Yield)
    @dispatch(float, object)
    def dmad(coupon, maturity):
        return bond.bondc(100, coupon, maturity, 0.0)[2];

    # FrbPVBPCHN(CBondObject,Yield)
    @dispatch(float, object)
    def dv01(coupon, maturity):
        return bond.bondc(100, coupon, maturity, 0.0)[4];

    @dispatch(object, object, float, float)
    def dv01(ValuationDate, MaturityDate, Coupon, CleanPrice):
        if type(ValuationDate) == str:
            ValuationDate = datetime.strptime(ValuationDate, '%Y-%m-%d').date()
        if type(MaturityDate) == str:
            MaturityDate = datetime.strptime(MaturityDate, '%Y-%m-%d').date()
        bond = McpFixedRateBond({
            "ValuationDate": ValuationDate,
            "MaturityDate": MaturityDate,
            "Coupon": Coupon,
        })
        yld = bond.YieldFromCleanPriceCHN(CleanPrice, False)

        return bond.PVBPCHN(yld)

    def fitNelsonSiegel(valuation_date, instruments_df):
        return ParameterCurve(valuation_date, instruments_df)

    def fNelsonSiegel(valuation_date, maturities, coupons, prices):
        instruments_df = pd.DataFrame()
        instruments_df['Maturity'] = maturities
        instruments_df['Coupon'] = coupons
        instruments_df['ClosePx'] = prices
        return ParameterCurve(valuation_date, instruments_df)


class Indicator:

    # def __init__(self, data):
    #     self.data = np.array(data[0])
    #     self.df = data[0]
    def final_value(ts):
        return ts[-1]

    def MaxDrawdown(ts):
        index_j = np.argmax(np.maximum.accumulate(ts) - ts)  # 结束位置
        if index_j == 0:
            return 0
        index_i = np.argmax(ts[:index_j])  # 开始位置
        d = (ts[index_i] - ts[index_j])  # 最大回撤
        return d

    def MaxProfit(ts):
        index_j = np.argmax(ts - np.minimum.accumulate(ts))  # 结束位置
        if index_j == 0:
            return 0
        index_i = np.argmin(ts[:index_j])  # 开始位置
        d = (ts[index_j] - ts[index_i])  # 最大赢率
        return d

    def StdDev(ts):
        stdp = np.std(np.maximum.accumulate(ts))
        return stdp

    def Average(ts):
        return np.mean(ts)

    def Median(ts):
        return np.median(ts[~np.isnan(ts)])

    def Range(ts):
        return np.max(ts) - np.min(ts)

    def sharpe_ratio(ts, days=1):
        '''夏普比率'''
        # returns = ts.shift(1) - ts.shift(0)  # 每日收益
        ts = ts / days * 252
        # returns = ts.shift(0) - ts.shift(1)
        returns = ts
        average_return = np.mean(returns)
        return_stdev = np.std(returns)

        return (average_return - 0.02) / return_stdev

        # rf=0.02
        # rf_daily=(1+rf)**(1/365)-1
        # sr_daily=(average_return-rf_daily)/return_stdev
        # sr_annual=sr_daily* np.sqrt(252)
        # return sr_annual

        # AnnualRet = average_return * 252  # 默认252个工作日
        # AnnualVol = return_stdev * np.sqrt(252)
        # sharpe_ratio = (AnnualRet - 0.02) / AnnualVol  # 默认无风险利率为0.02
        # return (sharpe_ratio)

    def to_percent(f, fmt=None):
        return round(f * 100, 2)

    def StrategyResult(self, strategyPnls, strategyTitles, days=1):
        strategy_df = pd.DataFrame(
            columns=['MaxDrawndown', 'MaxProfit', 'SharpeRatio', 'Mean', 'Median', 'Range', "Year", 'Profit',
                     "Annual"])
        i = 0
        title_df = pd.DataFrame(strategyTitles)
        # print("title_df:\n", title_df)
        for row in strategyPnls:
            dates = row['Date']
            years = (dates[len(dates) - 1] - dates[0]).days / 365
            cumpnls = row['cumpnl']
            profit = cumpnls[len(cumpnls) - 1]
            annual_return = profit / years
            strategy_df.loc[len(strategy_df.index)] = [
                # strategyTitles[i],
                self.to_percent(self.MaxDrawdown(row['cumpnl']), '.2%'),
                self.to_percent(self.MaxProfit(row['cumpnl']), '.2%'),
                self.sharpe_ratio(row['pnl'], days),
                self.to_percent(self.Average(row['cumpnl']), '.2%'),
                self.to_percent(self.Median(row['cumpnl']), '.2%'),
                self.to_percent(self.Range(row['cumpnl']), '.2%'),
                format(years, '.2f'),
                self.to_percent(profit, '.2%'),
                self.to_percent(annual_return, '.2%'),
            ]
            i = i + 1
        # print("strategy_df:\n", strategy_df)
        return title_df.merge(strategy_df, left_index=True, right_index=True)
        # return strategy_df

    def ResultStatistics(self, df, fields):
        funcs = [
            ("average", np.average),
            ("std", np.std),
            ("max", np.max),
            ("min", np.min),
        ]
        d = {"field": fields}
        for key, func in funcs:
            d[key] = [round(func(df[field]), 2) for field in fields]
        return pd.DataFrame(d)
