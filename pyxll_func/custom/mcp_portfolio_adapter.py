"""
组合适配器管理模块
提供 Excel 函数来创建、查询和管理 PortfolioAdapter 对象
"""

import traceback
import os
import sys
from typing import Dict, Any, List, Optional, Tuple
from pyxll import xl_func, xl_arg, xl_return
from datetime import datetime, timedelta

# 全局对象存储：用于在 Excel 函数调用之间保持对象引用
_asset_portfolio_managers: Dict[str, Any] = {}  # manager_id -> AssetPortfolioManager
_valuator_instances: Dict[str, Any] = {}  # instance_id -> BatchValuator
_global_portfolio_adapters: Dict[str, Any] = {}  # adapter_id -> portfolio_adapter (用于跨管理器组合)
_hierarchical_managers: Dict[str, Dict[str, Any]] = {}  # hierarchical_manager_id -> {'manager': manager, 'portfolio_manager': portfolio_manager, 'managers': [managers], 'scenario_ids': [scenario_ids]}

# 添加必要的路径到 sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_current_dir))
_valuation_demo_path = os.path.join(_project_root, "test", "port2", "valuation_demo")
if _valuation_demo_path not in sys.path:
    sys.path.insert(0, _valuation_demo_path)


def excel_date_to_string(excel_date):
    """将Excel日期转换为字符串"""
    # 处理 None 或空值
    if excel_date is None or excel_date == '':
        return ''
    
    # 处理字符串类型的日期（已经是 YYYY-MM-DD 格式）
    if isinstance(excel_date, str):
        excel_date_str = excel_date.strip()
        # 如果已经是日期格式，直接返回
        if len(excel_date_str) == 10 and excel_date_str.count('-') == 2:
            try:
                # 验证是否是有效日期格式
                datetime.strptime(excel_date_str, '%Y-%m-%d')
                return excel_date_str
            except ValueError:
                pass
    
    # 处理数字类型（Excel 日期格式：从 1900-01-01 开始的天数）
    # Excel 可能传递 int 或 float 类型
    if isinstance(excel_date, (int, float)):
        try:
            base_date = datetime(1899, 12, 30)
            delta_days = timedelta(days=float(excel_date))
            date_obj = base_date + delta_days
            date_string = date_obj.strftime('%Y-%m-%d')
            return date_string
        except (ValueError, OverflowError) as e:
            print(f"Warning: Failed to convert Excel date {excel_date}: {e}")
            return str(excel_date)
    
    # 其他情况，直接转换为字符串
    return str(excel_date)


def _parse_data_to_records(data, asset_type):
    """将二维数组数据解析为AssetRecord对象列表"""
    from csv_reader import AssetRecord  # type: ignore
    
    if not data or len(data) < 2:
        raise ValueError('输入数据至少需要包含表头行和一行数据')
    
    header_row = data[0]
    field_names = [str(field).strip() if field is not None else '' for field in header_row]
    
    date_fields = ['reference_date', 'start_date', 'expiry_date', 'end_date', 'premium_date', 
                   'trade_date', 'valuation_date', 'settlement_date', 'delivery_date', 
                   'maturity_date', 'payment_date', 'fixing_date']
    
    records = []
    for row in data[1:]:
        if not row:
            continue
        row_dict = {}
        for col_idx, field_name in enumerate(field_names):
            if col_idx < len(row):
                value = row[col_idx]
                if isinstance(value, (int, float)) and field_name in date_fields:
                    value = excel_date_to_string(value)
                elif value is None:
                    value = ''
                else:
                    value = str(value).strip()
                row_dict[field_name] = value
            else:
                row_dict[field_name] = ''
        
        if asset_type == 'FUND':
            required_fields = ['InstrumentId']
        else:
            required_fields = ['underlying', 'InstrumentId']
        
        missing_values = [f for f in required_fields if not row_dict.get(f)]
        if missing_values:
            continue
        
        try:
            record = AssetRecord(row_dict)
            records.append(record)
        except Exception:
            continue
    
    if not records:
        raise ValueError('没有找到有效的交易记录')
    
    return records


class AssetPortfolioManager:
    """
    资产组合管理器
    保存当前资产（每个sheet页）每笔交易的估值对象，以及缓存每个portfolio_key对应的portfolio_adapter
    """
    
    def __init__(self, asset_type: str, data: List[List], scenario_group_id: str, valuation_date: str):
        """
        初始化资产组合管理器
        
        参数:
            asset_type: 资产类型
            data: 二维数组，第一行是字段名称，后续行是交易数据
            scenario_group_id: 情景组ID
            valuation_date: 估值日期
        """
        self.asset_type = asset_type
        self.scenario_group_id = scenario_group_id
        self.valuation_date = valuation_date
        
        # 解析数据
        self.records = _parse_data_to_records(data, asset_type)
        
        # 初始化 BatchValuator
        from batch_valuator import BatchValuator  # type: ignore
        from config_loader import ConfigLoader  # type: ignore
        
        config_file_path = os.path.join(_valuation_demo_path, "config.json")
        if not os.path.exists(config_file_path):
            raise FileNotFoundError(f"配置文件未找到: {config_file_path}")
        
        self.valuator = BatchValuator(config_file_path)
        self.config_loader = ConfigLoader(config_file_path)
        
        # 初始化市场数据
        if self.valuator.base_snapshot is None:
            self.valuator.initialize_market_data(valuation_date)


        # 解析场景组ID，获取所有场景ID列表
        try:
            self.scenario_ids = self.valuator.scenario_manager.resolve_scenario_ids([scenario_group_id])
        except Exception as e:
            self.scenario_ids = ['BASE']
            traceback.print_exc()
        
        if not self.scenario_ids:
            self.scenario_ids = ['BASE']

        input_ids = [scenario_group_id]
        applied_groups = set()
        for input_id in input_ids:
            # 检查是否是场景组或复合组
            group_def = self.valuator.scenario_manager.get_scenario_group(input_id)
            if group_def and input_id not in applied_groups:
                # 这是场景组或复合组，需要应用
                if input_id != 'BASE_SCENARIOS' and input_id != 'BASE':
                    try:
                        # 应用场景组或组合组
                        self.valuator.scenario_manager.apply_scenario_group(input_id, self.valuator.base_snapshot)
                        applied_groups.add(input_id)
                    except Exception as e:
                        print(f"Warning: Failed to apply scenario group {input_id}: {e}")
                        traceback.print_exc()
            # 如果是单个场景ID（如 'BASE' 或其他场景ID），跳过应用步骤

        # 保存每笔交易的估值对象：instrument_id -> {scenario_id: (adapter, asset_obj, record)}
        self.instrument_adapters: Dict[str, Dict[str, Tuple[Any, Any, Any]]] = {}
        
        # 缓存每个portfolio_key对应的portfolio_adapter：portfolio_key -> {scenario_id: portfolio_adapter}
        self.portfolio_adapters: Dict[str, Dict[str, Any]] = {}
        
        # 存储 asset_obj 以确保生命周期：portfolio_key -> {scenario_id: [asset_obj, ...]}
        self.portfolio_asset_objs: Dict[str, Dict[str, List[Any]]] = {}
        
        # HierarchicalPortfolioManager（用于计算 Hierarchical 级别指标）
        self.hierarchical_manager: Optional[Any] = None
        
        # 初始化所有场景的适配器
        self._initialize_adapters()
        
        # 初始化 HierarchicalPortfolioManager
        self._initialize_hierarchical_manager()
    
    def _initialize_adapters(self):
        """初始化所有场景的适配器"""
        snapshot_scenario_id = self.scenario_group_id
        
        print(f"[DEBUG] AssetPortfolioManager._initialize_adapters: 开始初始化 {self.asset_type} 的适配器")
        print(f"[DEBUG]   - 交易记录数量: {len(self.records)}")
        print(f"[DEBUG]   - 场景ID列表: {self.scenario_ids}")
        
        records_with_portfolio = 0
        records_without_portfolio = 0
        
        for record in self.records:
            instrument_id = record.instrument_id
            
            # 获取组合键
            portfolio_key = None
            if hasattr(record, 'portfolio_key'):
                portfolio_key = record.portfolio_key
            elif hasattr(record, 'get') and callable(record.get):
                portfolio_key = record.get('PortfolioKey', '')
            
            if not portfolio_key or not portfolio_key.strip():
                portfolio_key = None  # 没有组合键的交易
                records_without_portfolio += 1
            else:
                records_with_portfolio += 1
            
            for scenario_id in self.scenario_ids:
                try:
                    # 应用场景冲击获取市场数据快照
                    scenario_snapshot = self.valuator.scenario_manager.apply_scenario_shocks(
                        self.valuator.base_snapshot,
                        snapshot_scenario_id,
                        scenario_id if snapshot_scenario_id != scenario_id else None
                    )
                    
                    # 创建资产适配器
                    asset_obj, adapter = self.valuator.asset_factory.create_asset(
                        self.asset_type,
                        record,
                        scenario_snapshot,
                        self.valuation_date
                    )
                    
                    if not adapter:
                        continue
                    
                    # 设置市场数据
                    self.valuator._set_market_data(adapter, self.asset_type, scenario_snapshot, record, asset_obj)
                    
                    # 保存单笔交易的适配器
                    if instrument_id not in self.instrument_adapters:
                        self.instrument_adapters[instrument_id] = {}
                    self.instrument_adapters[instrument_id][scenario_id] = (adapter, asset_obj, record)
                    
                    # 如果有组合键，添加到组合适配器
                    if portfolio_key:
                        if portfolio_key not in self.portfolio_adapters:
                            self.portfolio_adapters[portfolio_key] = {}
                            self.portfolio_asset_objs[portfolio_key] = {}
                        
                        if scenario_id not in self.portfolio_adapters[portfolio_key]:
                            # 获取组合名称
                            portfolio_name = portfolio_key
                            if hasattr(record, 'portfolio_name'):
                                portfolio_name = record.portfolio_name
                            elif hasattr(record, 'get') and callable(record.get):
                                portfolio_name = record.get('PortfolioName', portfolio_key)
                            
                            # 创建 PortfolioAdapter
                            portfolio_adapter = self.valuator._get_or_create_portfolio_adapter(
                                portfolio_key, portfolio_name, self.asset_type
                            )
                            
                            if portfolio_adapter:
                                self.portfolio_adapters[portfolio_key][scenario_id] = portfolio_adapter
                                self.portfolio_asset_objs[portfolio_key][scenario_id] = []
                                print(f"[DEBUG]     创建 portfolio_adapter: {portfolio_key} / {scenario_id} (asset_type: {self.asset_type})")
                            else:
                                print(f"[WARNING]     创建 portfolio_adapter 失败: {portfolio_key} / {scenario_id} (asset_type: {self.asset_type})")
                        
                        # 添加适配器到 PortfolioAdapter
                        portfolio_adapter = self.portfolio_adapters[portfolio_key][scenario_id]
                        if portfolio_adapter:
                            success = self.valuator._add_adapter_to_portfolio(portfolio_adapter, adapter, self.asset_type)
                            if success:
                                # 保存 asset_obj 以确保生命周期
                                self.portfolio_asset_objs[portfolio_key][scenario_id].append(asset_obj)
                            else:
                                print(f"[WARNING]     添加 adapter 到 portfolio_adapter 失败: {instrument_id} -> {portfolio_key} / {scenario_id}")
                        else:
                            print(f"[WARNING]     portfolio_adapter 为 None: {portfolio_key} / {scenario_id}")
                    else:
                        # 没有组合键的交易，只保存单笔交易的适配器
                        pass
                
                except Exception as e:
                    print(f"[ERROR] Failed to create adapter for {instrument_id} (scenario: {scenario_id}): {e}")
                    traceback.print_exc()
        
        print(f"[DEBUG] AssetPortfolioManager._initialize_adapters: 完成初始化")
        print(f"[DEBUG]   - 有 PortfolioKey 的交易: {records_with_portfolio}")
        print(f"[DEBUG]   - 无 PortfolioKey 的交易: {records_without_portfolio}")
        print(f"[DEBUG]   - 创建的 portfolio_adapters 数量: {len(self.portfolio_adapters)}")
        if self.portfolio_adapters:
            print(f"[DEBUG]   - portfolio_keys: {list(self.portfolio_adapters.keys())}")
    
    def _initialize_hierarchical_manager(self):
        """初始化 HierarchicalPortfolioManager（用于计算 Hierarchical 级别指标）"""
        if not self.valuator.mcp:
            print(f"[WARNING] AssetPortfolioManager._initialize_hierarchical_manager: mcp 模块未加载，跳过")
            return
        
        if not self.portfolio_adapters:
            print(f"[WARNING] AssetPortfolioManager._initialize_hierarchical_manager: 没有 portfolio_adapters，跳过")
            return
        
        try:
            # 创建 HierarchicalPortfolioManager
            if hasattr(self.valuator.mcp, 'metrics') and hasattr(self.valuator.mcp.metrics, 'HierarchicalPortfolioManager'):
                self.hierarchical_manager = self.valuator.mcp.metrics.HierarchicalPortfolioManager()
            elif hasattr(self.valuator.mcp, 'HierarchicalPortfolioManager'):
                self.hierarchical_manager = self.valuator.mcp.HierarchicalPortfolioManager()
            else:
                print(f"[WARNING] AssetPortfolioManager._initialize_hierarchical_manager: HierarchicalPortfolioManager 不可用")
                return
            
            # 确定适配器类型
            adapter_type = self.valuator._get_portfolio_adapter_type(self.asset_type)
            if not adapter_type or adapter_type not in ['rate', 'fx', 'future', 'bond', 'option', 'fund']:
                print(f"[WARNING] AssetPortfolioManager._initialize_hierarchical_manager: 资产类型 {self.asset_type} 不支持 Hierarchical 级别")
                return
            
            # 将所有 portfolio_adapter 添加到 HierarchicalPortfolioManager
            added_count = 0
            for portfolio_key, scenario_adapters in self.portfolio_adapters.items():
                for sid in self.scenario_ids:
                    if sid not in scenario_adapters:
                        continue
                    
                    portfolio_adapter = scenario_adapters[sid]
                    try:
                        self.hierarchical_manager.addPortfolioAdapter(portfolio_adapter)
                        added_count += 1
                        print(f"[DEBUG] AssetPortfolioManager._initialize_hierarchical_manager: 添加 portfolio adapter: {portfolio_key} / {sid}")
                    except Exception as e:
                        print(f"[ERROR] AssetPortfolioManager._initialize_hierarchical_manager: 添加 portfolio adapter 失败 {portfolio_key} (scenario: {sid}): {e}")
                        traceback.print_exc()
            
            if added_count > 0:
                print(f"[DEBUG] AssetPortfolioManager._initialize_hierarchical_manager: 成功初始化，添加了 {added_count} 个适配器")
            else:
                print(f"[WARNING] AssetPortfolioManager._initialize_hierarchical_manager: 没有成功添加任何适配器")
                self.hierarchical_manager = None
        except Exception as e:
            print(f"[ERROR] AssetPortfolioManager._initialize_hierarchical_manager: 初始化失败: {e}")
            traceback.print_exc()
            self.hierarchical_manager = None
    
    def get_scenario_ids(self) -> List[str]:
        """获取所有场景ID列表"""
        return self.scenario_ids
    
    def get_instrument_metrics(self, scenario_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取每笔交易的估值数据
        
        参数:
            scenario_id: 场景ID，如果为None则获取所有场景的数据
        
        返回:
            结果列表
        """
        results = []
        scenario_ids_to_process = [scenario_id] if scenario_id else self.scenario_ids
        
        for instrument_id, scenario_adapters in self.instrument_adapters.items():
            for sid in scenario_ids_to_process:
                if sid not in scenario_adapters:
                    continue
                
                adapter, asset_obj, record = scenario_adapters[sid]
                
                try:
                    # 执行估值
                    valuation_results = self.valuator._valuate_single(
                        self.asset_type,
                        record,
                        sid,
                        self.valuation_date,
                        self.scenario_group_id
                    )
                    
                    # 处理估值结果
                    for result_dict in valuation_results:
                        instrument_id_from_result = result_dict.get('instrument_id', instrument_id)
                        level = result_dict.get('level', 'INSTRUMENT')
                        metrics = result_dict.get('metrics', [])
                        
                        # 获取 portfolio_key（用于排序）
                        portfolio_key = None
                        if hasattr(record, 'portfolio_key'):
                            portfolio_key = record.portfolio_key
                        elif hasattr(record, 'get') and callable(record.get):
                            portfolio_key = record.get('PortfolioKey', '')
                        
                        for metric in metrics:
                            results.append({
                                'scenario_id': sid,
                                'instrument_id': instrument_id_from_result,
                                'level': level,
                                'metric_name': metric.get('metric_name', ''),
                                'value': metric.get('value', 0.0),
                                'currency': metric.get('currency', ''),
                                'unit': metric.get('unit', ''),
                                'category': metric.get('category', ''),
                                'description': metric.get('description', ''),
                                'bucket_key': metric.get('bucket_key', ''),
                                'leg': metric.get('leg', ''),
                                'portfolio_key': portfolio_key  # 添加 portfolio_key 用于排序
                            })
                except Exception as e:
                    print(f"Warning: Failed to get metrics for {instrument_id} (scenario: {sid}): {e}")
                    traceback.print_exc()
        
        return results
    
    def get_portfolio_metrics(self, scenario_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取组合的估值数据
        
        参数:
            scenario_id: 场景ID，如果为None则获取所有场景的数据
        
        返回:
            结果列表
        """
        results = []
        scenario_ids_to_process = [scenario_id] if scenario_id else self.scenario_ids
        
        for portfolio_key, scenario_adapters in self.portfolio_adapters.items():
            for sid in scenario_ids_to_process:
                if sid not in scenario_adapters:
                    continue
                
                portfolio_adapter = scenario_adapters[sid]
                
                try:
                    # 确定资产类型
                    asset_type = 'UNKNOWN'
                    adapter_type = self.valuator._get_portfolio_adapter_type(self.asset_type)
                    if adapter_type == 'rate':
                        asset_type = 'RATE_PORTFOLIO'
                    elif adapter_type == 'fx':
                        asset_type = 'FX_PORTFOLIO'
                    elif adapter_type == 'future':
                        asset_type = 'FUTURE_PORTFOLIO'
                    elif adapter_type == 'bond':
                        asset_type = 'BOND_PORTFOLIO'
                    elif adapter_type == 'option':
                        asset_type = 'OPTION_PORTFOLIO'
                    elif adapter_type == 'fund':
                        asset_type = 'FUND_PORTFOLIO'
                    
                    # 计算组合指标
                    portfolio_results = self.valuator._calculate_portfolio_metrics(
                        portfolio_key, portfolio_adapter, asset_type, sid
                    )
                    
                    # 处理结果
                    for result_dict in portfolio_results:
                        instrument_id = result_dict.get('instrument_id', portfolio_key)
                        level = result_dict.get('level', 'PORTFOLIO')
                        metrics = result_dict.get('metrics', [])
                        
                        for metric in metrics:
                            results.append({
                                'scenario_id': sid,
                                'instrument_id': instrument_id,
                                'level': level,
                                'metric_name': metric.get('metric_name', ''),
                                'value': metric.get('value', 0.0),
                                'currency': metric.get('currency', ''),
                                'unit': metric.get('unit', ''),
                                'category': metric.get('category', ''),
                                'description': metric.get('description', ''),
                                'bucket_key': metric.get('bucket_key', ''),
                                'leg': metric.get('leg', ''),
                                'portfolio_key': portfolio_key  # 添加 portfolio_key 用于排序
                            })
                except Exception as e:
                    print(f"Warning: Failed to get portfolio metrics for {portfolio_key} (scenario: {sid}): {e}")
                    traceback.print_exc()
        
        return results




def _get_manager_id(asset_type: str, scenario_group_id: str, valuation_date: str) -> str:
    """生成管理器ID"""
    return f"{asset_type}__{scenario_group_id}__{valuation_date}"


def _get_metrics_by_level(manager_id: str, level: str, scenario_id: str, metric_category: str, 
                          use_transpose: bool, parent_key: str = '') -> List[Dict[str, Any]]:
    """
    获取指定级别的指标（辅助函数）
    
    参数:
        manager_id: 管理器ID（可能是 AssetPortfolioManager 的 ID 或 HierarchicalManager 的 ID）
        level: 级别（INSTRUMENT, PORTFOLIO, HIERARCHICAL）
        scenario_id: 场景ID
        metric_category: 指标类型
        use_transpose: 是否使用转置格式
        parent_key: 父节点键（仅 HIERARCHICAL 使用）
    
    返回:
        结果列表
    """
    # 首先尝试从 _asset_portfolio_managers 中查找
    manager = None
    hierarchical_info = None
    
    if manager_id in _asset_portfolio_managers:
        manager = _asset_portfolio_managers[manager_id]
    elif manager_id in _hierarchical_managers:
        # 如果是 hierarchical_manager_id，从 _hierarchical_managers 中获取信息
        hierarchical_info = _hierarchical_managers[manager_id]
        manager = hierarchical_info.get('manager')  # 使用第一个 manager 作为基础
    else:
        # 尝试通过 hierarchical_manager_id 查找（遍历所有 managers）
        for mgr_id, mgr in _asset_portfolio_managers.items():
            if hasattr(mgr, 'hierarchical_manager_id') and mgr.hierarchical_manager_id == manager_id:
                manager = mgr
                break
    
    if not manager:
        print(f"[WARNING] _get_metrics_by_level: 找不到 manager_id={manager_id}")
        return []
    
    results = []
    
    if level == 'INSTRUMENT':
        sid = scenario_id if scenario_id and scenario_id.strip() else None
        if hierarchical_info:
            # 跨资产情况：从所有相关的 managers 中收集 INSTRUMENT 级别数据
            managers_to_use = hierarchical_info.get('managers', [])
            print(f"[DEBUG] _get_metrics_by_level: 跨资产获取 INSTRUMENT 级别指标，从 {len(managers_to_use)} 个 managers 收集")
            for mgr in managers_to_use:
                mgr_results = mgr.get_instrument_metrics(scenario_id=sid)
                results.extend(mgr_results)
                print(f"[DEBUG]   - 从 {mgr.asset_type} 获取了 {len(mgr_results)} 条 INSTRUMENT 级别数据")
        else:
            # 单资产情况：只从当前 manager 获取
            results = manager.get_instrument_metrics(scenario_id=sid)
    elif level == 'PORTFOLIO':
        sid = scenario_id if scenario_id and scenario_id.strip() else None
        if hierarchical_info:
            # 跨资产情况：从所有相关的 managers 中收集 PORTFOLIO 级别数据
            managers_to_use = hierarchical_info.get('managers', [])
            print(f"[DEBUG] _get_metrics_by_level: 跨资产获取 PORTFOLIO 级别指标，从 {len(managers_to_use)} 个 managers 收集")
            for mgr in managers_to_use:
                mgr_results = mgr.get_portfolio_metrics(scenario_id=sid)
                results.extend(mgr_results)
                print(f"[DEBUG]   - 从 {mgr.asset_type} 获取了 {len(mgr_results)} 条 PORTFOLIO 级别数据")
        else:
            # 单资产情况：只从当前 manager 获取
            results = manager.get_portfolio_metrics(scenario_id=sid)
    elif level == 'HIERARCHICAL':
        # 确定使用哪个 hierarchical_manager
        portfolio_manager = None
        scenario_ids_to_use = []
        managers_to_use = []
        
        if hierarchical_info:
            # 使用 McpPortfolioManagerGroup 创建的跨资产 hierarchical_manager
            portfolio_manager = hierarchical_info.get('portfolio_manager')
            scenario_ids_to_use = hierarchical_info.get('scenario_ids', [])
            managers_to_use = hierarchical_info.get('managers', [])
            print(f"[DEBUG] _get_metrics_by_level: 使用跨资产 hierarchical_manager (ID: {manager_id})")
        elif hasattr(manager, 'hierarchical_manager') and manager.hierarchical_manager is not None:
            # 使用单个资产的 hierarchical_manager（在初始化时创建）
            portfolio_manager = manager.hierarchical_manager
            managers_to_use = [manager]
            print(f"[DEBUG] _get_metrics_by_level: 使用单资产 hierarchical_manager")
        else:
            print(f"[WARNING] _get_metrics_by_level: manager 没有 hierarchical_manager")
            return []
        
        if not portfolio_manager:
            print(f"[WARNING] _get_metrics_by_level: portfolio_manager 为 None")
            return []
        
        valuator = manager.valuator
        
        # 确定要使用的场景ID列表
        if scenario_id and scenario_id.strip():
            scenario_ids_to_use = [scenario_id.strip()]
        elif not scenario_ids_to_use:
            scenario_ids_to_use = manager.scenario_ids if manager.scenario_ids else ['BASE']
        
        # 确定要使用的父节点键列表
        if parent_key and parent_key.strip():
            parent_keys_to_use = [parent_key.strip()]
        else:
            # 从所有相关的 managers 中提取所有的父节点键（跨资产情况）
            parent_keys_to_use = set()
            for mgr in managers_to_use:
                for portfolio_key in mgr.portfolio_adapters.keys():
                    if '/' in portfolio_key:
                        parent_key_candidate = portfolio_key.split('/')[0]
                        parent_keys_to_use.add(parent_key_candidate)
                    else:
                        parent_keys_to_use.add(portfolio_key)
            parent_keys_to_use = sorted(list(parent_keys_to_use))
            print(f"[DEBUG] _get_metrics_by_level: 找到 {len(parent_keys_to_use)} 个父节点键: {parent_keys_to_use}")
        
        if not parent_keys_to_use:
            return []
        
        # 遍历所有父节点和场景
        for pk in parent_keys_to_use:
            for sid in scenario_ids_to_use:
                # 获取指标
                if not metric_category or metric_category == 'Valuation':
                    try:
                        parent_valuation = portfolio_manager.calculateParentValuationMetrics(pk)
                        for metric in parent_valuation:
                            from valuation_result_writer import ValuationResultWriter  # type: ignore
                            result_writer = ValuationResultWriter()
                            metric_dict = result_writer.convert_metric_result(metric)
                            results.append({
                                'scenario_id': sid,
                                'instrument_id': pk,
                                'level': 'HIERARCHICAL',
                                'metric_name': metric_dict.get('metric_name', ''),
                                'value': metric_dict.get('value', 0.0),
                                'currency': metric_dict.get('currency', ''),
                                'unit': metric_dict.get('unit', ''),
                                'category': 'Valuation',
                                'description': metric_dict.get('description', ''),
                                'bucket_key': metric_dict.get('bucket_key', ''),
                                'leg': metric_dict.get('leg', ''),
                                'portfolio_key': pk  # HIERARCHICAL 级别的 instrument_id 就是父节点
                            })
                    except Exception as e:
                        print(f"Warning: Failed to calculate valuation metrics for {pk} (scenario: {sid}): {e}")
                
                if not metric_category or metric_category == 'Risk':
                    try:
                        parent_risk = portfolio_manager.calculateParentRiskMetrics(pk)
                        for metric in parent_risk:
                            from valuation_result_writer import ValuationResultWriter  # type: ignore
                            result_writer = ValuationResultWriter()
                            metric_dict = result_writer.convert_metric_result(metric)
                            results.append({
                                'scenario_id': sid,
                                'instrument_id': pk,
                                'level': 'HIERARCHICAL',
                                'metric_name': metric_dict.get('metric_name', ''),
                                'value': metric_dict.get('value', 0.0),
                                'currency': metric_dict.get('currency', ''),
                                'unit': metric_dict.get('unit', ''),
                                'category': 'Risk',
                                'description': metric_dict.get('description', ''),
                                'bucket_key': metric_dict.get('bucket_key', ''),
                                'leg': metric_dict.get('leg', ''),
                                'portfolio_key': pk  # HIERARCHICAL 级别的 instrument_id 就是父节点
                            })
                    except Exception as e:
                        print(f"Warning: Failed to calculate risk metrics for {pk} (scenario: {sid}): {e}")
                
                if not metric_category or metric_category == 'Campisi Attribution':
                    # Campisi 归因需要前一交易日的数据
                    if hasattr(valuator, 'prev_snapshot') and valuator.prev_snapshot and hasattr(valuator, 'base_snapshot') and valuator.base_snapshot:
                        try:
                            from datetime import datetime, timedelta
                            prev_date = (datetime.strptime(manager.valuation_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
                            
                            # 构建 CampisiMarketDataSnapshot
                            start_snapshot = valuator.mcp.CampisiMarketDataSnapshot()
                            start_snapshot.snapshot_date = prev_date.replace("-", "/")
                            start_benchmark_curve = valuator.prev_snapshot['yield_curves'].get('CNY_BOND')
                            if not start_benchmark_curve:
                                start_benchmark_curve = valuator.prev_snapshot['yield_curves'].get('CNY_SWAP')
                            if start_benchmark_curve:
                                curve_type = type(start_benchmark_curve).__name__
                                shared_ptr = None
                                if curve_type == 'MBondCurve' and hasattr(valuator.mcp, 'CreateYieldCurveSharedPtrFromMBondCurve'):
                                    try:
                                        shared_ptr = valuator.mcp.CreateYieldCurveSharedPtrFromMBondCurve(start_benchmark_curve)
                                    except Exception:
                                        pass
                                elif curve_type == 'MSwapCurve' and hasattr(valuator.mcp, 'CreateYieldCurveSharedPtrFromMSwapCurve'):
                                    try:
                                        shared_ptr = valuator.mcp.CreateYieldCurveSharedPtrFromMSwapCurve(start_benchmark_curve)
                                    except Exception:
                                        pass
                                if shared_ptr:
                                    start_snapshot.benchmark_curve = shared_ptr
                            
                            end_snapshot = valuator.mcp.CampisiMarketDataSnapshot()
                            end_snapshot.snapshot_date = manager.valuation_date.replace("-", "/")
                            end_benchmark_curve = valuator.base_snapshot['yield_curves'].get('CNY_BOND')
                            if not end_benchmark_curve:
                                end_benchmark_curve = valuator.base_snapshot['yield_curves'].get('CNY_SWAP')
                            if end_benchmark_curve:
                                curve_type = type(end_benchmark_curve).__name__
                                shared_ptr = None
                                if curve_type == 'MBondCurve' and hasattr(valuator.mcp, 'CreateYieldCurveSharedPtrFromMBondCurve'):
                                    try:
                                        shared_ptr = valuator.mcp.CreateYieldCurveSharedPtrFromMBondCurve(end_benchmark_curve)
                                    except Exception:
                                        pass
                                elif curve_type == 'MSwapCurve' and hasattr(valuator.mcp, 'CreateYieldCurveSharedPtrFromMSwapCurve'):
                                    try:
                                        shared_ptr = valuator.mcp.CreateYieldCurveSharedPtrFromMSwapCurve(end_benchmark_curve)
                                    except Exception:
                                        pass
                                if shared_ptr:
                                    end_snapshot.benchmark_curve = shared_ptr
                            
                            krd_tenors = ["1Y", "2Y", "5Y", "10Y"]
                            
                            # 尝试使用 StringVector（如果可用），否则直接使用列表
                            try:
                                if hasattr(valuator.mcp, 'StringVector'):
                                    krd_tenors_vector = valuator.mcp.StringVector()
                                    for tenor in krd_tenors:
                                        krd_tenors_vector.append(tenor)
                                elif hasattr(valuator.mcp, 'std') and hasattr(valuator.mcp.std, 'StringVector'):
                                    krd_tenors_vector = valuator.mcp.std.StringVector()
                                    for tenor in krd_tenors:
                                        krd_tenors_vector.append(tenor)
                                else:
                                    krd_tenors_vector = krd_tenors
                            except Exception:
                                krd_tenors_vector = krd_tenors
                            
                            parent_campisi = portfolio_manager.calculateParentCampisiAttribution(
                                pk, start_snapshot, end_snapshot, krd_tenors_vector
                            )
                            
                            from valuation_result_writer import ValuationResultWriter  # type: ignore
                            result_writer = ValuationResultWriter()
                            for metric in parent_campisi:
                                metric_dict = result_writer.convert_metric_result(metric)
                                results.append({
                                    'scenario_id': sid,
                                    'instrument_id': pk,
                                    'level': 'HIERARCHICAL',
                                    'metric_name': metric_dict.get('metric_name', ''),
                                    'value': metric_dict.get('value', 0.0),
                                    'currency': metric_dict.get('currency', ''),
                                    'unit': metric_dict.get('unit', ''),
                                    'category': 'Campisi Attribution',
                                    'description': metric_dict.get('description', ''),
                                    'bucket_key': metric_dict.get('bucket_key', ''),
                                    'leg': metric_dict.get('leg', ''),
                                    'portfolio_key': pk  # HIERARCHICAL 级别的 instrument_id 就是父节点
                                })
                        except Exception as e:
                            print(f"Warning: Failed to calculate Campisi attribution for {pk} (scenario: {sid}): {e}")
                            traceback.print_exc()
    
    # 过滤指标类型
    if metric_category and metric_category.strip():
        results = [r for r in results if r.get('category', '') == metric_category]
    
    return results


def _format_results_transpose(results: List[Dict[str, Any]], sort_by_level: bool = True) -> List[List[Any]]:
    """
    将结果转换为行转列格式（每个指标平铺为一列）
    
    参数:
        results: 结果列表，每个结果包含 scenario_id, instrument_id, level, metric_name, value 等字段
        sort_by_level: 是否按父子结构排序（先按场景，再按父子结构）
    
    返回:
        二维数组：[[InstrumentId, ScenarioId, Level, MetricName1, MetricName2, ...], ...]
    """
    if not results:
        return []
    
    # 收集所有唯一的指标名称
    metric_names = sorted(set([r.get('metric_name', '') for r in results if r.get('metric_name')]))
    
    # 按 (instrument_id, scenario_id, level) 分组，同时保存额外的排序信息
    grouped = {}
    group_info = {}  # 保存每个组的额外信息（portfolio_key等）
    for r in results:
        key = (r.get('instrument_id', ''), r.get('scenario_id', ''), r.get('level', ''))
        if key not in grouped:
            grouped[key] = {}
            group_info[key] = {
                'portfolio_key': r.get('portfolio_key', ''),
                'instrument_id': r.get('instrument_id', ''),
                'level': r.get('level', ''),
                'scenario_id': r.get('scenario_id', '')
            }
        metric_name = r.get('metric_name', '')
        if metric_name:
            grouped[key][metric_name] = r.get('value', 0.0)
    
    # 构建表头
    header = ['InstrumentId', 'ScenarioId', 'Level'] + metric_names
    
    # 构建数据行
    output = [header]
    
    # 排序逻辑：先按场景，再按父子结构深度优先排序
    if sort_by_level:
        def get_sort_key(item):
            """获取排序键，实现先按场景，再按父子结构深度优先排序"""
            key, metrics = item
            instrument_id, scenario_id, level = key
            info = group_info[key]
            portfolio_key = info.get('portfolio_key', '')
            
            # 构建完整的层级路径用于排序，使用级别前缀确保同一父节点下的子节点按级别排序
            level_order = {'HIERARCHICAL': '0', 'PORTFOLIO': '1', 'INSTRUMENT': '2'}
            level_prefix = level_order.get(level, '9')
            
            if level == 'HIERARCHICAL':
                # HIERARCHICAL 级别：instrument_id 就是父节点（如 "PORTFOLIO_A"）
                # 排序路径：场景 + 级别前缀 + 父节点
                sort_path = f"{scenario_id}::{level_prefix}::{instrument_id}"
            elif level == 'PORTFOLIO':
                # PORTFOLIO 级别：instrument_id 是 portfolio_key（如 "PORTFOLIO_A/SUB_A1"）
                portfolio_key = instrument_id
                if '/' in portfolio_key:
                    # 有父节点的情况（如 "PORTFOLIO_A/SUB_A1"）
                    parts = portfolio_key.split('/')
                    parent = parts[0]  # 父节点（如 "PORTFOLIO_A"）
                    # 排序路径：场景 + 父节点 + 级别前缀 + portfolio_key
                    # 使用级别前缀确保同一父节点下的 PORTFOLIO 紧跟在 HIERARCHICAL 后面
                    sort_path = f"{scenario_id}::{parent}::{level_prefix}::{portfolio_key}"
                else:
                    # 没有父节点的情况（如 "PORTFOLIO_B"）
                    # 排序路径：场景 + 'ZZZ' + 级别前缀 + portfolio_key
                    # 使用 'ZZZ' 确保没有父节点的 PORTFOLIO 排在所有有父节点的 PORTFOLIO 之后
                    sort_path = f"{scenario_id}::ZZZ::{level_prefix}::{portfolio_key}"
            else:  # INSTRUMENT
                # INSTRUMENT 级别：需要从 portfolio_key 推断父节点
                if portfolio_key:
                    if '/' in portfolio_key:
                        # 有父节点的情况（如 "PORTFOLIO_A/SUB_A1"）
                        parts = portfolio_key.split('/')
                        parent = parts[0]  # 父节点（如 "PORTFOLIO_A"）
                        # 排序路径：场景 + 父节点 + 级别前缀 + portfolio_key + 级别前缀 + instrument_id
                        # 使用与 PORTFOLIO 相同的路径前缀，确保 INSTRUMENT 紧跟在对应的 PORTFOLIO 后面
                        sort_path = f"{scenario_id}::{parent}::1::{portfolio_key}::{level_prefix}::{instrument_id}"
                    else:
                        # 没有父节点的情况（如 "PORTFOLIO_B"）
                        # 排序路径：场景 + 'ZZZ' + 级别前缀 + portfolio_key + 级别前缀 + instrument_id
                        sort_path = f"{scenario_id}::ZZZ::1::{portfolio_key}::{level_prefix}::{instrument_id}"
                else:
                    # 没有 portfolio_key，无法确定层级关系
                    # 排序路径：场景 + 级别前缀 + instrument_id
                    sort_path = f"{scenario_id}::{level_prefix}::{instrument_id}"
            
            # 使用层级路径排序，这样会自动实现深度优先的父子结构
            return sort_path
        
        sorted_items = sorted(grouped.items(), key=get_sort_key)
    else:
        sorted_items = sorted(grouped.items())
    
    # 生成树形结构的 InstrumentId（添加缩进和层级标识）
    # 使用简单的缩进方式，让Excel中更容易看出层级关系
    for (instrument_id, scenario_id, level), metrics in sorted_items:
        info = group_info[(instrument_id, scenario_id, level)]
        portfolio_key = info.get('portfolio_key', '')
        
        # 计算层级深度并生成带缩进的 InstrumentId
        display_id = instrument_id
        if level == 'HIERARCHICAL':
            # 顶级节点，不缩进
            display_id = instrument_id
        elif level == 'PORTFOLIO':
            # 二级节点，添加两个空格缩进
            if '/' in instrument_id:
                display_id = '  ' + instrument_id  # 两个空格缩进
            else:
                display_id = instrument_id  # 没有父节点的PORTFOLIO不缩进
        else:  # INSTRUMENT
            # 三级节点，添加四个空格缩进
            if portfolio_key and '/' in portfolio_key:
                display_id = '    ' + instrument_id  # 四个空格缩进
            elif portfolio_key:
                display_id = '  ' + instrument_id  # 两个空格缩进
            else:
                display_id = instrument_id  # 没有portfolio_key的不缩进
        
        row = [display_id, scenario_id, level]
        for metric_name in metric_names:
            row.append(metrics.get(metric_name, ''))
        output.append(row)
    
    return output


@xl_func(macro=False, recalc_on_open=True, thread_safe=False)
@xl_arg("data", "var[][]")
@xl_arg("asset_type", "str")
@xl_arg("scenario_group_id", "str")
@xl_arg("valuation_date", "var")
@xl_return("str")
def McpPortfolioAdapter(
    data, 
    asset_type, 
    scenario_group_id='GROUP_BASE_SCENARIOS',
    valuation_date=None
):
    """
    创建 AssetPortfolioManager 对象
    
    参数:
        data: 二维数组，第一行是字段名称，后续行是交易数据
        asset_type: 资产类型（如 'COMMODITYFUTURE', 'EQUITYSPOT' 等）
        scenario_group_id: 情景组ID，默认为 'GROUP_BASE_SCENARIOS'
        valuation_date: 估值日期（格式：'YYYY-MM-DD'），如果为None则从配置文件读取
    
    返回:
        @manager_id: 管理器ID，用于后续查询（前缀 @ 表示对象ID）
    """
    try:
        from config_loader import ConfigLoader  # type: ignore
        
        # 确定估值日期
        if valuation_date is None or valuation_date == '':
            config_file_path = os.path.join(_valuation_demo_path, "config.json")
            config_loader = ConfigLoader(config_file_path)
            valuation_date = config_loader.get_valuation_date() or "2025-01-15"
        else:
            # 处理Excel日期格式（可能是数字或字符串）
            valuation_date = excel_date_to_string(valuation_date)
            
            # 验证日期格式
            if not valuation_date or len(valuation_date) != 10 or valuation_date.count('-') != 2:
                raise ValueError(f"无效的估值日期格式: {valuation_date}。期望格式: YYYY-MM-DD")
        
        # 创建 AssetPortfolioManager
        manager = AssetPortfolioManager(
            asset_type=asset_type,
            data=data,
            scenario_group_id=scenario_group_id,
            valuation_date=valuation_date
        )
        
        # 生成 manager_id
        manager_id = _get_manager_id(asset_type, scenario_group_id, valuation_date)
        
        # 存储管理器
        _asset_portfolio_managers[manager_id] = manager
        
        # 返回时加上 @ 前缀
        return f"@{manager_id}"
    
    except Exception as e:
        traceback.print_exc()
        return f"ERROR: {str(e)}"


@xl_func(macro=False, recalc_on_open=True, thread_safe=False, auto_resize=True)
@xl_arg("manager_id", "str")
def PortGetScenarioIds(manager_id):
    """
    获取当前场景组/组合组下有哪些 scenario_id
    
    参数:
        manager_id: 管理器ID（由 McpPortfolioAdapter 返回，支持 @ 前缀）
    
    返回:
        一维数组：场景ID列表
    """
    try:
        # 移除 @ 前缀（如果存在）
        if manager_id.startswith('@'):
            manager_id = manager_id[1:]
        
        if manager_id not in _asset_portfolio_managers:
            return [['ERROR'], [f'管理器ID不存在: {manager_id}']]
        
        manager = _asset_portfolio_managers[manager_id]
        scenario_ids = manager.get_scenario_ids()
        
        # 返回二维数组格式（每行一个场景ID）
        return [[sid] for sid in scenario_ids]
    
    except Exception as e:
        traceback.print_exc()
        return [['ERROR'], [f'获取场景ID失败: {str(e)}']]


@xl_func(macro=False, recalc_on_open=True, thread_safe=False, auto_resize=True)
@xl_arg("manager_id", "str")
@xl_arg("level", "str")
@xl_arg("scenario_id", "str")
@xl_arg("metric_category", "str")
@xl_arg("output_format", "str")
def PortMetrics(manager_id, level='', scenario_id='', metric_category='', output_format='', parent_key=''):
    """
    获取估值指标数据（支持 Instrument、Portfolio、Hierarchical 三个级别）
    
    参数:
        manager_id: 管理器ID（由 McpPortfolioAdapter 或 McpPortfolioManagerGroup 返回，支持 @ 前缀）
        level: 指标级别（可选）：
            - '': 返回所有级别的指标（默认）
            - 'INSTRUMENT': 交易级别指标
            - 'PORTFOLIO': 组合级别指标
            - 'HIERARCHICAL': 分层级别指标
        scenario_id: 场景ID，如果不传则获取所有场景的数据
        metric_category: 指标类型（可选）：
            - 'Valuation': 估值指标
            - 'Risk': 风险指标
            - 'Attribution': 归因指标
            - 'Concentration': 集中度指标（仅 Portfolio 级别）
            - 'Portfolio': 交易笔数（仅 Portfolio 级别）
            - 'Campisi Attribution': Campisi 归因指标（仅 Hierarchical 级别）
            - '': 所有指标（默认）
        output_format: 输出格式（可选）：
            - '': 默认行转列格式（transpose），每个指标平铺为一列
            - 'transpose': 行转列格式，每个指标平铺为一列
            - 'normal': 正常格式，每行一个指标
        parent_key: 父节点组合键（仅 Hierarchical 级别使用，如 'PORTFOLIO_A'），默认为 ''。如果为 ''，则计算所有父节点
    
    返回:
        二维数组：
        - normal格式：[[ScenarioId, InstrumentId, Level, MetricName, Value, Currency, Unit, Category, Description, Bucket, Leg], ...]
        - transpose格式：[[InstrumentId, ScenarioId, Level, MetricName1, MetricName2, ...], ...]
    """
    try:
        # 移除 @ 前缀（如果存在）
        if manager_id.startswith('@'):
            manager_id = manager_id[1:]
        
        # 确定输出格式：默认是 transpose，传 'transpose' 时也是 transpose，传 'normal' 时是 normal
        use_transpose = (output_format != 'normal')
        
        # 确定级别：如果为空，返回所有级别
        level_upper = level.upper() if level and level.strip() else ''
        
        # 如果 level 为空，收集所有级别的指标
        if not level_upper:
            all_results = []
            
            # 检查是否是跨资产组合
            is_cross_asset = (manager_id in _hierarchical_managers)
            if is_cross_asset:
                hierarchical_info = _hierarchical_managers[manager_id]
                managers_count = len(hierarchical_info.get('managers', []))
                print(f"[DEBUG] PortMetrics: 跨资产组合，包含 {managers_count} 个资产类型")
            
            # 获取 INSTRUMENT 级别指标（跨资产情况下会从所有 managers 收集）
            instrument_results = _get_metrics_by_level(manager_id, 'INSTRUMENT', scenario_id, metric_category, use_transpose)
            if instrument_results:
                all_results.extend(instrument_results)
                print(f"[DEBUG] PortMetrics: 收集了 {len(instrument_results)} 条 INSTRUMENT 级别数据")
            
            # 获取 PORTFOLIO 级别指标（跨资产情况下会从所有 managers 收集）
            portfolio_results = _get_metrics_by_level(manager_id, 'PORTFOLIO', scenario_id, metric_category, use_transpose)
            if portfolio_results:
                all_results.extend(portfolio_results)
                print(f"[DEBUG] PortMetrics: 收集了 {len(portfolio_results)} 条 PORTFOLIO 级别数据")
            
            # 获取 HIERARCHICAL 级别指标
            hierarchical_results = _get_metrics_by_level(manager_id, 'HIERARCHICAL', scenario_id, metric_category, use_transpose, parent_key)
            if hierarchical_results:
                all_results.extend(hierarchical_results)
                print(f"[DEBUG] PortMetrics: 收集了 {len(hierarchical_results)} 条 HIERARCHICAL 级别数据")
            
            print(f"[DEBUG] PortMetrics: 总共收集了 {len(all_results)} 条数据（跨资产: {is_cross_asset}）")
            
            if not all_results:
                if use_transpose:
                    return [['InstrumentId', 'ScenarioId', 'Level'], ['', '', '']]
                return [['ScenarioId', 'InstrumentId', 'Level', 'MetricName', 'Value', 'Currency', 'Unit', 'Category', 'Description', 'Bucket', 'Leg'],
                        ['', '', '', 'WARNING', 0.0, '', '', 'Warning', '没有找到任何指标', '', '']]
            
            # 根据输出格式转换
            if use_transpose:
                return _format_results_transpose(all_results, sort_by_level=True)
            
            # 正常格式：转换为二维数组
            output = []
            for r in all_results:
                output.append([
                    r.get('scenario_id', ''),
                    r.get('instrument_id', ''),
                    r.get('level', ''),
                    r.get('metric_name', ''),
                    r.get('value', 0.0),
                    r.get('currency', ''),
                    r.get('unit', ''),
                    r.get('category', ''),
                    r.get('description', ''),
                    r.get('bucket_key', ''),
                    r.get('leg', '')
                ])
            
            header = [['ScenarioId', 'InstrumentId', 'Level', 'MetricName', 'Value', 'Currency', 'Unit', 'Category', 'Description', 'Bucket', 'Leg']]
            return header + output
        
        # 如果指定了级别，只返回该级别的指标
        results = _get_metrics_by_level(manager_id, level_upper, scenario_id, metric_category, use_transpose, parent_key)
        
        if not results:
            if use_transpose:
                return [['InstrumentId', 'ScenarioId', 'Level'], ['', '', level_upper]]
            return [['ScenarioId', 'InstrumentId', 'Level', 'MetricName', 'Value', 'Currency', 'Unit', 'Category', 'Description', 'Bucket', 'Leg'],
                    ['', '', level_upper, 'WARNING', 0.0, '', '', 'Warning', '没有找到任何指标', '', '']]
        
        # 根据输出格式转换
        if use_transpose:
            return _format_results_transpose(results, sort_by_level=True)
        
        # 正常格式：转换为二维数组
        output = []
        for r in results:
            output.append([
                r.get('scenario_id', ''),
                r.get('instrument_id', ''),
                r.get('level', level_upper),
                r.get('metric_name', ''),
                r.get('value', 0.0),
                r.get('currency', ''),
                r.get('unit', ''),
                r.get('category', ''),
                r.get('description', ''),
                r.get('bucket_key', ''),
                r.get('leg', '')
            ])
        
        header = [['ScenarioId', 'InstrumentId', 'Level', 'MetricName', 'Value', 'Currency', 'Unit', 'Category', 'Description', 'Bucket', 'Leg']]
        return header + output
    
    except Exception as e:
        traceback.print_exc()
        level_upper = level.upper() if level else ''
        use_transpose = (output_format != 'normal')
        if use_transpose:
            return [['InstrumentId', 'ScenarioId', 'Level'], ['', '', 'ERROR']]
        return [['ScenarioId', 'InstrumentId', 'Level', 'MetricName', 'Value', 'Currency', 'Unit', 'Category', 'Description', 'Bucket', 'Leg'],
                ['', '', level_upper, 'ERROR', 0.0, '', '', 'Error', f'获取指标失败: {str(e)}', '', '']]


@xl_func(macro=False, recalc_on_open=True, thread_safe=False)
@xl_arg("manager_id", "str")
def McpGetPortfolioAdapter(manager_id, portfolio_key, scenario_id='BASE'):
    """
    获取指定组合的 PortfolioAdapter 对象（用于组合多个适配器创建 PortfolioManager）
    
    参数:
        manager_id: 管理器ID（由 McpPortfolioAdapter 返回，支持 @ 前缀）
        portfolio_key: 组合键（如 'PORTFOLIO_A/SUB_A1'）
        scenario_id: 场景ID，默认为 'BASE'
    
    返回:
        @adapter_id: 适配器ID，用于 McpPortfolioManagerGroup（前缀 @ 表示对象ID）
    """
    try:
        # 移除 @ 前缀（如果存在）
        if manager_id.startswith('@'):
            manager_id = manager_id[1:]
        
        if manager_id not in _asset_portfolio_managers:
            return f"ERROR: 管理器ID不存在: {manager_id}"
        
        manager = _asset_portfolio_managers[manager_id]
        
        if portfolio_key not in manager.portfolio_adapters:
            return f"ERROR: 组合键不存在: {portfolio_key}"
        
        if scenario_id not in manager.portfolio_adapters[portfolio_key]:
            return f"ERROR: 场景ID不存在: {scenario_id}"
        
        portfolio_adapter = manager.portfolio_adapters[portfolio_key][scenario_id]
        
        # 生成 adapter_id（用于后续组合）
        adapter_id = f"{manager_id}__{portfolio_key}__{scenario_id}"
        
        # 存储到全局字典（用于 McpPortfolioManagerGroup）
        _global_portfolio_adapters[adapter_id] = {
            'adapter': portfolio_adapter,
            'manager_id': manager_id,
            'portfolio_key': portfolio_key,
            'scenario_id': scenario_id,
            'asset_type': manager.asset_type
        }
        
        # 返回时加上 @ 前缀
        return f"@{adapter_id}"
    
    except Exception as e:
        traceback.print_exc()
        return f"ERROR: {str(e)}"


@xl_func(macro=False, recalc_on_open=True, thread_safe=False)
@xl_arg("manager_ids", "var[]")
@xl_arg("scenario_id", "str")
def McpPortfolioManagerGroup(manager_ids, scenario_id=''):
    """
    组合多个 AssetPortfolioManager 创建 HierarchicalPortfolioManager
    
    参数:
        manager_ids: 管理器ID数组（由 McpPortfolioAdapter 返回的ID列表，每个对应一个资产类型，支持 @ 前缀）
        scenario_id: 场景ID，默认为 ''。如果为 ''，则使用第一个 manager 的所有场景ID
    
    返回:
        @hierarchical_manager_id: 分层管理器ID，用于后续查询（前缀 @ 表示对象ID）
    """
    try:
        if not manager_ids:
            return f"ERROR: manager_ids 不能为空"
        
        # 确保 manager_ids 是列表
        if not isinstance(manager_ids, list):
            manager_ids = [manager_ids]
        
        # 移除 @ 前缀（如果存在）并验证所有 manager_id 是否存在
        managers = []
        for manager_id in manager_ids:
            # 移除 @ 前缀（如果存在）
            if isinstance(manager_id, str) and manager_id.startswith('@'):
                manager_id = manager_id[1:]
            
            if manager_id not in _asset_portfolio_managers:
                return f"ERROR: 管理器ID不存在: {manager_id}"
            managers.append(_asset_portfolio_managers[manager_id])
        
        # 使用第一个 manager 的 valuator（所有 manager 应该共享相同的 mcp 模块）
        first_manager = managers[0]
        valuator = first_manager.valuator
        
        if not valuator.mcp:
            return f"ERROR: mcp 模块未加载"
        
        # 确定要使用的场景ID列表
        if scenario_id and scenario_id.strip():
            # 如果指定了 scenario_id，只使用该场景
            scenario_ids_to_use = [scenario_id.strip()]
        else:
            # 如果没有指定 scenario_id，使用第一个 manager 的所有场景ID
            scenario_ids_to_use = first_manager.scenario_ids if first_manager.scenario_ids else ['BASE']
        
        # 创建新的 HierarchicalPortfolioManager（为每个场景创建一个）
        # 注意：由于 HierarchicalPortfolioManager 不能同时包含多个场景的数据，
        # 我们为所有场景添加 portfolio_adapter，但使用第一个场景的 manager_id 作为标识
        portfolio_manager = None
        if hasattr(valuator.mcp, 'metrics') and hasattr(valuator.mcp.metrics, 'HierarchicalPortfolioManager'):
            portfolio_manager = valuator.mcp.metrics.HierarchicalPortfolioManager()
        elif hasattr(valuator.mcp, 'HierarchicalPortfolioManager'):
            portfolio_manager = valuator.mcp.HierarchicalPortfolioManager()
        else:
            return f"ERROR: HierarchicalPortfolioManager 不可用"
        
        # 从每个 manager 中获取所有的 portfolio_adapter 并添加到 HierarchicalPortfolioManager
        added_count = 0
        print(f"[DEBUG] McpPortfolioManagerGroup: 开始处理 {len(managers)} 个 manager")
        print(f"[DEBUG] 场景ID列表: {scenario_ids_to_use}")
        
        for manager in managers:
            print(f"\n[DEBUG] 处理 manager: asset_type={manager.asset_type}, scenario_group_id={manager.scenario_group_id}")
            print(f"[DEBUG]   - 该 manager 的场景ID: {manager.scenario_ids}")
            print(f"[DEBUG]   - 该 manager 的 portfolio_adapters 数量: {len(manager.portfolio_adapters)}")
            
            if not manager.portfolio_adapters:
                print(f"[WARNING] manager {manager.asset_type} 没有 portfolio_adapters（可能所有交易都没有 PortfolioKey）")
                continue
            
            # 确定适配器类型
            adapter_type = valuator._get_portfolio_adapter_type(manager.asset_type)
            print(f"[DEBUG]   - adapter_type: {adapter_type}")
            
            if not adapter_type:
                print(f"[WARNING] manager {manager.asset_type} 的 adapter_type 为 None，跳过该 manager")
                continue
            
            if adapter_type not in ['rate', 'fx', 'future', 'bond', 'option', 'fund']:
                print(f"[WARNING] manager {manager.asset_type} 的 adapter_type '{adapter_type}' 不在支持的列表中，跳过该 manager")
                continue
            
            # 遍历该 manager 的所有 portfolio_key
            for portfolio_key, scenario_adapters in manager.portfolio_adapters.items():
                print(f"[DEBUG]   处理 portfolio_key: {portfolio_key}")
                print(f"[DEBUG]     - 该 portfolio_key 的场景ID: {list(scenario_adapters.keys())}")
                
                # 遍历所有要使用的场景ID
                for sid in scenario_ids_to_use:
                    if sid not in scenario_adapters:
                        # 如果指定的 scenario_id 不存在，跳过
                        print(f"[DEBUG]     - 跳过场景 {sid}（不存在于该 portfolio_key）")
                        continue
                    
                    portfolio_adapter = scenario_adapters[sid]
                    
                    try:
                        portfolio_manager.addPortfolioAdapter(portfolio_adapter)
                        added_count += 1
                        print(f"[SUCCESS] Added portfolio adapter: {manager.asset_type} / {portfolio_key} / {sid}")
                    except Exception as e:
                        print(f"[ERROR] Failed to add portfolio adapter {portfolio_key} from {manager.asset_type} (scenario: {sid}): {e}")
                        print(f"[ERROR]   - portfolio_adapter 类型: {type(portfolio_adapter).__name__}")
                        print(f"[ERROR]   - portfolio_manager 类型: {type(portfolio_manager).__name__}")
                        traceback.print_exc()
        
        print(f"\n[DEBUG] McpPortfolioManagerGroup: 总共添加了 {added_count} 个 portfolio adapter")
        
        if added_count == 0:
            return f"ERROR: 没有成功添加任何适配器到 PortfolioManager"
        
        # 生成 hierarchical_manager_id（简化版本，使用时间戳和计数器）
        import time
        timestamp = int(time.time() * 1000) % 1000000  # 取后6位时间戳
        counter = len(_asset_portfolio_managers) % 1000  # 取后3位计数器
        hierarchical_manager_id = f"H_{timestamp}_{counter}"
        
        # 存储到第一个 manager 中（用于向后兼容）
        first_manager.hierarchical_manager = portfolio_manager
        first_manager.hierarchical_manager_id = hierarchical_manager_id
        first_manager.hierarchical_scenario_ids = scenario_ids_to_use  # 保存使用的场景ID列表
        
        # 存储到全局字典中（用于跨资产查询）
        _hierarchical_managers[hierarchical_manager_id] = {
            'manager': first_manager,  # 第一个 manager 作为基础
            'portfolio_manager': portfolio_manager,
            'managers': managers,  # 所有相关的 managers
            'scenario_ids': scenario_ids_to_use,
            'manager_ids': [mgr_id for mgr_id in _asset_portfolio_managers if _asset_portfolio_managers[mgr_id] in managers]
        }
        print(f"[DEBUG] McpPortfolioManagerGroup: 存储 hierarchical_manager_id={hierarchical_manager_id} 到全局字典")
        print(f"[DEBUG]   - 包含 {len(managers)} 个 managers")
        print(f"[DEBUG]   - 场景ID列表: {scenario_ids_to_use}")
        
        # 返回时加上 @ 前缀
        return f"@{hierarchical_manager_id}"
    
    except Exception as e:
        traceback.print_exc()
        return f"ERROR: {str(e)}"


@xl_func(macro=False, recalc_on_open=False, thread_safe=False)
def McpClearPortfolioAdapters():
    """清空所有存储的 AssetPortfolioManager 对象"""
    global _asset_portfolio_managers, _hierarchical_managers
    _asset_portfolio_managers.clear()
    _hierarchical_managers.clear()
    return "已清空所有资产组合管理器"


@xl_func(macro=False, recalc_on_open=False, thread_safe=False, auto_resize=True)
def McpListPortfolioAdapters():
    """列出所有已创建的 AssetPortfolioManager ID"""
    if not _asset_portfolio_managers:
        return [['ManagerID', 'AssetType', 'ScenarioGroupId', 'ValuationDate'], ['', '', '', '']]
    
    results = []
    for manager_id, manager in _asset_portfolio_managers.items():
        results.append([
            manager_id,
            manager.asset_type,
            manager.scenario_group_id,
            manager.valuation_date
        ])
    
    header = [['ManagerID', 'AssetType', 'ScenarioGroupId', 'ValuationDate']]
    return header + results
@xl_arg("manager_id", "str")
def McpGetPortfolioAdapter(manager_id, portfolio_key, scenario_id='BASE'):
    """
    获取指定组合的 PortfolioAdapter 对象（用于组合多个适配器创建 PortfolioManager）
    
    参数:
        manager_id: 管理器ID（由 McpPortfolioAdapter 返回，支持 @ 前缀）
        portfolio_key: 组合键（如 'PORTFOLIO_A/SUB_A1'）
        scenario_id: 场景ID，默认为 'BASE'
    
    返回:
        @adapter_id: 适配器ID，用于 McpPortfolioManagerGroup（前缀 @ 表示对象ID）
    """
    try:
        # 移除 @ 前缀（如果存在）
        if manager_id.startswith('@'):
            manager_id = manager_id[1:]
        
        if manager_id not in _asset_portfolio_managers:
            return f"ERROR: 管理器ID不存在: {manager_id}"
        
        manager = _asset_portfolio_managers[manager_id]
        
        if portfolio_key not in manager.portfolio_adapters:
            return f"ERROR: 组合键不存在: {portfolio_key}"
        
        if scenario_id not in manager.portfolio_adapters[portfolio_key]:
            return f"ERROR: 场景ID不存在: {scenario_id}"
        
        portfolio_adapter = manager.portfolio_adapters[portfolio_key][scenario_id]
        
        # 生成 adapter_id（用于后续组合）
        adapter_id = f"{manager_id}__{portfolio_key}__{scenario_id}"
        
        # 存储到全局字典（用于 McpPortfolioManagerGroup）
        _global_portfolio_adapters[adapter_id] = {
            'adapter': portfolio_adapter,
            'manager_id': manager_id,
            'portfolio_key': portfolio_key,
            'scenario_id': scenario_id,
            'asset_type': manager.asset_type
        }
        
        # 返回时加上 @ 前缀
        return f"@{adapter_id}"
    
    except Exception as e:
        traceback.print_exc()
        return f"ERROR: {str(e)}"


@xl_func(macro=False, recalc_on_open=True, thread_safe=False)
@xl_arg("manager_ids", "var[]")
@xl_arg("scenario_id", "str")
def McpPortfolioManagerGroup(manager_ids, scenario_id=''):
    """
    组合多个 AssetPortfolioManager 创建 HierarchicalPortfolioManager
    
    参数:
        manager_ids: 管理器ID数组（由 McpPortfolioAdapter 返回的ID列表，每个对应一个资产类型，支持 @ 前缀）
        scenario_id: 场景ID，默认为 ''。如果为 ''，则使用第一个 manager 的所有场景ID
    
    返回:
        @hierarchical_manager_id: 分层管理器ID，用于后续查询（前缀 @ 表示对象ID）
    """
    try:
        if not manager_ids:
            return f"ERROR: manager_ids 不能为空"
        
        # 确保 manager_ids 是列表
        if not isinstance(manager_ids, list):
            manager_ids = [manager_ids]
        
        # 移除 @ 前缀（如果存在）并验证所有 manager_id 是否存在
        managers = []
        for manager_id in manager_ids:
            # 移除 @ 前缀（如果存在）
            if isinstance(manager_id, str) and manager_id.startswith('@'):
                manager_id = manager_id[1:]
            
            if manager_id not in _asset_portfolio_managers:
                return f"ERROR: 管理器ID不存在: {manager_id}"
            managers.append(_asset_portfolio_managers[manager_id])
        
        # 使用第一个 manager 的 valuator（所有 manager 应该共享相同的 mcp 模块）
        first_manager = managers[0]
        valuator = first_manager.valuator
        
        if not valuator.mcp:
            return f"ERROR: mcp 模块未加载"
        
        # 确定要使用的场景ID列表
        if scenario_id and scenario_id.strip():
            # 如果指定了 scenario_id，只使用该场景
            scenario_ids_to_use = [scenario_id.strip()]
        else:
            # 如果没有指定 scenario_id，使用第一个 manager 的所有场景ID
            scenario_ids_to_use = first_manager.scenario_ids if first_manager.scenario_ids else ['BASE']
        
        # 创建新的 HierarchicalPortfolioManager（为每个场景创建一个）
        # 注意：由于 HierarchicalPortfolioManager 不能同时包含多个场景的数据，
        # 我们为所有场景添加 portfolio_adapter，但使用第一个场景的 manager_id 作为标识
        portfolio_manager = None
        if hasattr(valuator.mcp, 'metrics') and hasattr(valuator.mcp.metrics, 'HierarchicalPortfolioManager'):
            portfolio_manager = valuator.mcp.metrics.HierarchicalPortfolioManager()
        elif hasattr(valuator.mcp, 'HierarchicalPortfolioManager'):
            portfolio_manager = valuator.mcp.HierarchicalPortfolioManager()
        else:
            return f"ERROR: HierarchicalPortfolioManager 不可用"
        
        # 从每个 manager 中获取所有的 portfolio_adapter 并添加到 HierarchicalPortfolioManager
        added_count = 0
        print(f"[DEBUG] McpPortfolioManagerGroup: 开始处理 {len(managers)} 个 manager")
        print(f"[DEBUG] 场景ID列表: {scenario_ids_to_use}")
        
        for manager in managers:
            print(f"\n[DEBUG] 处理 manager: asset_type={manager.asset_type}, scenario_group_id={manager.scenario_group_id}")
            print(f"[DEBUG]   - 该 manager 的场景ID: {manager.scenario_ids}")
            print(f"[DEBUG]   - 该 manager 的 portfolio_adapters 数量: {len(manager.portfolio_adapters)}")
            
            if not manager.portfolio_adapters:
                print(f"[WARNING] manager {manager.asset_type} 没有 portfolio_adapters（可能所有交易都没有 PortfolioKey）")
                continue
            
            # 确定适配器类型
            adapter_type = valuator._get_portfolio_adapter_type(manager.asset_type)
            print(f"[DEBUG]   - adapter_type: {adapter_type}")
            
            if not adapter_type:
                print(f"[WARNING] manager {manager.asset_type} 的 adapter_type 为 None，跳过该 manager")
                continue
            
            if adapter_type not in ['rate', 'fx', 'future', 'bond', 'option', 'fund']:
                print(f"[WARNING] manager {manager.asset_type} 的 adapter_type '{adapter_type}' 不在支持的列表中，跳过该 manager")
                continue
            
            # 遍历该 manager 的所有 portfolio_key
            for portfolio_key, scenario_adapters in manager.portfolio_adapters.items():
                print(f"[DEBUG]   处理 portfolio_key: {portfolio_key}")
                print(f"[DEBUG]     - 该 portfolio_key 的场景ID: {list(scenario_adapters.keys())}")
                
                # 遍历所有要使用的场景ID
                for sid in scenario_ids_to_use:
                    if sid not in scenario_adapters:
                        # 如果指定的 scenario_id 不存在，跳过
                        print(f"[DEBUG]     - 跳过场景 {sid}（不存在于该 portfolio_key）")
                        continue
                    
                    portfolio_adapter = scenario_adapters[sid]
                    
                    try:
                        portfolio_manager.addPortfolioAdapter(portfolio_adapter)
                        added_count += 1
                        print(f"[SUCCESS] Added portfolio adapter: {manager.asset_type} / {portfolio_key} / {sid}")
                    except Exception as e:
                        print(f"[ERROR] Failed to add portfolio adapter {portfolio_key} from {manager.asset_type} (scenario: {sid}): {e}")
                        print(f"[ERROR]   - portfolio_adapter 类型: {type(portfolio_adapter).__name__}")
                        print(f"[ERROR]   - portfolio_manager 类型: {type(portfolio_manager).__name__}")
                        traceback.print_exc()
        
        print(f"\n[DEBUG] McpPortfolioManagerGroup: 总共添加了 {added_count} 个 portfolio adapter")
        
        if added_count == 0:
            return f"ERROR: 没有成功添加任何适配器到 PortfolioManager"
        
        # 生成 hierarchical_manager_id（简化版本，使用时间戳和计数器）
        import time
        timestamp = int(time.time() * 1000) % 1000000  # 取后6位时间戳
        counter = len(_asset_portfolio_managers) % 1000  # 取后3位计数器
        hierarchical_manager_id = f"H_{timestamp}_{counter}"
        
        # 存储到第一个 manager 中（用于向后兼容）
        first_manager.hierarchical_manager = portfolio_manager
        first_manager.hierarchical_manager_id = hierarchical_manager_id
        first_manager.hierarchical_scenario_ids = scenario_ids_to_use  # 保存使用的场景ID列表
        
        # 存储到全局字典中（用于跨资产查询）
        _hierarchical_managers[hierarchical_manager_id] = {
            'manager': first_manager,  # 第一个 manager 作为基础
            'portfolio_manager': portfolio_manager,
            'managers': managers,  # 所有相关的 managers
            'scenario_ids': scenario_ids_to_use,
            'manager_ids': [mgr_id for mgr_id in _asset_portfolio_managers if _asset_portfolio_managers[mgr_id] in managers]
        }
        print(f"[DEBUG] McpPortfolioManagerGroup: 存储 hierarchical_manager_id={hierarchical_manager_id} 到全局字典")
        print(f"[DEBUG]   - 包含 {len(managers)} 个 managers")
        print(f"[DEBUG]   - 场景ID列表: {scenario_ids_to_use}")
        
        # 返回时加上 @ 前缀
        return f"@{hierarchical_manager_id}"
    
    except Exception as e:
        traceback.print_exc()
        return f"ERROR: {str(e)}"


@xl_func(macro=False, recalc_on_open=False, thread_safe=False)
def McpClearPortfolioAdapters():
    """清空所有存储的 AssetPortfolioManager 对象"""
    global _asset_portfolio_managers, _hierarchical_managers
    _asset_portfolio_managers.clear()
    _hierarchical_managers.clear()
    return "已清空所有资产组合管理器"


@xl_func(macro=False, recalc_on_open=False, thread_safe=False, auto_resize=True)
def McpListPortfolioAdapters():
    """列出所有已创建的 AssetPortfolioManager ID"""
    if not _asset_portfolio_managers:
        return [['ManagerID', 'AssetType', 'ScenarioGroupId', 'ValuationDate'], ['', '', '', '']]
    
    results = []
    for manager_id, manager in _asset_portfolio_managers.items():
        results.append([
            manager_id,
            manager.asset_type,
            manager.scenario_group_id,
            manager.valuation_date
        ])
    
    header = [['ManagerID', 'AssetType', 'ScenarioGroupId', 'ValuationDate']]
    return header + results
