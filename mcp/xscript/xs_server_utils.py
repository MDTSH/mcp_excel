import json
from pyxll import _log

from mcp.utils.mcp_utils import mcp_dt
from mcp.xscript.structure import SttStructure, McpStructureDef
from mcp.xscript.utils import SttUtils


class XsSvrUtils:
    @staticmethod
    def parse_xs_params(packageName, basis, params, structure_def: McpStructureDef):

        req_dic = {}
        param_dic = XsSvrUtils.parse_item(params)
        _log.info(f"parse_xs_params begin:{param_dic}")
        basis_dic = XsSvrUtils.parse_item(basis)
        if 'ReferenceDate' in basis_dic:
            param_value = basis_dic['ReferenceDate']
            if isinstance(param_value, float):
                date_value = mcp_dt.parse_excel_date(float(param_value)).strftime('%Y-%m-%d')
            else:
                date_value = basis_dic['ReferenceDate']
            basis_dic['ReferenceDate'] = date_value
        _log.info(f"parse_xs_params begin2:{basis_dic}")
        structure: SttStructure = structure_def.structure
        dates = structure.dates
        dates_list = []
        for date in dates:
            for param_key, param_value in param_dic.items():
                _log.info(f"parse_xs_params begin12:{date}, {param_key}, {param_value}")
                if param_key == date:
                    date_value = param_value
                    if isinstance(param_value, float):
                        date_value = mcp_dt.parse_excel_date(float(param_value)).strftime('%Y-%m-%d')
                    dates_dic = {'Key': date, 'Value': date_value}
                    dates_list.append(dates_dic)
                    break
        if len(dates_list) > 0:
            basis_dic['Dates'] = dates_list
        strikes = structure.strikes
        strikes_list = []
        for strike in strikes:
            for param_key, param_value in param_dic.items():
                if param_key == strike:
                    strikes_dic = {'Key': strike, 'StrikePx': param_value}
                    strikes_list.append(strikes_dic)
                    break
        arguments = structure.arguments
        arg_list = []
        for argument in arguments:
            for param_key, param_value in param_dic.items():
                if param_key == argument:
                    arguments_dic = {'Key': argument, 'Value': param_value}
                    arg_list.append(arguments_dic)
                    break
        schedules = structure_def.schedules
        schedules_list = []
        for schedule in schedules:
            schedules_dic = {}
            for field in schedule.fields:
                for param_key, param_value in param_dic.items():
                    if param_key == f"{schedule.name}/{field.field}":
                        is_date = False
                        for date_item in dates:
                            if field.field == date_item:
                                is_date = True
                        real_value = param_value
                        if is_date:
                            if isinstance(param_value, float):
                                real_value = mcp_dt.parse_excel_date(float(param_value)).strftime('%Y-%m-%d')
                        field_dic = {'Key': param_key, 'Value': real_value}
                        schedules_dic[field.field] = field_dic
                        break
            schedules_list.append(schedules_dic)
        term_dic = {}
        _log.info(f"parse xs server Strikes: {strikes_list}")
        _log.info(f"parse xs server Arguments: {arg_list}")
        _log.info(f"parse xs server Schedules: {schedules_list}")
        if len(strikes_list) > 0:
            term_dic['Strikes'] = strikes_list
        if len(arg_list) > 0:
            term_dic['Arguments'] = arg_list
        if len(schedules_list) > 0:
            term_dic['Schedules'] = schedules_list
        req_dic['CalculateTarget'] = 'Premium'
        mk_dic = {}
        result_dic = {}
        for param_key, param_value in param_dic.items():
            if 'CalculateTarget' == param_key:
                req_dic['CalculateTarget'] = param_value
            elif 'LogLevel' == param_key:
                req_dic['LogLevel'] = param_value
            elif 'CacheType' == param_key:
                req_dic['CacheType'] = param_value
            elif 'VolSurfaceSource' == param_key:
                mk_dic['VolSurfaceSource'] = param_value
            elif 'VolSurface' == param_key:
                mk_dic['VolSurface'] = param_value
            elif 'NumSimulation' == param_key:
                result_dic['NumSimulation'] = param_value
            elif 'PremiumDate' == param_key:
                result_dic['PremiumDate'] = param_value
            elif 'Premium' == param_key:
                pre_dic = {}
                m_dic = {'Ccy2': param_value}
                pre_dic['M'] = m_dic
                result_dic['Premium'] = pre_dic
        req_dic['Instrument'] = packageName
        if len(basis_dic) > 0:
            req_dic['Basis'] = basis_dic
        if len(term_dic) > 0:
            req_dic['Term'] = term_dic
        if len(mk_dic) > 0:
            req_dic['MarketData'] = mk_dic
        if len(result_dic) > 0:
            req_dic['Result'] = result_dic
        _log.info(f"parse xs server dic: {req_dic}")
        return json.dumps(req_dic)

    @staticmethod
    def parse_item(excel_dic):
        p_dic = SttUtils.parse_excel_kv_dict(excel_dic)
        raw_keys = p_dic['raw_keys']
        rs_dic = {}
        for key, value in raw_keys.items():
            rs_dic[value['key']] = value['value']
        return rs_dic


class McpStructuredServerData:
    def __init__(self, data):
        self.data = data

    def get_field_value(self, field_name, greek_type='Ccy1'):
        if self.data is None:
            return None
        if field_name in self.data:
            return self.data[field_name]
        basis_dic = self.data['Basis']
        if field_name in basis_dic:
            return basis_dic[field_name]
        term_dic = self.data['Term']
        if 'Strikes' in term_dic:
            for item in term_dic['Strikes']:
                if item['Key'] == field_name:
                    return item['StrikePx']
        if 'Arguments' in term_dic:
            for item in term_dic['Arguments']:
                if item['Key'] == field_name:
                    return item['Value']
        result_dic = self.data['Result']
        if field_name in result_dic:
            if field_name == 'Premium':
                return result_dic['Premium']['M']['Ccy2']
        if 'Greeks' in self.data:
            if field_name in self.data['Greeks']:
                return self.data['Greeks'][field_name]['M'][greek_type]
        return f"No field result: {field_name}"

