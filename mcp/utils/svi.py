# import traceback
#
# import numpy as np
# import scipy
# import scipy as sp
# import scipy.optimize as opt
# from scipy.interpolate import interp2d, interp1d
#
# from mcp import mcp
# from mcp.utils.mcp_utils import mcp_dt
#
#
# def svi_2steps(iv, x, init_msigma, maxiter=10, exit=1e-12, verbose=True):
#     opt_rmse = 1
#
#     def svi_quasi(y, a, d, c):
#         return a + d * y + c * np.sqrt(np.square(y) + 1)
#
#     def svi_quasi_rmse(iv, y, a, d, c):
#         return np.sqrt(np.mean(np.square(svi_quasi(y, a, d, c) - iv)))
#
#     # 计算a,d,c
#     def calc_adc(iv, x, _m, _sigma):
#         y = (x - _m) / _sigma
#         s = max(_sigma, 1e-6)
#         bnd = ((0, 0, 0), (max(max(iv), 1e-6), 2 * np.sqrt(2) * s, 2 * np.sqrt(2) * s))
#         z = np.sqrt(np.square(y) + 1)
#
#         # 此处等价于坐标轴旋转45°，这样写运行更快
#         A = np.column_stack([np.ones(len(iv)), np.sqrt(2) / 2 * (y + z), np.sqrt(2) / 2 * (-y + z)])
#
#         a, d, c = opt.lsq_linear(A, iv, bnd, tol=1e-12, verbose=False).x
#         return a, np.sqrt(2) / 2 * (d - c), np.sqrt(2) / 2 * (d + c)
#
#     def opt_msigma(msigma):
#         _m, _sigma = msigma
#         _y = (x - _m) / _sigma
#         _a, _d, _c = calc_adc(iv, x, _m, _sigma)
#         return np.sum(np.square(_a + _d * _y + _c * np.sqrt(np.square(_y) + 1) - iv))
#
#     for i in range(1, maxiter + 1):
#         # a_star,d_star,c_star = calc_adc(iv,x,init_msigma)
#         m_star, sigma_star = opt.minimize(opt_msigma,
#                                           init_msigma,
#                                           method='Nelder-Mead',
#                                           bounds=((2 * min(min(x), 0), 2 * max(max(x), 0)), (1e-6, 1)),
#                                           # bounds=((2 * min(x.min(), 0), 2 * max(x.max(), 0)), (1e-6, 1)),
#                                           tol=1e-12).x
#
#         a_star, d_star, c_star = calc_adc(iv, x, m_star, sigma_star)
#         opt_rmse1 = svi_quasi_rmse(iv, (x - m_star) / sigma_star, a_star, d_star, c_star)
#         if verbose:
#             print(f"round {i}: RMSE={opt_rmse1} para={[a_star, d_star, c_star, m_star, sigma_star]}     ")
#         if i > 1 and opt_rmse - opt_rmse1 < exit:
#             break
#         opt_rmse = opt_rmse1
#         init_msigma = [m_star, sigma_star]
#
#     result = np.array([a_star, d_star, c_star, m_star, sigma_star, opt_rmse1])
#     if verbose:
#         print(f"\nfinished. params = {result[:5].round(10)}")
#     return result
#
#
# def quasi2raw(a, d, c, m, sigma):
#     return a, c / sigma, d / c, m, sigma
#
#
# def svi_raw(x, a, b, rho, m, sigma):
#     centered = x - m
#     return a + b * (rho * centered + np.sqrt(np.square(centered) + np.square(sigma)))
#
#
# def svi_quasi(x, a, d, c, m, sigma):
#     y = (x - m) / sigma
#     z = np.sqrt(np.square(y) + 1)
#     re = a + d * y + c * z
#     return re
#
#
# class svi_quasi_model:
#     def __init__(self, a, d, c, m, sigma):
#         self.a = a
#         self.d = d
#         self.c = c
#         self.m = m
#         self.sigma = sigma
#
#     def __call__(self, x):
#         return svi_quasi(x, self.a, self.d, self.c, self.m, self.sigma)
#
#
# def list_divide(list1, list2):
#     return [list1[i] / list2[i] for i in range(len(list1))]
#
#
# class MSurfaceVol:
#
#     def __init__(self, referenceDate, spot, callPut, buildMethod, maturityDates, strikes,
#                  riskFreeCurve: mcp.MYieldCurve, prices, dividendDates, dividends, termInterpType, dayCounter):
#         # lmax, lmin = 4.11, 2.84
#         lmin, lmax = min(strikes), max(strikes)
#         lin = np.linspace(lmin, lmax, 500)
#         self.day_counter = mcp.MDayCounter(dayCounter)
#         self.data = {}
#
#         dd_times = []
#         for d in dividendDates:
#             dd_times.append(self.day_counter.YearFraction(referenceDate, d))
#         und_rates_interp = interp1d(dd_times, dividends)
#
#         self.ref_date = referenceDate
#         data = []
#         times = []
#         rates = []
#         for i in range(len(maturityDates)):
#             t = self.day_counter.YearFraction(referenceDate, maturityDates[i])
#             times.append(t)
#             r = riskFreeCurve.ZeroRate(maturityDates[i])
#             rates.append(r)
#             strike_vols = []
#             und_rate = und_rates_interp(t)
#             und_rate = float(und_rate)
#             for j in range(len(strikes)):
#                 args = [callPut, spot, t, t, strikes[j], und_rate, r,
#                         prices[i][j], 0.1, 0.00001, 200]
#                 try:
#                     bs_vanilla = mcp.MBSVanilla()
#                     vol = bs_vanilla.VolImpliedFromPrice(*args)
#                     strike_vols.append(vol)
#                 except:
#                     print("bs_vanilla VolImpliedFromPrice except:", args)
#                     traceback.print_exc()
#             # print(maturityDates[i], "strike:", strikes)
#             # print(maturityDates[i], "strike_vols:", strike_vols)
#             a, d, c, m, sigma, rmse = svi_2steps(strike_vols, strikes, [0.05, 0.1], 10)
#             res = (a, d, c, m, sigma)
#             model = svi_quasi_model(*res)
#             model_lin = model(lin)
#             data.append(model_lin)
#             # print(maturityDates[i], "lin:", list(lin))
#             # print(maturityDates[i], "model_lin:", list(model_lin))
#             std_date = mcp_dt.pure_digit(maturityDates[i])
#             self.data[std_date] = {
#                 "lin": list(lin),
#                 "model_lin": list(model_lin),
#                 "strikes": list(strikes),
#                 "strike_vols": list(strike_vols),
#             }
#         print("times:", times)
#         print("rates:", rates)
#         self.f = interp2d(lin, times, data)
#
#     def GetVolatility(self, strike, date, type=None):
#         t = self.day_counter.YearFraction(self.ref_date, date)
#         val = self.f(strike, t)[0]
#         print("GetVolatility: time=", t, ", strike=", strike, ", val=", val, "dates=", [self.ref_date, date])
#         return val
#
#     def get_data(self, date):
#         std_date = mcp_dt.pure_digit(date)
#         if std_date in self.data:
#             obj = self.data[std_date]
#             return obj
#         return None


class MSurfaceVol:

    def __init__(self, *args):
        pass

    def GetVolatility(self, strike, date, type=None):
        return None

    def get_data(self, date):
        return None
