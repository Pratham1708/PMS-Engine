"""
comparison_service.py — Institutional Historical Comparison & Recommendation Intelligence Engine.
"""

import logging
import time
from typing import Any, Dict, List, Optional
import uuid

from app.services import db

logger = logging.getLogger(__name__)

COMPARISON_VERSION = "1.0.0"

class IntegrityValidator:
    """Validates completeness and versions of snapshots to be compared."""
    
    @staticmethod
    def validate_snapshot(snap: dict) -> Dict[str, Any]:
        """Validate that a snapshot is complete and return its record counts."""
        sid = snap["snapshot_id"]
        stocks = db.get_snapshot_stocks(sid)
        indicators = db.get_snapshot_indicators(sid)
        scores = db.get_snapshot_scores(sid)
        
        # Check counts
        num_stocks = len(stocks)
        num_indicators = len(indicators)
        num_scores = len(scores)
        
        is_complete = num_stocks > 0 and num_indicators > 0 and num_scores > 0
        
        return {
            "snapshot_id": sid,
            "is_complete": is_complete,
            "counts": {
                "stocks": num_stocks,
                "indicators": num_indicators,
                "scores": num_scores
            }
        }
        
    @staticmethod
    def check_version_mismatch(snap1: dict, snap2: dict) -> Dict[str, Any]:
        """Compare versions between two snapshots and generate warning flags."""
        mismatches = {}
        warnings = []
        
        # Compare versions
        keys = [
            ("engine_version", "Engine Version"),
            ("indicator_version", "Indicator Version"),
            ("scoring_version", "Scoring Version"),
            ("ml_model_version", "ML Model Version"),
            ("feature_version", "Feature Version")
        ]
        
        for key, name in keys:
            v1 = snap1.get(key)
            v2 = snap2.get(key)
            if v1 != v2:
                mismatches[key] = {
                    "baseline": v1,
                    "comparison": v2
                }
                warnings.append(
                    f"{name} mismatch: baseline has '{v1}' while comparison has '{v2}'."
                )
                
        return {
            "has_mismatch": len(mismatches) > 0,
            "mismatches": mismatches,
            "warnings": warnings
        }


class ComparisonEngine:
    """Handles snapshot resolution, database matching, and delta mapping."""
    
    @staticmethod
    def resolve_snapshot(selector: str, official_only: bool = True) -> Optional[dict]:
        """Resolve selector keyword, date, or UUID to a snapshot record."""
        if not selector:
            return None
            
        selector_clean = selector.strip()
        
        # 1. Keywords
        if selector_clean.lower() == "latest":
            return db.get_latest_snapshot(official_only=official_only)
        elif selector_clean.lower() == "previous":
            latest = db.get_latest_snapshot(official_only=official_only)
            if not latest:
                return None
            return db.get_previous_official_snapshot(latest["snapshot_id"])
            
        # 2. Check if UUID
        try:
            uuid.UUID(selector_clean)
            return db.get_snapshot_by_id(selector_clean)
        except ValueError:
            pass
            
        # 3. Assume date YYYY-MM-DD
        return db.get_snapshot_by_date(selector_clean, official_only=official_only)

    @staticmethod
    def categorize_score_change(delta: float) -> str:
        """Classify a score change into logical categories."""
        if delta > 15.0:
            return "Major Improvement"
        elif delta > 5.0:
            return "Moderate Improvement"
        elif delta > 1.0:
            return "Minor Improvement"
        elif delta < -15.0:
            return "Major Decline"
        elif delta < -5.0:
            return "Moderate Decline"
        elif delta < -1.0:
            return "Minor Decline"
        else:
            return "No Change"

    @classmethod
    def run_comparison(
        cls, 
        snap1_sel: str, 
        snap2_sel: str, 
        strategy_id: str = "pms_default",
        official_only: bool = True
    ) -> Dict[str, Any]:
        """Main orchestrator: loads, validates, calculates, and returns comparison payload."""
        
        # 1. Resolve snapshots
        snap1 = cls.resolve_snapshot(snap1_sel, official_only=official_only)
        if not snap1:
            raise ValueError(f"Snapshot baseline '{snap1_sel}' could not be resolved.")
            
        # If comparing previous, resolve 'previous' relative to snap2 if snap2 is specified
        if snap1_sel.lower() == "previous" and snap2_sel.lower() != "latest":
            snap2_resolved = cls.resolve_snapshot(snap2_sel, official_only=official_only)
            if snap2_resolved:
                snap1 = db.get_previous_official_snapshot(snap2_resolved["snapshot_id"])
                
        # Resolve comparison target
        snap2 = cls.resolve_snapshot(snap2_sel, official_only=official_only)
        if not snap2:
            raise ValueError(f"Snapshot comparison target '{snap2_sel}' could not be resolved.")
            
        # 2. Validate integrity
        val1 = IntegrityValidator.validate_snapshot(snap1)
        val2 = IntegrityValidator.validate_snapshot(snap2)
        
        if not val1["is_complete"]:
            raise ValueError(f"Baseline snapshot '{snap1['snapshot_id']}' is incomplete. Counts: {val1['counts']}")
        if not val2["is_complete"]:
            raise ValueError(f"Comparison snapshot '{snap2['snapshot_id']}' is incomplete. Counts: {val2['counts']}")
            
        # 3. Check version mismatch
        version_check = IntegrityValidator.check_version_mismatch(snap1, snap2)
        
        # 4. Check if comparison registry exists, if not, write to it
        registered = db.get_registered_comparison(snap1["snapshot_id"], snap2["snapshot_id"], strategy_id)
        if not registered:
            db.register_snapshot_comparison(
                snap1["snapshot_id"], 
                snap2["snapshot_id"], 
                snap1["snapshot_date"], 
                snap2["snapshot_date"],
                strategy_id=strategy_id,
                comparison_version=COMPARISON_VERSION
            )
            
        # 5. Load raw records
        s1_stocks = {s["symbol"].upper(): s for s in db.get_snapshot_stocks(snap1["snapshot_id"])}
        s2_stocks = {s["symbol"].upper(): s for s in db.get_snapshot_stocks(snap2["snapshot_id"])}
        
        s1_scores = {s["symbol"].upper(): s for s in db.get_snapshot_scores(snap1["snapshot_id"])}
        s2_scores = {s["symbol"].upper(): s for s in db.get_snapshot_scores(snap2["snapshot_id"])}
        
        s1_indicators = {s["symbol"].upper(): s for s in db.get_snapshot_indicators(snap1["snapshot_id"])}
        s2_indicators = {s["symbol"].upper(): s for s in db.get_snapshot_indicators(snap2["snapshot_id"])}
        
        # Load sector ranks
        sectors1 = {s["sector"]: s for s in db.get_snapshot_sector(snap1["snapshot_id"])}
        sectors2 = {s["sector"]: s for s in db.get_snapshot_sector(snap2["snapshot_id"])}
        
        # 6. Perform JOIN and calculate deltas
        stock_deltas = []
        matched_symbols = set(s1_stocks.keys()) & set(s2_stocks.keys())
        all_symbols = set(s1_stocks.keys()) | set(s2_stocks.keys())
        
        for symbol in all_symbols:
            st1 = s1_stocks.get(symbol)
            st2 = s2_stocks.get(symbol)
            
            sc1 = s1_scores.get(symbol, {})
            sc2 = s2_scores.get(symbol, {})
            
            ind1 = s1_indicators.get(symbol, {})
            ind2 = s2_indicators.get(symbol, {})
            
            if st1 is None:
                # New stock in universe
                curr_rating = st2.get("final_rating") or "HOLD"
                stock_deltas.append({
                    "symbol": symbol,
                    "company_name": st2.get("company_name", ""),
                    "sector": st2.get("sector", "—"),
                    "transition_type": "NEW_IN_UNIVERSE",
                    "prev_rating": None,
                    "new_rating": curr_rating,
                    "score_changes": {
                        "composite_score": { "prev": None, "curr": st2.get("composite_score"), "delta": st2.get("composite_score"), "pct_change": 0.0, "category": "Major Improvement" }
                    },
                    "rank_movement": None,
                    "sector_movement": None,
                    "drivers": [{"feature": "New Stock", "prev_value": None, "curr_value": "Added to Universe", "change": "N/A", "effect": "positive"}]
                })
                continue
                
            if st2 is None:
                # Deleted stock
                stock_deltas.append({
                    "symbol": symbol,
                    "company_name": st1.get("company_name", ""),
                    "sector": st1.get("sector", "—"),
                    "transition_type": "DELETED_FROM_UNIVERSE",
                    "prev_rating": st1.get("final_rating"),
                    "new_rating": None,
                    "score_changes": {},
                    "rank_movement": None,
                    "sector_movement": None,
                    "drivers": []
                })
                continue
            
            # Matched stock
            # Compare all 13 metrics
            score_fields = [
                ("technical_score", "technical_score"),
                ("momentum_score", "momentum_score"),
                ("trend_score", "trend_score"),
                ("risk_score", "risk_score"),
                ("ml_score", "ensemble_score"), # Ensemble Score maps to ml_score in stock
                ("gru_score", "gru_score"),
                ("reliability_score", "reliability_score"),
                ("confidence", "confidence_score"),
                ("composite_score", "composite_score")
            ]
            
            changes = {}
            for field_key, response_key in score_fields:
                val1 = st1.get(field_key)
                val2 = st2.get(field_key)
                
                # Check default weights if None
                if val1 is None: val1 = 0.0
                if val2 is None: val2 = 0.0
                
                delta = round(val2 - val1, 2)
                pct = round((delta / val1 * 100.0), 2) if val1 != 0.0 else 0.0
                
                changes[response_key] = {
                    "prev": round(val1, 2),
                    "curr": round(val2, 2),
                    "delta": delta,
                    "pct_change": pct,
                    "category": cls.categorize_score_change(delta)
                }
                
            # Expected return (return_score from snapshot_score table)
            ret1 = sc1.get("return_score") or 0.0
            ret2 = sc2.get("return_score") or 0.0
            ret_delta = round(ret2 - ret1, 2)
            ret_pct = round((ret_delta / ret1 * 100.0), 2) if ret1 != 0.0 else 0.0
            
            changes["expected_return"] = {
                "prev": round(ret1, 2),
                "curr": round(ret2, 2),
                "delta": ret_delta,
                "pct_change": ret_pct,
                "category": cls.categorize_score_change(ret_delta)
            }
            
            # Ranks
            rank1 = st1.get("rank") or 0
            rank2 = st2.get("rank") or 0
            rank_move = rank1 - rank2 if rank1 > 0 and rank2 > 0 else 0  # positive means improvement (e.g. 10 -> 5)
            
            # Sector rank
            sec = st2.get("sector") or "—"
            sec_rank1 = sectors1.get(sec, {}).get("sector_rank") or 0
            sec_rank2 = sectors2.get(sec, {}).get("sector_rank") or 0
            sec_move = sec_rank1 - sec_rank2 if sec_rank1 > 0 and sec_rank2 > 0 else 0
            
            # Recommendation transition
            prev_rating = st1.get("final_rating") or "HOLD"
            curr_rating = st2.get("final_rating") or "HOLD"
            transition_type = RecommendationEngine.classify_transition(prev_rating, curr_rating)
            
            # Structured drivers
            drivers = RecommendationEngine.generate_structured_drivers(
                st1, st2, sc1, sc2, ind1, ind2
            )
            
            stock_deltas.append({
                "symbol": symbol,
                "company_name": st2.get("company_name", ""),
                "sector": sec,
                "transition_type": transition_type,
                "prev_rating": prev_rating,
                "new_rating": curr_rating,
                "score_changes": changes,
                "rank_movement": rank_move,
                "sector_movement": sec_move,
                "drivers": drivers
            })
            
        # 7. Generate modules summaries
        portfolio_summary = SectorAnalyticsEngine.generate_portfolio_summary(stock_deltas)
        rec_summary = RecommendationEngine.generate_recommendation_summary(stock_deltas)
        sector_summary = SectorAnalyticsEngine.generate_sector_summary(stock_deltas, sectors1, sectors2)
        
        # 8. Visualizations builder
        visuals = VisualizationBuilder.build_visualization_data(stock_deltas, sector_summary)
        
        # Assemble payload
        return {
            "comparison_metadata": {
                "date1": snap1["snapshot_date"],
                "date2": snap2["snapshot_date"],
                "snapshot_id_1": snap1["snapshot_id"],
                "snapshot_id_2": snap2["snapshot_id"],
                "strategy_id": strategy_id,
                "generated_at": snap2["generated_at"],
                "comparison_version": COMPARISON_VERSION,
                "version_warnings": version_check["warnings"] if version_check["has_mismatch"] else []
            },
            "portfolio_summary": portfolio_summary,
            "sector_summary": sector_summary,
            "recommendation_summary": rec_summary,
            "stock_deltas": stock_deltas,
            "visualizations": visuals
        }


class RecommendationEngine:
    """Calculates rating transitions, structured drivers, and recommendation matrices."""
    
    @staticmethod
    def classify_transition(prev: str, curr: str) -> str:
        """Classify rating transitions."""
        rating_order = {"STRONG SELL": 0, "SELL": 1, "HOLD": 2, "BUY": 3, "STRONG BUY": 4}
        p_val = rating_order.get(prev, 2)
        c_val = rating_order.get(curr, 2)
        
        if prev != curr:
            if prev in ("STRONG SELL", "SELL") and curr in ("BUY", "STRONG BUY"):
                return "NEW_BUY"
            elif prev in ("STRONG BUY", "BUY") and curr in ("SELL", "STRONG SELL"):
                return "NEW_SELL"
            elif c_val > p_val:
                return "UPGRADE"
            elif c_val < p_val:
                return "DOWNGRADE"
        return "UNCHANGED"

    @staticmethod
    def generate_structured_drivers(
        st1: dict, st2: dict, sc1: dict, sc2: dict, ind1: dict, ind2: dict
    ) -> List[Dict[str, Any]]:
        """Generate structured reasons mapping what caused recommendation/score changes."""
        drivers = []
        
        # Check major score movements
        score_keys = [
            ("technical_score", "Technical Score"),
            ("composite_score", "Composite Score"),
            ("momentum_score", "Momentum Score"),
            ("trend_score", "Trend Score"),
            ("confidence", "Confidence Score")
        ]
        for key, display in score_keys:
            val1 = float(st1.get(key) or 0.0)
            val2 = float(st2.get(key) or 0.0)
            diff = val2 - val1
            if abs(diff) >= 5.0:
                drivers.append({
                    "feature": display,
                    "prev_value": round(val1, 2),
                    "curr_value": round(val2, 2),
                    "change": f"{'+' if diff > 0 else ''}{round(diff, 1)}",
                    "effect": "positive" if diff > 0 else "negative"
                })
                
        # Check technical indicators change
        if ind1 and ind2:
            # RSI crossover
            rsi1 = ind1.get("rsi_14")
            rsi2 = ind2.get("rsi_14")
            if rsi1 is not None and rsi2 is not None:
                if rsi1 <= 50 < rsi2:
                    drivers.append({
                        "feature": "RSI Trend",
                        "prev_value": round(rsi1, 1),
                        "curr_value": round(rsi2, 1),
                        "change": "Crossed above 50 (Bullish)",
                        "effect": "positive"
                    })
                elif rsi1 >= 50 > rsi2:
                    drivers.append({
                        "feature": "RSI Trend",
                        "prev_value": round(rsi1, 1),
                        "curr_value": round(rsi2, 1),
                        "change": "Crossed below 50 (Bearish)",
                        "effect": "negative"
                    })
                elif abs(rsi2 - rsi1) >= 10.0:
                    diff = rsi2 - rsi1
                    drivers.append({
                        "feature": "RSI Value",
                        "prev_value": round(rsi1, 1),
                        "curr_value": round(rsi2, 1),
                        "change": f"{'+' if diff > 0 else ''}{round(diff, 1)} points",
                        "effect": "positive" if diff > 0 else "negative"
                    })
                    
            # EMA crossovers
            ema_keys = [("above_ema20", "EMA 20"), ("above_ema50", "EMA 50"), ("above_ema200", "EMA 200")]
            for key, display in ema_keys:
                pos1 = ind1.get(key)
                pos2 = ind2.get(key)
                if pos1 != pos2 and pos1 is not None and pos2 is not None:
                    effect = "positive" if pos2 else "negative"
                    change = "Crossed Above" if pos2 else "Crossed Below"
                    drivers.append({
                        "feature": display,
                        "prev_value": "Below" if not pos1 else "Above",
                        "curr_value": "Below" if not pos2 else "Above",
                        "change": change,
                        "effect": effect
                    })
                    
        return drivers

    @classmethod
    def generate_recommendation_summary(cls, stock_deltas: List[Dict]) -> Dict[str, Any]:
        """Aggregate transitions list into upgraded list, downgraded list, and Matrix."""
        upgrades = []
        downgrades = []
        
        # Standard rating order
        matrix = {
            "STRONG SELL": {"STRONG SELL": 0, "SELL": 0, "HOLD": 0, "BUY": 0, "STRONG BUY": 0},
            "SELL": {"STRONG SELL": 0, "SELL": 0, "HOLD": 0, "BUY": 0, "STRONG BUY": 0},
            "HOLD": {"STRONG SELL": 0, "SELL": 0, "HOLD": 0, "BUY": 0, "STRONG BUY": 0},
            "BUY": {"STRONG SELL": 0, "SELL": 0, "HOLD": 0, "BUY": 0, "STRONG BUY": 0},
            "STRONG BUY": {"STRONG SELL": 0, "SELL": 0, "HOLD": 0, "BUY": 0, "STRONG BUY": 0}
        }
        
        rating_order = {"STRONG SELL": 0, "SELL": 1, "HOLD": 2, "BUY": 3, "STRONG BUY": 4}
        for sd in stock_deltas:
            p = sd["prev_rating"]
            n = sd["new_rating"]
            if p is None or n is None:
                continue
            
            # Map valid rating keys to matrix
            if p in matrix and n in matrix:
                matrix[p][n] += 1
                
            p_val = rating_order.get(p, 2)
            n_val = rating_order.get(n, 2)
            if n_val > p_val:
                upgrades.append(sd)
            elif n_val < p_val:
                downgrades.append(sd)
                
        # Sort upgrades/downgrades by absolute composite change
        upgrades.sort(key=lambda x: abs(x["score_changes"].get("composite_score", {}).get("delta", 0)), reverse=True)
        downgrades.sort(key=lambda x: abs(x["score_changes"].get("composite_score", {}).get("delta", 0)), reverse=True)
        
        return {
            "upgrade_list": upgrades,
            "downgrade_list": downgrades,
            "matrix": matrix
        }


class SectorAnalyticsEngine:
    """Calculates sector delta stats and performs intelligence audits."""
    
    @staticmethod
    def generate_portfolio_summary(stock_deltas: List[Dict]) -> Dict[str, Any]:
        """Compute portfolio-level upgrades/downgrades counts and average changes."""
        matched = [sd for sd in stock_deltas if sd["prev_rating"] is not None and sd["new_rating"] is not None]
        total = len(matched)
        
        if total == 0:
            return {
                "upgrades": 0,
                "downgrades": 0,
                "unchanged": 0,
                "avg_composite_change": 0.0,
                "avg_technical_change": 0.0,
                "avg_expected_return_change": 0.0,
                "strongest_improving": [],
                "largest_deteriorating": []
            }
            
        rating_order = {"STRONG SELL": 0, "SELL": 1, "HOLD": 2, "BUY": 3, "STRONG BUY": 4}
        upgrades = sum(1 for sd in matched if rating_order.get(sd["new_rating"], 2) > rating_order.get(sd["prev_rating"], 2))
        downgrades = sum(1 for sd in matched if rating_order.get(sd["new_rating"], 2) < rating_order.get(sd["prev_rating"], 2))
        unchanged = sum(1 for sd in matched if rating_order.get(sd["new_rating"], 2) == rating_order.get(sd["prev_rating"], 2))
        
        def avg(key: str) -> float:
            vals = [sd["score_changes"][key]["delta"] for sd in matched if key in sd["score_changes"]]
            return round(sum(vals) / len(vals), 2) if vals else 0.0
            
        avg_comp = avg("composite_score")
        avg_tech = avg("technical_score")
        avg_ret = avg("expected_return")
        
        # Sort for top movers
        sorted_improving = sorted(
            matched, 
            key=lambda x: x["score_changes"].get("composite_score", {}).get("delta", 0.0), 
            reverse=True
        )
        sorted_deteriorating = sorted(
            matched, 
            key=lambda x: x["score_changes"].get("composite_score", {}).get("delta", 0.0)
        )
        
        return {
            "upgrades": upgrades,
            "downgrades": downgrades,
            "unchanged": unchanged,
            "avg_composite_change": avg_comp,
            "avg_technical_change": avg_tech,
            "avg_expected_return_change": avg_ret,
            "strongest_improving": sorted_improving[:5],
            "largest_deteriorating": sorted_deteriorating[:5]
        }

    @classmethod
    def generate_sector_summary(cls, stock_deltas: List[Dict], sectors1: dict, sectors2: dict) -> Dict[str, Any]:
        """Examine sector performance and isolate high-conviction metrics."""
        sector_groups = {}
        for sd in stock_deltas:
            if sd["prev_rating"] is None or sd["new_rating"] is None:
                continue
            sec = sd["sector"]
            sector_groups.setdefault(sec, []).append(sd)
            
        sector_deltas = []
        for sec, items in sector_groups.items():
            total = len(items)
            
            def avg_field(field_key: str) -> float:
                vals = [sd["score_changes"][field_key]["delta"] for sd in items if field_key in sd["score_changes"]]
                return round(sum(vals) / len(vals), 2) if vals else 0.0
                
            comp_diff = avg_field("composite_score")
            tech_diff = avg_field("technical_score")
            mom_diff = avg_field("momentum_score")
            risk_diff = avg_field("risk_score")
            
            upgrades = sum(1 for sd in items if sd["transition_type"] in ("UPGRADE", "NEW_BUY"))
            downgrades = sum(1 for sd in items if sd["transition_type"] in ("DOWNGRADE", "NEW_SELL"))
            
            # Fetch sector rank diff
            rank1 = sectors1.get(sec, {}).get("sector_rank") or 99
            rank2 = sectors2.get(sec, {}).get("sector_rank") or 99
            rank_diff = rank1 - rank2  # positive is improvement
            
            sector_deltas.append({
                "sector": sec,
                "stock_count": total,
                "avg_composite_change": comp_diff,
                "avg_technical_change": tech_diff,
                "avg_momentum_change": mom_diff,
                "avg_risk_change": risk_diff,
                "upgrades": upgrades,
                "downgrades": downgrades,
                "sector_rank_diff": rank_diff
            })
            
        if not sector_deltas:
            return {
                "best_sector": None,
                "worst_sector": None,
                "most_upgrades": None,
                "largest_momentum_gain": None,
                "largest_risk_reduction": None,
                "sector_deltas": []
            }
            
        # Isolate best/worst
        best_sec = max(sector_deltas, key=lambda x: x["avg_composite_change"])["sector"]
        worst_sec = min(sector_deltas, key=lambda x: x["avg_composite_change"])["sector"]
        
        most_upgrades_sec = max(sector_deltas, key=lambda x: x["upgrades"])
        most_upgrades = most_upgrades_sec["sector"] if most_upgrades_sec["upgrades"] > 0 else None
        
        largest_mom_sec = max(sector_deltas, key=lambda x: x["avg_momentum_change"])
        largest_mom = largest_mom_sec["sector"] if largest_mom_sec["avg_momentum_change"] > 0 else None
        
        largest_risk_sec = min(sector_deltas, key=lambda x: x["avg_risk_change"])
        largest_risk = largest_risk_sec["sector"] if largest_risk_sec["avg_risk_change"] < 0 else None
        
        return {
            "best_sector": best_sec,
            "worst_sector": worst_sec,
            "most_upgrades": most_upgrades,
            "largest_momentum_gain": largest_mom,
            "largest_risk_reduction": largest_risk,
            "sector_deltas": sector_deltas
        }


class HistoricalTrendEngine:
    """Traces multiple trajectory sequences (A -> B -> C -> D) for scores."""
    
    @staticmethod
    def get_trajectory_history(symbols: List[str], limit: int = 10) -> Dict[str, Any]:
        """Trace composite score trajectories over the last N snapshots for a list of stocks."""
        dates_list = db.list_snapshot_dates(official_only=True, limit=limit)
        dates_list.reverse() # chronologically oldest to newest
        
        dates = [d["snapshot_date"] for d in dates_list]
        snapshots = {d["snapshot_date"]: d["snapshot_id"] for d in dates_list}
        
        stock_trajectories = {}
        for symbol in symbols:
            stock_trajectories[symbol.upper()] = []
            
        for dt in dates:
            sid = snapshots[dt]
            stocks = {s["symbol"].upper(): s for s in db.get_snapshot_stocks(sid)}
            
            for symbol in symbols:
                sym_up = symbol.upper()
                s_rec = stocks.get(sym_up)
                if s_rec:
                    stock_trajectories[sym_up].append({
                        "date": dt,
                        "composite_score": s_rec.get("composite_score"),
                        "technical_score": s_rec.get("technical_score"),
                        "final_rating": s_rec.get("final_rating"),
                        "close": s_rec.get("close")
                    })
                    
        return {
            "dates": dates,
            "trajectories": stock_trajectories
        }


class VisualizationBuilder:
    """Formats payload parameters specifically structured for Recharts visualization."""
    
    @staticmethod
    def build_visualization_data(stock_deltas: List[Dict], sector_summary: dict) -> Dict[str, Any]:
        """Aggregate waterfall, distribution histogram, and heatmap structures."""
        
        # 1. Waterfall data: Contribution to composite change
        # Starts with baseline (0), tracks upgrades, downgrades, new buys, new sells, other, and final sum
        upgrades_contrib = 0.0
        downgrades_contrib = 0.0
        new_buys_contrib = 0.0
        new_sells_contrib = 0.0
        other_contrib = 0.0
        
        matched_count = 0
        for sd in stock_deltas:
            delta = sd["score_changes"].get("composite_score", {}).get("delta", 0.0)
            if sd["prev_rating"] is None:
                if sd["new_rating"] in ("STRONG BUY", "BUY"):
                    new_buys_contrib += delta
                else:
                    other_contrib += delta
            elif sd["new_rating"] is None:
                if sd["prev_rating"] in ("STRONG BUY", "BUY"):
                    new_sells_contrib += delta
                else:
                    other_contrib += delta
            else:
                matched_count += 1
                if sd["transition_type"] in ("UPGRADE", "NEW_BUY"):
                    upgrades_contrib += delta
                elif sd["transition_type"] in ("DOWNGRADE", "NEW_SELL"):
                    downgrades_contrib += delta
                else:
                    other_contrib += delta
                    
        total_delta = upgrades_contrib + downgrades_contrib + new_buys_contrib + new_sells_contrib + other_contrib
        avg_delta = round(total_delta / max(len(stock_deltas), 1), 2)
        
        waterfall = [
            {"name": "Baseline Average", "value": 0.0, "display": "0.0"},
            {"name": "Upgrades", "value": round(upgrades_contrib, 1), "display": f"+{round(upgrades_contrib, 1)}"},
            {"name": "Downgrades", "value": round(downgrades_contrib, 1), "display": f"{round(downgrades_contrib, 1)}"},
            {"name": "New Buys", "value": round(new_buys_contrib, 1), "display": f"+{round(new_buys_contrib, 1)}"},
            {"name": "New Sells", "value": round(new_sells_contrib, 1), "display": f"{round(new_sells_contrib, 1)}"},
            {"name": "Other Changes", "value": round(other_contrib, 1), "display": f"{'+' if other_contrib >= 0 else ''}{round(other_contrib, 1)}"},
            {"name": "Net Delta Sum", "value": round(total_delta, 1), "display": f"{'+' if total_delta >= 0 else ''}{round(total_delta, 1)}"}
        ]
        
        # 2. Histogram distribution of composite score changes
        # Buckets: <-15, -15 to -5, -5 to -1, -1 to 1, 1 to 5, 5 to 15, >15
        buckets = {
            "Major Decline (<-15)": 0,
            "Moderate Decline (-15 to -5)": 0,
            "Minor Decline (-5 to -1)": 0,
            "No Change (-1 to 1)": 0,
            "Minor Improvement (1 to 5)": 0,
            "Moderate Improvement (5 to 15)": 0,
            "Major Improvement (>15)": 0
        }
        for sd in stock_deltas:
            comp_chg = sd["score_changes"].get("composite_score", {}).get("delta")
            if comp_chg is not None:
                if comp_chg > 15.0:
                    buckets["Major Improvement (>15)"] += 1
                elif comp_chg > 5.0:
                    buckets["Moderate Improvement (5 to 15)"] += 1
                elif comp_chg > 1.0:
                    buckets["Minor Improvement (1 to 5)"] += 1
                elif comp_chg < -15.0:
                    buckets["Major Decline (<-15)"] += 1
                elif comp_chg < -5.0:
                    buckets["Moderate Decline (-15 to -5)"] += 1
                elif comp_chg < -1.0:
                    buckets["Minor Decline (-5 to -1)"] += 1
                else:
                    buckets["No Change (-1 to 1)"] += 1
                    
        histogram = [{"bucket": k, "count": v} for k, v in buckets.items()]
        
        # 3. Sector Heatmap Data
        sector_heatmap = []
        for sd in sector_summary.get("sector_deltas", []):
            sector_heatmap.append({
                "sector": sd["sector"],
                "avg_composite_change": sd["avg_composite_change"],
                "avg_technical_change": sd["avg_technical_change"],
                "upgrades": sd["upgrades"],
                "downgrades": sd["downgrades"],
                "stock_count": sd["stock_count"]
            })
            
        return {
            "waterfall": waterfall,
            "histogram": histogram,
            "sector_heatmap": sector_heatmap
        }
