from app.services.dhs_analytics_service import DHSAnalyticsService


def test_dhs_metadata():
    meta = DHSAnalyticsService.get_metadata()
    assert "indicators" in meta
    assert "countries" in meta
    assert len(meta["indicators"]) >= 5
    assert len(meta["countries"]) >= 5


def test_descriptive_stats_computation():
    stats_res = DHSAnalyticsService.get_descriptive_stats(
        country_codes=["ZMB", "KEN", "NGA"],
        indicator="u5_mortality"
    )

    assert stats_res["indicator"] == "u5_mortality"
    assert "pooled_stats" in stats_res
    assert stats_res["pooled_stats"]["mean"] > 0
    assert "per_country" in stats_res
    assert "ZMB" in stats_res["per_country"]
    assert stats_res["per_country"]["ZMB"]["count"] == 30
    assert "ci_95" in stats_res["per_country"]["ZMB"]


def test_inferential_t_test():
    res = DHSAnalyticsService.run_inferential_analysis(
        test_type="t_test",
        country_codes=["ZMB", "KEN"],
        indicator_x="u5_mortality"
    )

    assert res["test_type"] == "t_test"
    summary = res["summary"]
    assert "t_statistic" in summary
    assert "p_value" in summary
    assert "cohens_d" in summary
    assert summary["group1"]["code"] == "ZMB"


def test_inferential_anova():
    res = DHSAnalyticsService.run_inferential_analysis(
        test_type="anova",
        country_codes=["ZMB", "KEN", "NGA", "ZAF"],
        indicator_x="stunting_prevalence"
    )

    summary = res["summary"]
    assert "f_statistic" in summary
    assert "p_value" in summary
    assert summary["df_between"] == 3


def test_inferential_correlation_and_regression():
    res = DHSAnalyticsService.run_inferential_analysis(
        test_type="linear_regression",
        country_codes=["ZMB", "KEN", "NGA"],
        indicator_x="u5_mortality",
        indicator_y="stunting_prevalence"
    )

    summary = res["summary"]
    assert "pearson_r" in summary
    assert "ols_slope" in summary
    assert "r_squared" in summary
    assert len(summary["scatter_points"]) > 0
    assert len(summary["trend_line"]) == 2
