"""Official exchange source request interface catalog."""

from __future__ import annotations

from axdata_core.sources.base import (
    RequestExample,
    RequestField,
    RequestParameter,
    SourceRequestInterface,
)
from axdata_core.schema import STOCK_BASIC_FIELDS


STOCK_BASIC_INFO_FIELD_DESCRIPTION_ZH_OVERRIDES = {
    "security_full_name": "证券全称；上交所通常提供，其他交易所可能为空。",
    "market_code": "市场板块代码；上交所、北交所可能提供，没有时为空。",
    "industry_code": "行业代码；上交所通常提供，其他交易所可能为空。",
    "industry": "行业名称；各交易所口径不同，源端提供时返回。",
    "region_code": "地区代码；上交所通常提供，其他交易所可能为空。",
    "region": "地区名称；上交所、北交所可能提供，没有时为空。",
    "company_code": "公司代码；上交所通常提供，其他交易所可能为空。",
    "company_short_name": "公司简称；上交所通常提供，其他交易所可能为空。",
    "company_full_name": "公司法定全称；上交所通常提供，其他交易所可能为空。",
    "company_short_name_en": "公司英文简称；上交所、北交所可能提供，没有时为空。",
    "company_full_name_en": "公司英文全称；上交所通常提供，其他交易所可能为空。",
    "total_share": "总股本，单位：亿股；深交所、北交所通常提供，上交所当前列表可能为空。",
    "float_share": "流通股本，单位：亿股；深交所、北交所通常提供，上交所当前列表可能为空。",
    "is_profit": "是否尚未盈利；深交所可能提供，没有时为空。",
    "is_vie": "是否具有协议控制架构；深交所可能提供，没有时为空。",
    "has_weighted_voting_rights": "是否具有表决权差异安排；深交所可能提供，没有时为空。",
    "sponsor": "保荐机构或主办券商；北交所通常提供，其他交易所可能为空。",
    "share_report_date": "股本数据报告日期，格式 YYYYMMDD；北交所通常提供，其他交易所可能为空。",
}


STOCK_BASIC_INFO_FIELDS = tuple(
    RequestField(
        name=field.name,
        dtype=field.dtype,
        description=field.description,
        description_zh=STOCK_BASIC_INFO_FIELD_DESCRIPTION_ZH_OVERRIDES.get(
            field.name,
            field.description_zh,
        ),
    )
    for field in STOCK_BASIC_FIELDS
)


INTERFACES: dict[str, SourceRequestInterface] = {
    "stock_trade_calendar_exchange": SourceRequestInterface(
        name="stock_trade_calendar_exchange",
        display_name_zh="交易日历",
        source_code="exchange",
        source_name_zh="交易所",
        category="基础数据",
        request_mode="source_request",
        first_stage_strategy="临时请求深交所官方交易日历，默认不入库。",
        source_ability="SZSE official trading calendar",
        description=(
            "Return SZSE official trading-calendar rows. If no date parameter is provided, "
            "AxData returns the current natural year. year returns the full year. "
            "start_date/end_date returns the exact date range and has priority over year."
        ),
        parameters=(
            RequestParameter(
                name="year",
                dtype="integer/string",
                required=False,
                description="Natural year, for example 2026. Ignored when start_date or end_date is provided.",
                description_zh="年份，例如 2026；传 start_date/end_date 时优先按日期范围查询。",
            ),
            RequestParameter(
                name="start_date",
                dtype="string",
                required=False,
                description="Start date, YYYYMMDD or YYYY-MM-DD.",
                description_zh="开始日期，格式 YYYYMMDD 或 YYYY-MM-DD。",
            ),
            RequestParameter(
                name="end_date",
                dtype="string",
                required=False,
                description="End date, YYYYMMDD or YYYY-MM-DD.",
                description_zh="结束日期，格式 YYYYMMDD 或 YYYY-MM-DD。",
            ),
        ),
        fields=(
            RequestField(
                name="cal_date",
                dtype="date/string",
                description="Calendar date, YYYYMMDD.",
                description_zh="自然日期，格式 YYYYMMDD。",
            ),
            RequestField(
                name="is_open",
                dtype="boolean",
                description="Whether the market is open.",
                description_zh="是否交易日。",
            ),
            RequestField(
                name="pretrade_date",
                dtype="date/string",
                description="Previous trading day.",
                description_zh="上一个交易日；非交易日也返回最近上一交易日。",
            ),
            RequestField(
                name="next_trade_date",
                dtype="date/string",
                description="Next trading day.",
                description_zh="下一个交易日；非交易日也返回最近下一交易日。",
            ),
        ),
        example=RequestExample(
            request={
                "params": {
                    "start_date": "20260617",
                    "end_date": "20260622",
                },
                "persist": False,
            },
            response=(
                {
                    "cal_date": "20260617",
                    "is_open": True,
                    "pretrade_date": "20260616",
                    "next_trade_date": "20260618",
                },
                {
                    "cal_date": "20260618",
                    "is_open": True,
                    "pretrade_date": "20260617",
                    "next_trade_date": "20260622",
                },
                {
                    "cal_date": "20260619",
                    "is_open": False,
                    "pretrade_date": "20260618",
                    "next_trade_date": "20260622",
                },
                {
                    "cal_date": "20260622",
                    "is_open": True,
                    "pretrade_date": "20260618",
                    "next_trade_date": "20260623",
                },
            ),
        ),
    ),
    "stock_historical_list_exchange": SourceRequestInterface(
        name="stock_historical_list_exchange",
        display_name_zh="历史股票列表",
        source_code="exchange",
        source_name_zh="交易所",
        category="基础数据",
        request_mode="source_request",
        first_stage_strategy="临时请求交易所官方列表，按上市日期和退市日期计算指定日期已上市股票池，默认不入库。",
        source_ability="Official exchange stock lifecycle list",
        description=(
            "Return the official-exchange stock universe active on one or more dates. "
            "Rows are filtered by list_date <= target date and empty delist_date or delist_date >= target date."
        ),
        parameters=(
            RequestParameter(
                name="trade_date",
                dtype="string/list",
                required=False,
                description="Target date or date list, YYYYMMDD or YYYY-MM-DD.",
                description_zh="目标日期或日期列表，格式 YYYYMMDD 或 YYYY-MM-DD。",
            ),
            RequestParameter(
                name="start_date",
                dtype="string",
                required=False,
                description="Start date for a continuous date range, YYYYMMDD or YYYY-MM-DD.",
                description_zh="连续日期范围的开始日期，格式 YYYYMMDD 或 YYYY-MM-DD。",
            ),
            RequestParameter(
                name="end_date",
                dtype="string",
                required=False,
                description="End date for a continuous date range, YYYYMMDD or YYYY-MM-DD.",
                description_zh="连续日期范围的结束日期，格式 YYYYMMDD 或 YYYY-MM-DD。",
            ),
            RequestParameter(
                name="exchange",
                dtype="string/list",
                required=False,
                description="Exchange filter: SSE, SZSE, BSE. Empty means all supported exchanges.",
                description_zh="交易所筛选：SSE、SZSE、BSE；不传默认全部。",
            ),
        ),
        fields=(
            RequestField(
                name="trade_date",
                dtype="date/string",
                description="Target date for this stock-universe row, YYYYMMDD.",
                description_zh="本行对应的目标日期，格式 YYYYMMDD。",
            ),
            RequestField(
                name="instrument_id",
                dtype="string",
                description="AxData instrument id.",
                description_zh="AxData 统一证券代码，例如 000001.SZ、600000.SH、430047.BJ。",
            ),
            RequestField(
                name="symbol",
                dtype="string",
                description="Raw exchange symbol.",
                description_zh="交易所原始证券代码。",
            ),
            RequestField(
                name="exchange",
                dtype="string",
                description="Exchange code.",
                description_zh="交易所代码：SSE、SZSE、BSE。",
            ),
            RequestField(
                name="name",
                dtype="string",
                description="Security short name.",
                description_zh="证券简称。",
            ),
            RequestField(
                name="market",
                dtype="string",
                description="Market board.",
                description_zh="市场板块，例如主板、创业板、科创板、北交所。",
            ),
            RequestField(
                name="list_date",
                dtype="date/string",
                description="Listing date, YYYYMMDD.",
                description_zh="上市日期，格式 YYYYMMDD。",
            ),
            RequestField(
                name="delist_date",
                dtype="date/string",
                description="Delisting date, YYYYMMDD.",
                description_zh="退市日期；未退市为空。",
            ),
            RequestField(
                name="listing_status",
                dtype="string",
                description="Lifecycle status.",
                description_zh="上市状态：listed 或 delisted。",
            ),
        ),
        example=RequestExample(
            request={
                "params": {
                    "trade_date": "20240102",
                    "exchange": "SZSE",
                },
                "persist": False,
            },
            response=(
                {
                    "trade_date": "20240102",
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "exchange": "SZSE",
                    "name": "平安银行",
                    "market": "主板",
                    "list_date": "19910403",
                    "delist_date": None,
                    "listing_status": "listed",
                },
                {
                    "trade_date": "20240102",
                    "instrument_id": "000005.SZ",
                    "symbol": "000005",
                    "exchange": "SZSE",
                    "name": "ST星源",
                    "market": None,
                    "list_date": "19901210",
                    "delist_date": "20240426",
                    "listing_status": "delisted",
                },
            ),
        ),
    ),
    "stock_basic_info_exchange": SourceRequestInterface(
        name="stock_basic_info_exchange",
        display_name_zh="股票基础信息",
        source_code="exchange",
        source_name_zh="交易所",
        category="基础数据",
        request_mode="source_request",
        first_stage_strategy="临时请求交易所官方当前股票列表，返回股票基础资料，默认不入库。",
        source_ability="Official exchange current stock basic list",
        description=(
            "Return current official-exchange stock basic information. "
            "This interface has no date parameter and represents the latest official list口径. "
            "Fields differ by exchange; unavailable source fields are returned as null."
        ),
        parameters=(
            RequestParameter(
                name="exchange",
                dtype="string/list",
                required=False,
                description="Exchange filter: SSE, SZSE, BSE. Empty means all supported exchanges.",
                description_zh="交易所筛选：SSE、SZSE、BSE；不传默认全部。",
            ),
            RequestParameter(
                name="code",
                dtype="string/list",
                required=False,
                description="Stock code filter, for example 000001, 000001.SZ, sz000001, or a list.",
                description_zh="股票代码筛选，例如 000001、000001.SZ、sz000001；支持列表或逗号分隔。",
            ),
            RequestParameter(
                name="name",
                dtype="string/list",
                required=False,
                description="Security short-name filter, exact match.",
                description_zh="证券简称筛选，精确匹配；支持列表或逗号分隔。",
            ),
        ),
        fields=STOCK_BASIC_INFO_FIELDS,
        example=RequestExample(
            request={
                "params": {
                    "code": "000001.SZ",
                },
                "persist": False,
            },
            response=(
                {
                    "instrument_id": "000001.SZ",
                    "symbol": "000001",
                    "exchange": "SZSE",
                    "asset_type": "stock",
                    "name": "平安银行",
                    "security_full_name": None,
                    "market_code": None,
                    "market": "主板",
                    "industry_code": None,
                    "industry": "J 金融业",
                    "region_code": None,
                    "region": None,
                    "company_code": None,
                    "company_short_name": None,
                    "company_full_name": None,
                    "company_short_name_en": None,
                    "company_full_name_en": None,
                    "listing_status": "listed",
                    "list_date": "19910403",
                    "delist_date": None,
                    "total_share": 194.05918198,
                    "float_share": 194.05685028,
                    "is_profit": "-",
                    "is_vie": "-",
                    "has_weighted_voting_rights": "-",
                    "sponsor": None,
                    "share_report_date": None,
                },
            ),
        ),
    ),
    "stock_prbook_sse": SourceRequestInterface(
        name="stock_prbook_sse",
        display_name_zh="定期报告预约披露（上交所）",
        source_code="exchange",
        source_name_zh="交易所",
        category="基础数据",
        request_mode="source_request",
        first_stage_strategy=(
            "临时请求上交所定期报告预约披露接口（query.sse.com.cn JSONP），"
            "返回首次预约日/变更日/实际披露日，默认不入库。"
        ),
        source_ability="SSE periodic report appointment disclosure",
        description=(
            "Return SSE listed companies' periodic report appointment dates "
            "(first appointment, up to 3 change dates, actual disclosure date). "
            "SSE-only; SZSE has a separate channel."
        ),
        parameters=(
            RequestParameter(
                name="code",
                dtype="string",
                required=True,
                description="Stock code, e.g. 600101.",
                description_zh="股票代码（沪市），例如 600101。",
            ),
            RequestParameter(
                name="publish_year",
                dtype="string",
                required=False,
                description="Report year; default current year.",
                description_zh="报告年度；默认当前年。",
            ),
        ),
        fields=(
            RequestField(name="instrument_id", dtype="string",
                         description="AxData unified security code, e.g. 600101.SH.",
                         description_zh="AxData 统一证券代码，例如 600101.SH。"),
            RequestField(name="symbol", dtype="string",
                         description="Exchange six-digit code.",
                         description_zh="交易所六位代码。"),
            RequestField(name="exchange", dtype="string",
                         description="SSE.",
                         description_zh="交易所（SSE）。"),
            RequestField(name="bulletin_type", dtype="string",
                         description="SSE bulletin type code (L011-L014).",
                         description_zh="上交所公告类型码（L011-L014）。"),
            RequestField(name="report_type", dtype="string",
                         description="Report type name: 一季报/半年报/三季报/年报.",
                         description_zh="报告类型：一季报/半年报/三季报/年报。"),
            RequestField(name="publish_year", dtype="string",
                         description="Report year, e.g. 2026.",
                         description_zh="报告年度，例如 2026。"),
            RequestField(name="first_publish_date", dtype="string",
                         description="First appointment date YYYYMMDD.",
                         description_zh="首次预约披露日 YYYYMMDD。"),
            RequestField(name="change_date_1", dtype="string",
                         description="First change date YYYYMMDD or empty.",
                         description_zh="第一次变更日 YYYYMMDD，无则空。"),
            RequestField(name="change_date_2", dtype="string",
                         description="Second change date YYYYMMDD or empty.",
                         description_zh="第二次变更日 YYYYMMDD，无则空。"),
            RequestField(name="change_date_3", dtype="string",
                         description="Third change date YYYYMMDD or empty.",
                         description_zh="第三次变更日 YYYYMMDD，无则空。"),
            RequestField(name="actual_date", dtype="string",
                         description="Actual disclosure date YYYYMMDD or empty.",
                         description_zh="实际披露日 YYYYMMDD，未披露则空。"),
        ),
        example=RequestExample(
            request={"params": {"code": "600101"}, "persist": False},
            response=(
                {
                    "instrument_id": "600101.SH",
                    "symbol": "600101",
                    "exchange": "SSE",
                    "bulletin_type": "L012",
                    "report_type": "半年报",
                    "publish_year": "2026",
                    "first_publish_date": "20260827",
                    "change_date_1": "",
                    "change_date_2": "",
                    "change_date_3": "",
                    "actual_date": "",
                },
            ),
        ),
    ),
}
