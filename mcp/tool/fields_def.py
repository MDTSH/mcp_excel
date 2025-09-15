from mcp.utils.enums import *
from mcp.wrapper import *


class InitFields:
    @staticmethod
    def AsianOption():
        return [
            [
                ("CallPut", "const"),
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("AveRate", "float"),
                ("FirstAverageDate", "date"),
                ("ExpiryDate", "date"),
                ("SettlementDate", "date"),
                ("StrikePx", "float"),
                ("ForwardPx", "float"),
                ("AccRate", "float"),
                ("UndRate", "float"),
                ("Volatility", "float"),
                ("PremiumDate", "date"),
                ("FixingFrequency", "const", Frequency.Monthly, "Monthly"),
                ("LastAverageDate", "date"),
                ("CalculatedTarget", "const", CalculatedTarget.CCY1),
                ("AverageMethod", "const", AverageMethod.Arithmetic, "Arithmetic"),
                ("StrikeType", "const", StrikeType.Fixed, "Fixed"),
                ("PricingMethod", "const", PricingMethod.BINOMIAL, "BINOMIAL"),
                ("BuySell", "const"),
                ("FaceAmount", "float", 1),
                ("NumSimulation", "int", 10000),

                ("FixingDateAdjuster", "const", DateAdjusterRule.ModifiedFollowing, "ModifiedFollowing"),
                ("KeepEndOfMonth", "bool", True),
                ("FixingLongStub", "bool", False),
                ("FixingEndStub", "bool", True),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("TimeStep", "int", 10),

                ("PipsUnit", "float", 10000),
            ],
            [
                ("CallPut", "const"),
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("AveRate", "float"),
                ("FirstAverageDate", "date"),
                ("ExpiryDate", "date"),
                ("SettlementDate", "date"),
                ("StrikePx", "float"),
                ("AccRate", "float"),
                ("UndRate", "float"),
                ("Volatility", "float"),
                ("PremiumDate", "date"),
                ("NumFixings", "int"),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("AverageMethod", "const", AverageMethod.Arithmetic, "Arithmetic"),
                ("StrikeType", "const", StrikeType.Fixed, "Fixed"),
                ("PricingMethod", "const", PricingMethod.BINOMIAL, "BINOMIAL"),
                ("BuySell", "const"),
                ("FaceAmount", "float", 1),
                ("TimeStep", "int", 10),
                ("NumSimulation", "int", 10000),

                ("PipsUnit", "float", 10000),
            ],
        ]
