"""TDX F10 接口 adapter 级集成测试（08-11 补测）。

此前 32 个 F10 接口仅有 provider 声明校验测试，无归一化链路验证。
本文件 mock 7615 payload（走真实 parse_tqlex_tables + f10_context +
normalize_f10_row），覆盖通用单表、多表 meta 合并与错误响应路径。
"""

from __future__ import annotations

from axdata_source_tdx.f10_request import request_f10_interface
from axdata_source_tdx.tdx_f10_specs import F10_INTERFACE_SPECS


class FakeClient:
    """TdxTqlexClient 最小替身：request() 返回注入的 7615 payload。"""

    def __init__(self, payload: dict) -> None:
        self._payload = payload
        self.last_entry: str | None = None
        self.last_body: dict | None = None

    def request(self, entry: str, body: dict) -> dict:
        self.last_entry = entry
        self.last_body = body
        return self._payload


def _payload(tables: list[tuple[list[str], list[dict]]]) -> dict:
    """构造 7615 JSON 响应：[(ColName, Content行list), ...] 每元素一张表。"""
    return {
        "ErrorCode": 0,
        "ResultSets": [
            {"ColName": cols, "Content": rows} for cols, rows in tables
        ],
    }


def test_f10_company_profile_normalizes_single_table():
    """通用单表路径：T 前缀源键 + code 上下文注入 instrument_id/symbol。"""
    spec = F10_INTERFACE_SPECS["stock_company_profile_tdx"]
    client = FakeClient(_payload([
        (["T035", "T031", "T042", "mgmz"],
         [{"T035": "A股", "T031": "19940509", "T042": 5.2, "mgmz": 1.0}]),
    ]))
    rows = request_f10_interface(client, spec, {"code": "000001.SZ"})
    assert len(rows) == 1
    row = rows[0]
    assert row["instrument_id"] == "000001.SZ"
    assert row["symbol"] == "000001"
    assert row["stock_type"] == "A股"
    assert row["list_date"] == "19940509"
    assert row["issue_price"] == 5.2
    assert row["par_value"] == 1.0
    assert client.last_entry == "CWServ.tdxf10_gg_gsgk"


def test_f10_dividend_history_normalizes_with_body_params():
    """通用单表路径：混合源键 + 特殊 body_template（Params 列表）。"""
    spec = F10_INTERFACE_SPECS["stock_dividend_history_tdx"]
    client = FakeClient(_payload([
        (["rq", "T003", "T004", "T006", "T021", "T023", "T036", "glzfl"],
         [{"rq": "2025", "T003": "20260315", "T004": "10派3.5元",
           "T006": 1.82, "T021": "20260710", "T023": "20260711",
           "T036": "实施", "glzfl": 19.2}]),
    ]))
    rows = request_f10_interface(client, spec, {"code": "600519.SH"})
    assert len(rows) == 1
    row = rows[0]
    assert row["symbol"] == "600519"
    assert row["report_period"] == "2025"
    assert row["plan"] == "10派3.5元"
    assert row["eps"] == 1.82
    assert row["record_date"] == "20260710"
    assert row["ex_dividend_date"] == "20260711"
    assert row["payout_ratio_pct"] == 19.2
    # body 渲染：Params 按 f10_context 注入 code
    assert client.last_body == {"Params": ["600519", "fh"]}


def test_f10_forecast_consensus_merges_meta_from_second_table():
    """多表路径：main_table_index=1 + 表 0/4 行合并进 meta（预测机构数等）。"""
    spec = F10_INTERFACE_SPECS["stock_forecast_consensus_tdx"]
    client = FakeClient(_payload([
        (["t023"], [{"t023": 8}]),
        (["nyear", "flag", "T036", "T037", "T033"],
         [{"nyear": 2026, "flag": "A", "T036": 2.35, "T037": 2.61, "T033": 29500}]),
        ([], []),
        ([], []),
        ([], [{"N001": 88}]),
    ]))
    rows = request_f10_interface(client, spec, {"code": "000001.SZ"})
    assert len(rows) == 1
    row = rows[0]
    assert row["forecast_start_year"] == 2026
    assert row["eps_year1"] == 2.35
    assert row["eps_year2"] == 2.61
    assert row["net_profit_year1"] == 29500
    assert row["forecast_institution_count"] == 8


def test_f10_error_code_raises_value_error():
    """错误响应路径：ErrorCode != 0 抛 ValueError（不产出脏数据）。"""
    spec = F10_INTERFACE_SPECS["stock_company_profile_tdx"]
    client = FakeClient({"ErrorCode": 1, "ResultSets": []})
    try:
        request_f10_interface(client, spec, {"code": "000001.SZ"})
    except ValueError as exc:
        assert "ErrorCode" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError for ErrorCode=1")
