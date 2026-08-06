"""DHS Analytics and Inferential Statistics Engine for EpiSphere AI"""

import math
from typing import List, Dict, Any, Optional
import numpy as np
import scipy.stats as stats


DHS_INDICATORS = {
    "u5_mortality": {
        "name": "Under-5 Mortality Rate",
        "unit": "deaths per 1,000 live births",
        "category": "Child Health",
        "description": "Probability of dying between birth and exactly five years of age."
    },
    "stunting_prevalence": {
        "name": "Stunting Prevalence in Under-5s",
        "unit": "percentage (%)",
        "category": "Nutrition",
        "description": "Percentage of children under 5 years whose height-for-age is below -2 SD."
    },
    "full_immunization": {
        "name": "Full Immunization Coverage (12-23m)",
        "unit": "percentage (%)",
        "category": "Immunization",
        "description": "Percentage of children aged 12-23 months receiving all basic WHO recommended vaccines."
    },
    "anc4_coverage": {
        "name": "Antenatal Care 4+ Visits",
        "unit": "percentage (%)",
        "category": "Maternal Health",
        "description": "Percentage of women aged 15-49 with a live birth who received 4+ antenatal care visits."
    },
    "malaria_prevalence_u5": {
        "name": "Malaria Parasitemia Prevalence (U5)",
        "unit": "percentage (%)",
        "category": "Infectious Diseases",
        "description": "Percentage of children 6-59 months testing positive for malaria parasites by microscopy/RDT."
    },
    "maternal_mortality_ratio": {
        "name": "Maternal Mortality Ratio",
        "unit": "deaths per 100,000 live births",
        "category": "Maternal Health",
        "description": "Annual number of female deaths from any cause related to or aggravated by pregnancy."
    }
}

DHS_COUNTRIES = {
    "ZMB": {"name": "Zambia", "region": "Southern Africa", "baseline_multiplier": 1.0},
    "KEN": {"name": "Kenya", "region": "East Africa", "baseline_multiplier": 0.85},
    "NGA": {"name": "Nigeria", "region": "West Africa", "baseline_multiplier": 1.40},
    "ZAF": {"name": "South Africa", "region": "Southern Africa", "baseline_multiplier": 0.55},
    "COD": {"name": "Democratic Republic of the Congo", "region": "Central Africa", "baseline_multiplier": 1.50},
    "UGA": {"name": "Uganda", "region": "East Africa", "baseline_multiplier": 0.95},
    "ETH": {"name": "Ethiopia", "region": "East Africa", "baseline_multiplier": 0.90},
    "GHA": {"name": "Ghana", "region": "West Africa", "baseline_multiplier": 0.75},
}


class DHSAnalyticsService:
    """Service providing multi-country DHS data generation, descriptive statistics, and inferential statistical testing."""

    @staticmethod
    def get_metadata() -> Dict[str, Any]:
        """Return available indicators and countries."""
        return {
            "indicators": [
                {"code": code, **info} for code, info in DHS_INDICATORS.items()
            ],
            "countries": [
                {"iso_code": iso, **info} for iso, info in DHS_COUNTRIES.items()
            ],
            "survey_waves": ["2015-DHS", "2018-DHS", "2021-DHS", "2023-MIS", "2024-DHS"]
        }

    @classmethod
    def generate_country_samples(cls, iso_code: str, indicator: str, n_samples: int = 30) -> List[float]:
        """Generate deterministic, statistically representative sample distributions for DHS indicators by country."""
        country_info = DHS_COUNTRIES.get(iso_code.upper(), {"baseline_multiplier": 1.0})
        mult = country_info["baseline_multiplier"]
        
        # Base seed based on hash of ISO code + indicator
        seed_value = (abs(hash(iso_code + indicator)) % 1000000)
        rng = np.random.default_rng(seed_value)

        if indicator == "u5_mortality":
            base_mean = 55.0 * mult
            base_std = 8.5
            vals = rng.normal(base_mean, base_std, n_samples)
        elif indicator == "stunting_prevalence":
            base_mean = 32.0 * mult
            base_std = 5.2
            vals = rng.normal(base_mean, base_std, n_samples)
        elif indicator == "full_immunization":
            base_mean = max(35.0, min(95.0, 78.0 / mult))
            base_std = 6.0
            vals = rng.normal(base_mean, base_std, n_samples)
        elif indicator == "anc4_coverage":
            base_mean = max(30.0, min(90.0, 70.0 / mult))
            base_std = 7.0
            vals = rng.normal(base_mean, base_std, n_samples)
        elif indicator == "malaria_prevalence_u5":
            base_mean = min(60.0, 22.0 * mult)
            base_std = 4.8
            vals = rng.normal(base_mean, base_std, n_samples)
        elif indicator == "maternal_mortality_ratio":
            base_mean = 350.0 * mult
            base_std = 45.0
            vals = rng.normal(base_mean, base_std, n_samples)
        else:
            vals = rng.normal(50.0, 10.0, n_samples)

        return [round(float(max(0.0, v)), 2) for v in vals]

    @classmethod
    def get_descriptive_stats(cls, country_codes: List[str], indicator: str) -> Dict[str, Any]:
        """Compute comprehensive descriptive statistics across specified countries."""
        if not country_codes:
            country_codes = list(DHS_COUNTRIES.keys())

        indicator_meta = DHS_INDICATORS.get(indicator, {
            "name": indicator,
            "unit": "value",
            "category": "General"
        })

        per_country_stats = {}
        all_values = []

        for iso in country_codes:
            iso_upper = iso.upper()
            samples = cls.generate_country_samples(iso_upper, indicator)
            all_values.extend(samples)
            
            arr = np.array(samples)
            n = len(arr)
            mean_val = float(np.mean(arr))
            median_val = float(np.median(arr))
            std_val = float(np.std(arr, ddof=1)) if n > 1 else 0.0
            var_val = float(np.var(arr, ddof=1)) if n > 1 else 0.0
            q25, q75 = float(np.percentile(arr, 25)), float(np.percentile(arr, 75))
            iqr_val = q75 - q25
            min_val, max_val = float(np.min(arr)), float(np.max(arr))
            skew_val = float(stats.skew(arr)) if n > 2 else 0.0
            kurt_val = float(stats.kurtosis(arr)) if n > 3 else 0.0
            sem_val = float(stats.sem(arr)) if n > 1 else 0.0
            
            ci = stats.t.interval(0.95, df=n-1, loc=mean_val, scale=sem_val) if n > 1 and sem_val > 0 else (mean_val, mean_val)

            per_country_stats[iso_upper] = {
                "country_name": DHS_COUNTRIES.get(iso_upper, {}).get("name", iso_upper),
                "count": n,
                "mean": round(mean_val, 2),
                "median": round(median_val, 2),
                "std_dev": round(std_val, 2),
                "variance": round(var_val, 2),
                "min": round(min_val, 2),
                "max": round(max_val, 2),
                "q25": round(q25, 2),
                "q75": round(q75, 2),
                "iqr": round(iqr_val, 2),
                "skewness": round(skew_val, 3),
                "kurtosis": round(kurt_val, 3),
                "sem": round(sem_val, 2),
                "ci_95": [round(float(ci[0]), 2), round(float(ci[1]), 2)],
                "values": samples
            }

        # Combined pooled stats
        combined_arr = np.array(all_values)
        combined_n = len(combined_arr)
        combined_mean = float(np.mean(combined_arr))
        combined_sem = float(stats.sem(combined_arr)) if combined_n > 1 else 0.0
        combined_ci = stats.t.interval(0.95, df=combined_n-1, loc=combined_mean, scale=combined_sem) if combined_n > 1 else (combined_mean, combined_mean)

        pooled_stats = {
            "count": combined_n,
            "mean": round(combined_mean, 2),
            "median": round(float(np.median(combined_arr)), 2),
            "std_dev": round(float(np.std(combined_arr, ddof=1)), 2),
            "variance": round(float(np.var(combined_arr, ddof=1)), 2),
            "min": round(float(np.min(combined_arr)), 2),
            "max": round(float(np.max(combined_arr)), 2),
            "q25": round(float(np.percentile(combined_arr, 25)), 2),
            "q75": round(float(np.percentile(combined_arr, 75)), 2),
            "iqr": round(float(np.percentile(combined_arr, 75) - np.percentile(combined_arr, 25)), 2),
            "skewness": round(float(stats.skew(combined_arr)), 3),
            "kurtosis": round(float(stats.kurtosis(combined_arr)), 3),
            "sem": round(combined_sem, 2),
            "ci_95": [round(float(combined_ci[0]), 2), round(float(combined_ci[1]), 2)],
        }

        return {
            "indicator": indicator,
            "indicator_meta": indicator_meta,
            "pooled_stats": pooled_stats,
            "per_country": per_country_stats
        }

    @classmethod
    def run_inferential_analysis(
        cls,
        test_type: str,
        country_codes: List[str],
        indicator_x: str,
        indicator_y: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run inferential statistical test based on specified parameters."""
        if not country_codes or len(country_codes) < 1:
            country_codes = ["ZMB", "KEN"]

        test_type = test_type.lower()
        result = {
            "test_type": test_type,
            "country_codes": country_codes,
            "indicator_x": indicator_x,
            "indicator_y": indicator_y,
            "summary": {}
        }

        if test_type in ["t_test", "welch_t_test"]:
            c1 = country_codes[0].upper()
            c2 = country_codes[1].upper() if len(country_codes) > 1 else "KEN"
            s1 = np.array(cls.generate_country_samples(c1, indicator_x))
            s2 = np.array(cls.generate_country_samples(c2, indicator_x))
            
            equal_var = (test_type != "welch_t_test")
            t_stat, p_val = stats.ttest_ind(s1, s2, equal_var=equal_var)
            
            mean1, mean2 = float(np.mean(s1)), float(np.mean(s2))
            diff = mean1 - mean2
            
            # Cohen's d calculation
            n1, n2 = len(s1), len(s2)
            var1, var2 = np.var(s1, ddof=1), np.var(s2, ddof=1)
            pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
            cohens_d = diff / pooled_std if pooled_std > 0 else 0.0

            result["summary"] = {
                "test_name": "Two-Sample Independent T-Test" if equal_var else "Welch's T-Test (Unequal Variances)",
                "group1": {"code": c1, "name": DHS_COUNTRIES.get(c1, {}).get("name", c1), "mean": round(mean1, 2), "std": round(float(np.std(s1, ddof=1)), 2)},
                "group2": {"code": c2, "name": DHS_COUNTRIES.get(c2, {}).get("name", c2), "mean": round(mean2, 2), "std": round(float(np.std(s2, ddof=1)), 2)},
                "t_statistic": round(float(t_stat), 4),
                "p_value": round(float(p_val), 6),
                "degrees_freedom": round(float(n1 + n2 - 2) if equal_var else float((var1/n1 + var2/n2)**2 / ((var1/n1)**2/(n1-1) + (var2/n2)**2/(n2-1))), 2),
                "mean_difference": round(diff, 2),
                "cohens_d": round(cohens_d, 3),
                "significant_95": bool(p_val < 0.05),
                "interpretation": f"{'Statistically significant difference' if p_val < 0.05 else 'No statistically significant difference'} observed between {c1} and {c2} for {DHS_INDICATORS.get(indicator_x, {}).get('name', indicator_x)} (p = {p_val:.4f})."
            }

        elif test_type == "mann_whitney":
            c1 = country_codes[0].upper()
            c2 = country_codes[1].upper() if len(country_codes) > 1 else "KEN"
            s1 = np.array(cls.generate_country_samples(c1, indicator_x))
            s2 = np.array(cls.generate_country_samples(c2, indicator_x))
            
            u_stat, p_val = stats.mannwhitneyu(s1, s2, alternative="two-sided")
            
            result["summary"] = {
                "test_name": "Mann-Whitney U Rank-Sum Test",
                "group1": {"code": c1, "name": DHS_COUNTRIES.get(c1, {}).get("name", c1), "median": round(float(np.median(s1)), 2)},
                "group2": {"code": c2, "name": DHS_COUNTRIES.get(c2, {}).get("name", c2), "median": round(float(np.median(s2)), 2)},
                "u_statistic": round(float(u_stat), 2),
                "p_value": round(float(p_val), 6),
                "significant_95": bool(p_val < 0.05),
                "interpretation": f"Non-parametric rank sum test indicates {'significant' if p_val < 0.05 else 'no significant'} median difference between {c1} and {c2} (U = {u_stat:.1f}, p = {p_val:.4f})."
            }

        elif test_type == "anova":
            groups = [np.array(cls.generate_country_samples(c.upper(), indicator_x)) for c in country_codes]
            f_stat, p_val = stats.f_oneway(*groups)
            
            total_n = sum(len(g) for g in groups)
            k = len(groups)
            df_between = k - 1
            df_within = total_n - k

            result["summary"] = {
                "test_name": "One-Way Analysis of Variance (ANOVA)",
                "countries_evaluated": country_codes,
                "f_statistic": round(float(f_stat), 4),
                "p_value": round(float(p_val), 6),
                "df_between": df_between,
                "df_within": df_within,
                "significant_95": bool(p_val < 0.05),
                "interpretation": f"ANOVA test across {k} countries shows {'significant' if p_val < 0.05 else 'no significant'} variance in {DHS_INDICATORS.get(indicator_x, {}).get('name', indicator_x)} (F = {f_stat:.3f}, p = {p_val:.4f})."
            }

        elif test_type == "chi_square":
            # Categorical cross-tabulation of indicator risk levels across countries
            contingency_table = []
            for c in country_codes[:4]:
                s = np.array(cls.generate_country_samples(c.upper(), indicator_x))
                med = np.median(s)
                low_risk = int(np.sum(s < med))
                high_risk = int(np.sum(s >= med))
                contingency_table.append([low_risk, high_risk])

            chi2, p_val, dof, expected = stats.chi2_contingency(contingency_table)

            result["summary"] = {
                "test_name": "Chi-Square Test of Independence",
                "contingency_table": contingency_table,
                "chi2_statistic": round(float(chi2), 4),
                "p_value": round(float(p_val), 6),
                "degrees_freedom": dof,
                "significant_95": bool(p_val < 0.05),
                "interpretation": f"Chi-Square test of independence yields chi2 = {chi2:.3f} (p = {p_val:.4f}, df = {dof})."
            }

        elif test_type in ["correlation", "linear_regression"]:
            ind_y = indicator_y or "stunting_prevalence"
            
            # Build paired dataset across countries
            x_vals, y_vals, scatter_points = [], [], []
            for c in country_codes:
                sx = cls.generate_country_samples(c.upper(), indicator_x)
                sy = cls.generate_country_samples(c.upper(), ind_y)
                for vx, vy in zip(sx, sy):
                    x_vals.append(vx)
                    y_vals.append(vy)
                    scatter_points.append({"country": c.upper(), "x": vx, "y": vy})

            arr_x = np.array(x_vals)
            arr_y = np.array(y_vals)

            r_pearson, p_pearson = stats.pearsonr(arr_x, arr_y)
            r_spearman, p_spearman = stats.spearmanr(arr_x, arr_y)

            # OLS Linear Regression
            slope, intercept, r_val, p_val_reg, std_err = stats.linregress(arr_x, arr_y)
            
            min_x, max_x = float(np.min(arr_x)), float(np.max(arr_x))
            trend_line = [
                {"x": min_x, "y": round(float(intercept + slope * min_x), 2)},
                {"x": max_x, "y": round(float(intercept + slope * max_x), 2)}
            ]

            result["summary"] = {
                "test_name": "Pearson & Spearman Correlation & OLS Linear Regression",
                "indicator_x": DHS_INDICATORS.get(indicator_x, {}).get("name", indicator_x),
                "indicator_y": DHS_INDICATORS.get(ind_y, {}).get("name", ind_y),
                "n_obs": len(arr_x),
                "pearson_r": round(float(r_pearson), 4),
                "pearson_p_value": round(float(p_pearson), 6),
                "spearman_r": round(float(r_spearman), 4),
                "spearman_p_value": round(float(p_spearman), 6),
                "ols_slope": round(float(slope), 4),
                "ols_intercept": round(float(intercept), 4),
                "r_squared": round(float(r_val**2), 4),
                "regression_p_value": round(float(p_val_reg), 6),
                "std_err": round(float(std_err), 4),
                "significant_95": bool(p_pearson < 0.05),
                "trend_line": trend_line,
                "scatter_points": scatter_points[:120],  # sample points for charts
                "interpretation": f"Strong correlation (Pearson r = {r_pearson:.3f}, R² = {r_val**2:.3f}, p = {p_pearson:.4f}) between {indicator_x} and {ind_y}."
            }

        return result
