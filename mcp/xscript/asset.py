from mcp.utils.enums import ModelType, XScriptRunMode
from mcp.xscript.utils import SttUtils


class McpAsset:

    def __init__(self):
        self.fields = []
        self.key_parse_func = {
            'NumSimulation': lambda x: int(float(x)),
            # 'ReferenceDate': lambda x: int(to_excel_ordinal(x)),
        }
        self.mcp_fields = []

    def execute(self, d, xscript):
        args = []
        for key, val in self.mcp_fields:
            raw = SttUtils.get_value(key, d, val)
            if key in self.key_parse_func:
                raw = self.key_parse_func[key](raw)
            args.append(raw)
        print(f"pricingSimpleBS args: {args}")
        return xscript.pricingSimpleBS(*args)


class McpAssetFx(McpAsset):

    def __init__(self):
        super().__init__()
        self.fields = [
            ("rd", None),
            ("rf", None),
            # ("Currency", None),
        ]
        self.mcp_fields = [
            ('ReferenceDate', None),
            ('Spot', None),
            ('Vol', None),
            ('rd', None),
            ('rf', None),

            # ('Normal', False),
            ('ModelType', ModelType.BlackSchole),
            ('Events', None),
            ('NumSimulation', 1000),

            ('seed', 0),
            ('fuzzy', True),
            ('defEps', 0.0001),
            ('skipDoms', False),
            ('compile', True),
            ('RunMode', XScriptRunMode.AutoSelect),
            ('logLevel', 4),
            ('modelParam', '[0.52139, 0.0463869, 0.00206347, -0.00126779, 0.0511969]'),
        ]


class McpAssetEquity(McpAsset):

    def __init__(self):
        super().__init__()
        self.fields = [
            ("r", None),
            ("q", None),
            ("Spot", None),
        ]
        self.mcp_fields = [
            ('ReferenceDate', None),
            ('Spot', None),
            ('Vol', None),
            ('r', None),
            ('q', None),

            # ('Normal', False),
            ('ModelType', ModelType.BlackSchole),
            ('Events', None),
            ('NumSimulation', 1000),

            ('seed', 0),
            ('fuzzy', True),
            ('defEps', 0.0001),
            ('skipDoms', False),
            ('compile', True),
            # ('logLevel', 0),
            ('RunMode', XScriptRunMode.AutoSelect),
            ('logLevel', 4),
            ('modelParam', '[0.52139, 0.0463869, 0.00206347, -0.00126779, 0.0511969]'),
        ]


class McpAssetFactory:

    @staticmethod
    def gen_asset(asset_name):
        lower_name = str(asset_name).lower()
        if lower_name == 'fx':
            return McpAssetFx()
        elif lower_name == 'equity':
            return McpAssetEquity()
        else:
            raise Exception(f"Unsupported asset {asset_name}")
