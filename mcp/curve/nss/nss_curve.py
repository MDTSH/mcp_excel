from .bcalc import *
from mcp.utils.enums import ParametricCurveModel


class McpParameterCurve:

    def __init__(self, reference_date, maturity_dates, ylds, model=ParametricCurveModel.NS):
        self.maturity = maturity_dates
        self.yld = ylds
        self.model = model
        self.reference_date = reference_date
        df = pd.DataFrame({
            'MaturityDates': self.maturity,
            'Rates': self.yld
        })
        df = df.sort_values(by=['MaturityDates'])
        args = {
            'ReferenceDate': self.reference_date.strftime('%Y-%m-%d'),
            'MaturityDates': [dt.strftime('%Y-%m-%d') for dt in df['MaturityDates']],
            'Rates': df['Rates'].tolist(),
            'ParamCurveModel': self.model,
        }
        print(args)
        self.wrapper = McpParametricCurve(args)

    def Ytm(self, dates):
        return [self.wrapper.ZeroRate(date.strftime('%Y-%m-%d')) for date in dates]

    def ytm_tenors(self, tenors):
        cal = McpCalendar()
        vdate = self.reference_date.strftime('%Y-%m-%d')
        dates = [cal.AddPeriod(vdate, tenor) for tenor in tenors]
        ylds = [self.wrapper.ZeroRate(dt) for dt in dates]
        return dates, ylds

    def X(self):
        return self.maturity

    def Y(self):
        return self.yld


class McpNssCurve(ParameterCurve):

    def __init__(self, reference_date, df, fields=['MaturityDates', 'Rates']):
        df = df.copy()
        df[fields[0]] = pd.to_datetime(df[fields[0]])
        super().__init__(reference_date, df[fields[0]], df[fields[1]])
        self.reference_date = reference_date
        self.df = df
        self.fields = fields

    def to_json(self):
        mcp_args = [
            ['ReferenceDate', self.reference_date.strftime('%Y-%m-%d')],
            ['MaturityDates', json.dumps(self.df[self.fields[0]].dt.strftime('%Y-%m-%d').tolist())],
            ['Rates', json.dumps(self.df[self.fields[1]].tolist())],
            ['ParamCurveModel', 'NS'],
            ['DayCounter', 'Act365Fixed'],
        ]
        obj = {
            "mcp_name": 'McpNssCurve',
            "mcp_args": mcp_args,
        }
        return json.dumps(obj)

    def ytm(self, dates):
        return super().Ytm(dates)

    @staticmethod
    def from_json(s):
        obj = json.loads(s)
        mcp_args = obj['mcp_args']
        reference_date = pd.to_datetime(mcp_args[0][1])
        df = pd.DataFrame({
            'MaturityDates': pd.to_datetime(json.loads(mcp_args[1][1])),
            'Rates': json.loads(mcp_args[2][1]),
        })
        return McpNssCurve(reference_date, df)
