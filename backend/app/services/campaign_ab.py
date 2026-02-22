"""
Campaign A/B Testing Service
Phase 6 Enhancement - Advanced campaign testing with statistical analysis and optimization
"""
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import numpy as np
from dataclasses import dataclass
from scipy import stats
import json

from app.models.crm import CRMCompany, CRMContact, CRMDeal
from app.models.tenant import Tenant
from app.config import get_settings


@dataclass
class CampaignVariant:
    """Campaign variant definition"""
    id: str
    name: str
    description: str
    traffic_allocation: float  # 0.0 to 1.0
    subject: str
    content: str
    sender: str
    target_audience: Dict[str, Any]
    created_at: datetime


@dataclass
class CampaignMetrics:
    """Campaign metrics for a variant"""
    variant_id: str
    sent_count: int
    delivered_count: int
    opened_count: int
    clicked_count: int
    converted_count: int
    unsubscribed_count: int
    bounce_count: int
    spam_count: int
    
    @property
    def delivery_rate(self) -> float:
        return (self.delivered_count / self.sent_count) if self.sent_count > 0 else 0
    
    @property
    def open_rate(self) -> float:
        return (self.opened_count / self.delivered_count) if self.delivered_count > 0 else 0
    
    @property
    def click_rate(self) -> float:
        return (self.clicked_count / self.opened_count) if self.opened_count > 0 else 0
    
    @property
    def conversion_rate(self) -> float:
        return (self.converted_count / self.clicked_count) if self.clicked_count > 0 else 0
    
    @property
    def unsubscribe_rate(self) -> float:
        return (self.unsubscribed_count / self.delivered_count) if self.delivered_count > 0 else 0
    
    @property
    def bounce_rate(self) -> float:
        return (self.bounce_count / self.sent_count) if self.sent_count > 0 else 0


@dataclass
class TestResult:
    """A/B test statistical result"""
    variant_a: str
    variant_b: str
    metric: str
    variant_a_value: float
    variant_b_value: float
    absolute_difference: float
    relative_difference: float
    statistical_significance: bool
    p_value: float
    confidence_interval: Tuple[float, float]
    winner: Optional[str]
    confidence_level: float


class CampaignABService:
    """Service for A/B testing campaigns"""
    
    def __init__(self, db: Session):
        self.db = db
        self.significance_threshold = 0.05  # 5% significance level
        self.confidence_level = 0.95  # 95% confidence level
        self.min_sample_size = 100  # Minimum sample size for statistical significance
        
        # Mock campaign storage (in production, this would be in database)
        self.campaigns = {}
        self.campaign_results = {}
    
    async def create_ab_test(
        self,
        campaign_name: str,
        tenant_id: str,
        variant_a: Dict[str, Any],
        variant_b: Dict[str, Any],
        test_duration_days: int = 14,
        target_audience: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new A/B test campaign
        
        Args:
            campaign_name: Name of the campaign
            tenant_id: Tenant ID
            variant_a: Variant A configuration
            variant_b: Variant B configuration
            test_duration_days: Duration of the test in days
            target_audience: Target audience criteria
        """
        test_id = f"ab_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Create campaign variants
        campaign_variants = [
            CampaignVariant(
                id=f"{test_id}_A",
                name=variant_a.get("name", "Variant A"),
                description=variant_a.get("description", ""),
                traffic_allocation=0.5,
                subject=variant_a.get("subject", ""),
                content=variant_a.get("content", ""),
                sender=variant_a.get("sender", ""),
                target_audience=target_audience or {},
                created_at=datetime.utcnow()
            ),
            CampaignVariant(
                id=f"{test_id}_B",
                name=variant_b.get("name", "Variant B"),
                description=variant_b.get("description", ""),
                traffic_allocation=0.5,
                subject=variant_b.get("subject", ""),
                content=variant_b.get("content", ""),
                sender=variant_b.get("sender", ""),
                target_audience=target_audience or {},
                created_at=datetime.utcnow()
            )
        ]
        
        # Store campaign
        self.campaigns[test_id] = {
            "id": test_id,
            "name": campaign_name,
            "tenant_id": tenant_id,
            "variants": campaign_variants,
            "test_duration_days": test_duration_days,
            "target_audience": target_audience,
            "status": "created",
            "created_at": datetime.utcnow(),
            "start_date": datetime.utcnow(),
            "end_date": datetime.utcnow() + timedelta(days=test_duration_days),
            "primary_metric": "conversion_rate",
            "sample_size": 0
        }
        
        return {
            "test_id": test_id,
            "status": "created",
            "variants": [
                {
                    "id": variant.id,
                    "name": variant.name,
                    "traffic_allocation": variant.traffic_allocation
                }
                for variant in campaign_variants
            ],
            "test_duration_days": test_duration_days,
            "start_date": self.campaigns[test_id]["start_date"].isoformat(),
            "end_date": self.campaigns[test_id]["end_date"].isoformat()
        }
    
    async def start_ab_test(
        self,
        test_id: str,
        sample_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Start an A/B test campaign
        
        Args:
            test_id: Test ID to start
            sample_size: Optional sample size override
        """
        if test_id not in self.campaigns:
            raise ValueError(f"A/B test '{test_id}' not found")
        
        campaign = self.campaigns[test_id]
        
        if campaign["status"] != "created":
            raise ValueError(f"A/B test '{test_id}' is already {campaign['status']}")
        
        # Set sample size
        if sample_size:
            campaign["sample_size"] = sample_size
        else:
            # Calculate sample size based on target audience
            campaign["sample_size"] = await self._calculate_sample_size(
                campaign["tenant_id"],
                campaign["target_audience"]
            )
        
        # Update status
        campaign["status"] = "running"
        campaign["start_date"] = datetime.utcnow()
        
        # Initialize metrics for each variant
        campaign["metrics"] = {
            variant.id: CampaignMetrics(
                variant_id=variant.id,
                sent_count=0,
                delivered_count=0,
                opened_count=0,
                clicked_count=0,
                converted_count=0,
                unsubscribed_count=0,
                bounce_count=0,
                spam_count=0
            )
            for variant in campaign["variants"]
        }
        
        return {
            "test_id": test_id,
            "status": "running",
            "sample_size": campaign["sample_size"],
            "start_date": campaign["start_date"].isoformat(),
            "end_date": campaign["end_date"].isoformat()
        }
    
    async def record_campaign_event(
        self,
        test_id: str,
        variant_id: str,
        event_type: str,
        contact_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Record a campaign event for A/B testing
        
        Args:
            test_id: Test ID
            variant_id: Variant ID
            event_type: Event type (sent, delivered, opened, clicked, converted, etc.)
            contact_id: Contact ID (if applicable)
            timestamp: Event timestamp
        """
        if test_id not in self.campaigns:
            raise ValueError(f"A/B test '{test_id}' not found")
        
        campaign = self.campaigns[test_id]
        
        if campaign["status"] != "running":
            raise ValueError(f"A/B test '{test_id}' is not running")
        
        if variant_id not in campaign["metrics"]:
            raise ValueError(f"Variant '{variant_id}' not found in test '{test_id}'")
        
        # Update metrics based on event type
        metrics = campaign["metrics"][variant_id]
        
        if event_type == "sent":
            metrics.sent_count += 1
        elif event_type == "delivered":
            metrics.delivered_count += 1
        elif event_type == "opened":
            metrics.opened_count += 1
        elif event_type == "clicked":
            metrics.clicked_count += 1
        elif event_type == "converted":
            metrics.converted_count += 1
        elif event_type == "unsubscribed":
            metrics.unsubscribed_count += 1
        elif event_type == "bounce":
            metrics.bounce_count += 1
        elif event_type == "spam":
            metrics.spam_count += 1
        
        # Store event for detailed analysis
        if "events" not in campaign:
            campaign["events"] = []
        
        campaign["events"].append({
            "variant_id": variant_id,
            "event_type": event_type,
            "contact_id": contact_id,
            "timestamp": timestamp or datetime.utcnow()
        })
        
        return {
            "test_id": test_id,
            "variant_id": variant_id,
            "event_type": event_type,
            "recorded_at": datetime.utcnow().isoformat()
        }
    
    async def get_test_results(
        self,
        test_id: str,
        include_detailed_metrics: bool = False
    ) -> Dict[str, Any]:
        """
        Get A/B test results and statistical analysis
        
        Args:
            test_id: Test ID
            include_detailed_metrics: Include detailed metrics for each variant
        """
        if test_id not in self.campaigns:
            raise ValueError(f"A/B test '{test_id}' not found")
        
        campaign = self.campaigns[test_id]
        
        # Get metrics for each variant
        variant_metrics = {}
        for variant_id, metrics in campaign["metrics"].items():
            variant_metrics[variant_id] = {
                "sent_count": metrics.sent_count,
                "delivered_count": metrics.delivered_count,
                "opened_count": metrics.opened_count,
                "clicked_count": metrics.clicked_count,
                "converted_count": metrics.converted_count,
                "unsubscribed_count": metrics.unsubscribed_count,
                "bounce_count": metrics.bounce_count,
                "spam_count": metrics.spam_count,
                "delivery_rate": metrics.delivery_rate,
                "open_rate": metrics.open_rate,
                "click_rate": metrics.click_rate,
                "conversion_rate": metrics.conversion_rate,
                "unsubscribe_rate": metrics.unsubscribe_rate,
                "bounce_rate": metrics.bounce_rate
            }
        
        # Calculate statistical tests
        test_results = await self._calculate_statistical_tests(test_id)
        
        # Determine winner
        winner = await self._determine_winner(test_id, test_results)
        
        # Check if test is complete
        is_complete = await self._is_test_complete(test_id)
        
        if is_complete:
            campaign["status"] = "completed"
            campaign["completed_at"] = datetime.utcnow()
        
        result_data = {
            "test_id": test_id,
            "test_name": campaign["name"],
            "status": campaign["status"],
            "start_date": campaign["start_date"].isoformat(),
            "end_date": campaign["end_date"].isoformat(),
            "is_complete": is_complete,
            "sample_size": campaign["sample_size"],
            "primary_metric": campaign["primary_metric"],
            "variant_metrics": variant_metrics,
            "statistical_tests": test_results,
            "winner": winner,
            "confidence_level": self.confidence_level
        }
        
        if include_detailed_metrics:
            result_data["detailed_events"] = campaign.get("events", [])
        
        return result_data
    
    async def _calculate_statistical_tests(self, test_id: str) -> List[TestResult]:
        """Calculate statistical tests for A/B test variants"""
        campaign = self.campaigns[test_id]
        variants = campaign["variants"]
        
        if len(variants) != 2:
            return []
        
        variant_a = variants[0]
        variant_b = variants[1]
        metrics_a = campaign["metrics"][variant_a.id]
        metrics_b = campaign["metrics"][variant_b.id]
        
        # Metrics to test
        metrics_to_test = [
            ("open_rate", metrics_a.open_rate, metrics_b.open_rate),
            ("click_rate", metrics_a.click_rate, metrics_b.click_rate),
            ("conversion_rate", metrics_a.conversion_rate, metrics_b.conversion_rate),
            ("unsubscribe_rate", metrics_a.unsubscribe_rate, metrics_b.unsubscribe_rate)
        ]
        
        test_results = []
        
        for metric_name, value_a, value_b in metrics_to_test:
            # Skip if no data
            if value_a == 0 and value_b == 0:
                continue
            
            # Calculate statistical significance
            result = await self._calculate_statistical_significance(
                variant_a.id, variant_b.id, metric_name, value_a, value_b
            )
            
            test_results.append(result)
        
        return test_results
    
    async def _calculate_statistical_significance(
        self,
        variant_a: str,
        variant_b: str,
        metric: str,
        value_a: float,
        value_b: float
    ) -> TestResult:
        """Calculate statistical significance between two variants"""
        campaign = self.campaigns[f"ab_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"]
        
        # Get sample sizes
        metrics_a = campaign["metrics"][variant_a]
        metrics_b = campaign["metrics"][variant_b]
        
        # Determine sample sizes based on metric
        if metric == "open_rate":
            n_a = metrics_a.delivered_count
            n_b = metrics_b.delivered_count
        elif metric == "click_rate":
            n_a = metrics_a.opened_count
            n_b = metrics_b.opened_count
        elif metric == "conversion_rate":
            n_a = metrics_a.clicked_count
            n_b = metrics_b.clicked_count
        else:
            n_a = metrics_a.sent_count
            n_b = metrics_b.sent_count
        
        # Skip if sample sizes are too small
        if n_a < self.min_sample_size or n_b < self.min_sample_size:
            return TestResult(
                variant_a=variant_a,
                variant_b=variant_b,
                metric=metric,
                variant_a_value=value_a,
                variant_b_value=value_b,
                absolute_difference=value_b - value_a,
                relative_difference=((value_b - value_a) / value_a * 100) if value_a > 0 else 0,
                statistical_significance=False,
                p_value=1.0,
                confidence_interval=(0, 0),
                winner=None,
                confidence_level=self.confidence_level
            )
        
        # Perform two-proportion z-test
        try:
            # Calculate pooled proportion
            pooled_p = (value_a * n_a + value_b * n_b) / (n_a + n_b)
            
            # Calculate standard error
            se = np.sqrt(pooled_p * (1 - pooled_p) * (1/n_a + 1/n_b))
            
            # Calculate z-score
            if se > 0:
                z_score = (value_b - value_a) / se
            else:
                z_score = 0
            
            # Calculate p-value (two-tailed test)
            p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
            
            # Calculate confidence interval
            z_critical = stats.norm.ppf(1 - (1 - self.confidence_level) / 2)
            margin_of_error = z_critical * se
            ci_lower = (value_b - value_a) - margin_of_error
            ci_upper = (value_b - value_a) + margin_of_error
            
            # Determine statistical significance
            is_significant = p_value < self.significance_threshold
            
            # Determine winner
            winner = None
            if is_significant:
                winner = variant_b if value_b > value_a else variant_a
            
            return TestResult(
                variant_a=variant_a,
                variant_b=variant_b,
                metric=metric,
                variant_a_value=value_a,
                variant_b_value=value_b,
                absolute_difference=value_b - value_a,
                relative_difference=((value_b - value_a) / value_a * 100) if value_a > 0 else 0,
                statistical_significance=is_significant,
                p_value=p_value,
                confidence_interval=(ci_lower, ci_upper),
                winner=winner,
                confidence_level=self.confidence_level
            )
            
        except Exception as e:
            # Return default result if calculation fails
            return TestResult(
                variant_a=variant_a,
                variant_b=variant_b,
                metric=metric,
                variant_a_value=value_a,
                variant_b_value=value_b,
                absolute_difference=value_b - value_a,
                relative_difference=((value_b - value_a) / value_a * 100) if value_a > 0 else 0,
                statistical_significance=False,
                p_value=1.0,
                confidence_interval=(0, 0),
                winner=None,
                confidence_level=self.confidence_level
            )
    
    async def _determine_winner(
        self,
        test_id: str,
        test_results: List[TestResult]
    ) -> Optional[Dict[str, Any]]:
        """Determine the winning variant based on statistical tests"""
        campaign = self.campaigns[test_id]
        primary_metric = campaign["primary_metric"]
        
        # Find test result for primary metric
        primary_result = None
        for result in test_results:
            if result.metric == primary_metric:
                primary_result = result
                break
        
        if not primary_result:
            return None
        
        # Determine winner
        if primary_result.winner:
            winner_variant = next(
                (v for v in campaign["variants"] if v.id == primary_result.winner),
                None
            )
            
            if winner_variant:
                return {
                    "variant_id": primary_result.winner,
                    "variant_name": winner_variant.name,
                    "metric": primary_metric,
                    "improvement": primary_result.relative_difference,
                    "confidence": primary_result.confidence_level,
                    "statistical_significance": primary_result.statistical_significance
                }
        
        return None
    
    async def _is_test_complete(self, test_id: str) -> bool:
        """Check if A/B test is complete"""
        campaign = self.campaigns[test_id]
        
        # Check if end date has passed
        if datetime.utcnow() > campaign["end_date"]:
            return True
        
        # Check if sample size has been reached
        total_sent = sum(
            metrics.sent_count for metrics in campaign["metrics"].values()
        )
        
        if total_sent >= campaign["sample_size"]:
            return True
        
        # Check if statistical significance has been achieved
        test_results = await self._calculate_statistical_tests(test_id)
        primary_result = None
        
        for result in test_results:
            if result.metric == campaign["primary_metric"]:
                primary_result = result
                break
        
        if primary_result and primary_result.statistical_significance:
            return True
        
        return False
    
    async def _calculate_sample_size(self, tenant_id: str, target_audience: Dict[str, Any]) -> int:
        """Calculate required sample size for A/B test"""
        # Mock calculation - in production, this would query actual audience size
        base_audience_size = 1000  # Mock base audience size
        
        # Adjust for target audience criteria
        if target_audience:
            # Mock adjustment based on criteria
            audience_multiplier = 0.5  # Assume criteria filter 50% of audience
        else:
            audience_multiplier = 1.0
        
        # Calculate required sample size for statistical significance
        # Using formula for two-proportion test with 95% confidence and 80% power
        effect_size = 0.05  # 5% minimum detectable difference
        required_sample_size = int(base_audience_size * audience_multiplier * 0.1)  # Mock calculation
        
        return max(required_sample_size, self.min_sample_size)
    
    async def stop_test(self, test_id: str) -> Dict[str, Any]:
        """Stop an A/B test and declare winner"""
        if test_id not in self.campaigns:
            raise ValueError(f"A/B test '{test_id}' not found")
        
        campaign = self.campaigns[test_id]
        
        if campaign["status"] != "running":
            raise ValueError(f"A/B test '{test_id}' is not running")
        
        # Update status
        campaign["status"] = "stopped"
        campaign["stopped_at"] = datetime.utcnow()
        
        # Get final results
        results = await self.get_test_results(test_id)
        
        return {
            "test_id": test_id,
            "status": "stopped",
            "stopped_at": campaign["stopped_at"].isoformat(),
            "final_results": results
        }
    
    async def get_campaign_recommendations(self, test_id: str) -> List[str]:
        """Get recommendations based on A/B test results"""
        if test_id not in self.campaigns:
            raise ValueError(f"A/B test '{test_id}' not found")
        
        results = await self.get_test_results(test_id)
        recommendations = []
        
        # Analyze results and generate recommendations
        if results["winner"]:
            winner = results["winner"]
            recommendations.append(f"Variant '{winner['variant_name']}' won with {winner['improvement']:.1f}% improvement in {winner['metric']}")
            
            if winner["statistical_significance"]:
                recommendations.append("Result is statistically significant - implement winning variant")
            else:
                recommendations.append("Result is not statistically significant - consider running test longer")
        else:
            recommendations.append("No clear winner detected - consider testing different variables")
        
        # Analyze metrics
        variant_metrics = results["variant_metrics"]
        
        # Check for low open rates
        low_open_variants = [
            variant_id for variant_id, metrics in variant_metrics.items()
            if metrics["open_rate"] < 0.15  # Less than 15% open rate
        ]
        
        if low_open_variants:
            recommendations.append("Consider improving subject lines and sender reputation")
        
        # Check for high unsubscribe rates
        high_unsubscribe_variants = [
            variant_id for variant_id, metrics in variant_metrics.items()
            if metrics["unsubscribe_rate"] > 0.05  # More than 5% unsubscribe rate
        ]
        
        if high_unsubscribe_variants:
            recommendations.append("High unsubscribe rate detected - review content and targeting")
        
        # Check for low conversion rates
        low_conversion_variants = [
            variant_id for variant_id, metrics in variant_metrics.items()
            if metrics["conversion_rate"] < 0.02  # Less than 2% conversion rate
        ]
        
        if low_conversion_variants:
            recommendations.append("Low conversion rate - improve call-to-action and landing page")
        
        if not recommendations:
            recommendations.append("Campaign metrics look good - continue with current strategy")
        
        return recommendations


# Helper function to get campaign A/B service
def get_campaign_ab_service(db: Session) -> CampaignABService:
    """Get campaign A/B testing service instance"""
    return CampaignABService(db)
