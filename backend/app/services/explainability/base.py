from typing import List, Dict, Any
from app.models.schemas import (
    Contribution,
    ValidationMetric,
    ResearchReference,
    ScoreInterpretation,
    ExplainScoreResponse,
    NormalizationExplain,
    ResearchReference as ResearchReferenceSchema,
    FeatureMetadata,
    FeatureAttribution,
    CategoryContribution
)
from app.services.explainability.registry import (
    METADATA_REGISTRY,
    FORMULA_REGISTRY,
    NORMALIZATION_REGISTRY,
    REFERENCE_REGISTRY
)

class BaseExplainer:
    def get_purpose(self) -> str:
        raise NotImplementedError

    def get_formula(self) -> str:
        raise NotImplementedError

    def get_references(self) -> List[ResearchReference]:
        raise NotImplementedError

    def get_validation(self) -> List[ValidationMetric]:
        raise NotImplementedError

    def get_interpretation(self) -> List[ScoreInterpretation]:
        raise NotImplementedError

    def get_limitations(self) -> List[str]:
        raise NotImplementedError

    def explain(self, stock_data: Dict[str, Any], history: List[Dict[str, Any]]) -> ExplainScoreResponse:
        raise NotImplementedError


def enrich_runtime_contributions(runtime_categories: list) -> List[CategoryContribution]:
    """
    Takes a list of categories with runtime features and joins static metadata.
    """
    if not runtime_categories:
        return []
        
    enriched_categories = []
    for cat_dict in runtime_categories:
        cat_name = cat_dict.get("category") or "General"
        features_list = cat_dict.get("features") or []
        subtotal = cat_dict.get("subtotal") or 0.0
        
        enriched_features = []
        for feat in features_list:
            key = feat.get("feature_key")
            if not key:
                continue
                
            # Retrieve static metadata (with safe fallbacks)
            meta = METADATA_REGISTRY.get(key, {})
            formula_info = FORMULA_REGISTRY.get(key, {})
            norm_info = NORMALIZATION_REGISTRY.get(key, {})
            ref_info = REFERENCE_REGISTRY.get(key, {})
            
            display_name = meta.get("display_name") or key.upper()
            data_source = meta.get("data_source") or "Unknown"
            description = meta.get("description") or "Quantitative factor."
            
            plain_formula = formula_info.get("plain_formula") or "N/A"
            latex_formula = formula_info.get("latex_formula") or "N/A"
            
            norm_explain = NormalizationExplain(
                method=norm_info.get("method") or "Direct Mapping",
                range=norm_info.get("range") or "N/A",
                logic=norm_info.get("logic") or "No scaling applied."
            )
            
            res_ref = ResearchReferenceSchema(
                paper=ref_info.get("paper") or "PMS Standard Technical Methodology",
                author=ref_info.get("author") or "PMS Research Team",
                year=ref_info.get("year") or 2026,
                link=ref_info.get("link"),
                description=ref_info.get("description") or "Baseline scoring mapping."
            )
            
            metadata = FeatureMetadata(
                data_source=data_source,
                plain_formula=plain_formula,
                latex_formula=latex_formula,
                normalization=norm_explain,
                reference=res_ref
            )
            
            # Build natural plain language explanation of impact
            weight_pct = feat.get("weight", 0.0) * 100
            contrib = feat.get("contribution") or 0.0
            effect = feat.get("effect") or "neutral"
            
            if effect == "positive" and contrib > 0:
                explanation = f"{display_name} is bullish, contributing +{contrib:.2f} points ({weight_pct:.1f}% weight) to the score."
            elif effect == "negative" and contrib < 0:
                explanation = f"{display_name} exhibits downward pressure, reducing the score by {abs(contrib):.2f} points ({weight_pct:.1f}% weight)."
            else:
                explanation = f"{display_name} is neutral, carrying {weight_pct:.1f}% weight with zero net impact."
                
            attr = FeatureAttribution(
                feature_key=key,
                name=display_name,
                current_value=str(feat.get("current_value") or "—"),
                normalized_value=float(feat.get("normalized_value") or 0.0),
                weight=float(feat.get("weight") or 0.0),
                contribution=float(contrib),
                effect=effect,
                explanation=explanation,
                confidence=feat.get("confidence") or "Medium",
                metadata=metadata
            )
            enriched_features.append(attr)
            
        enriched_categories.append(CategoryContribution(
            category=cat_name,
            features=enriched_features,
            subtotal=float(subtotal)
        ))
    return enriched_categories
