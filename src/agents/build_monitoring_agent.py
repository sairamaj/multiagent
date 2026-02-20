"""
Build Monitoring Agent

This agent handles Azure DevOps build monitoring tasks including:
- Querying pipeline status
- Analyzing build failures
- Monitoring deployments
- Tracking build metrics
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import re

# Import config loader
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config_loader import config_loader

logger = logging.getLogger(__name__)


@dataclass
class BuildResult:
    """Represents a build result"""
    build_id: int
    pipeline_name: str
    status: str
    result: str
    start_time: datetime
    finish_time: datetime
    duration_minutes: int
    triggered_by: str
    error_message: Optional[str] = None


@dataclass
class Pipeline:
    """Represents an Azure DevOps pipeline"""
    id: int
    name: str
    project: str
    folder: str
    latest_build_status: str


class BuildMonitoringAgent:
    """
    Agent responsible for Azure DevOps build monitoring operations.
    
    Uses configuration from config_loader for monitoring policies and thresholds.
    """
    
    def __init__(self):
        """Initialize the Build Monitoring Agent"""
        self.config_loader = config_loader
        logger.info("BuildMonitoringAgent initialized")
    
    def query_pipeline_status(self, pipeline_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query pipeline status.
        
        Args:
            pipeline_name: Specific pipeline name (optional)
        
        Returns:
            List of pipeline statuses
        """
        logger.info(f"Querying pipeline status: {pipeline_name or 'all'}")
        
        # Get monitored pipelines from config
        monitoring_config = self.config_loader.get_pipeline_monitoring_config()
        monitored_pipelines = monitoring_config.get("monitored_pipelines", [])
        
        # Mock data - in real implementation, this would use Azure DevOps REST API
        all_pipelines = self._get_mock_pipelines()
        
        if pipeline_name:
            pipelines = [p for p in all_pipelines if p.name == pipeline_name]
        else:
            # Return only monitored pipelines if specified in config
            if monitored_pipelines:
                monitored_names = [p["name"] for p in monitored_pipelines]
                pipelines = [p for p in all_pipelines if p.name in monitored_names]
            else:
                pipelines = all_pipelines
        
        results = []
        for pipeline in pipelines:
            results.append({
                "pipeline_id": pipeline.id,
                "name": pipeline.name,
                "project": pipeline.project,
                "latest_status": pipeline.latest_build_status,
                "folder": pipeline.folder
            })
        
        logger.info(f"Found {len(results)} pipelines")
        return results
    
    def get_build_failures(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get failed builds in the last N days.
        
        Args:
            days: Number of days to look back
        
        Returns:
            List of failed build information
        """
        logger.info(f"Getting build failures from last {days} days")
        
        # Mock data - in real implementation, this would use Azure DevOps REST API
        all_builds = self._get_mock_builds()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        failed_builds = [
            build for build in all_builds
            if build.result == "failed" and build.start_time > cutoff_date
        ]
        
        results = []
        for build in failed_builds:
            failure_category = self._categorize_failure(build.error_message or "")
            
            results.append({
                "build_id": build.build_id,
                "pipeline": build.pipeline_name,
                "status": build.status,
                "result": build.result,
                "start_time": build.start_time.isoformat(),
                "duration_minutes": build.duration_minutes,
                "error_message": build.error_message,
                "failure_category": failure_category,
                "triggered_by": build.triggered_by
            })
        
        logger.info(f"Found {len(results)} failed builds")
        return results
    
    def analyze_build_failures(self, days: int = 7) -> Dict[str, Any]:
        """
        Analyze build failures and identify patterns.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Analysis results with patterns and recommendations
        """
        logger.info(f"Analyzing build failures from last {days} days")
        
        failures = self.get_build_failures(days)
        
        if not failures:
            return {
                "total_failures": 0,
                "message": f"No build failures in the last {days} days"
            }
        
        # Categorize failures
        categories = {}
        pipelines = {}
        
        for failure in failures:
            # Count by category
            category = failure["failure_category"]
            categories[category] = categories.get(category, 0) + 1
            
            # Count by pipeline
            pipeline = failure["pipeline"]
            pipelines[pipeline] = pipelines.get(pipeline, 0) + 1
        
        # Get top categories and pipelines
        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
        top_pipelines = sorted(pipelines.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Generate recommendations
        recommendations = self._generate_recommendations(top_categories)
        
        analysis = {
            "total_failures": len(failures),
            "analysis_period_days": days,
            "failure_categories": dict(top_categories),
            "affected_pipelines": dict(top_pipelines),
            "recommendations": recommendations,
            "recent_failures": failures[:5]  # Last 5 failures
        }
        
        logger.info(f"Analysis complete: {len(failures)} total failures")
        return analysis
    
    def _categorize_failure(self, error_message: str) -> str:
        """Categorize failure based on error message"""
        if not error_message:
            return "unknown"
        
        # Load failure patterns from config
        config = self.config_loader.load_config("build_monitoring")
        patterns = config.get("build_failure_analysis", {}).get("failure_patterns", [])
        
        # Check against configured patterns
        for pattern_config in patterns:
            pattern = pattern_config.get("pattern", "")
            category = pattern_config.get("category", "unknown")
            
            if re.search(pattern, error_message, re.IGNORECASE):
                return category
        
        return "unknown"
    
    def _generate_recommendations(self, top_categories: List[tuple]) -> List[str]:
        """Generate recommendations based on failure patterns"""
        recommendations = []
        
        # Load failure patterns with suggestions from config
        config = self.config_loader.load_config("build_monitoring")
        patterns = config.get("build_failure_analysis", {}).get("failure_patterns", [])
        
        for category, count in top_categories:
            # Find matching pattern in config
            for pattern_config in patterns:
                if pattern_config.get("category") == category:
                    action = pattern_config.get("suggested_action", "Investigate this issue")
                    recommendations.append(
                        f"{category.title()} ({count} occurrences): {action}"
                    )
                    break
        
        return recommendations
    
    def get_deployment_status(self, environment: str = "production") -> Dict[str, Any]:
        """
        Get deployment status for an environment.
        
        Args:
            environment: Environment name (development, staging, production)
        
        Returns:
            Deployment status information
        """
        logger.info(f"Getting deployment status for: {environment}")
        
        # Load deployment monitoring config
        config = self.config_loader.load_config("build_monitoring")
        deployment_config = config.get("deployment_monitoring", {})
        monitored_envs = deployment_config.get("monitored_environments", [])
        
        # Find environment config
        env_config = next(
            (e for e in monitored_envs if e["name"].lower() == environment.lower()),
            None
        )
        
        # Mock deployment data
        deployment = {
            "environment": environment,
            "status": "succeeded",
            "last_deployment": datetime.now() - timedelta(hours=2),
            "version": "1.2.3",
            "deployed_by": "user@example.com",
            "requires_approval": env_config.get("require_approval", False) if env_config else False
        }
        
        return deployment
    
    def get_build_metrics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get build performance metrics.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Build metrics
        """
        logger.info(f"Getting build metrics for last {days} days")
        
        # Mock data - in real implementation, calculate from actual builds
        all_builds = self._get_mock_builds()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_builds = [b for b in all_builds if b.start_time > cutoff_date]
        
        if not recent_builds:
            return {"message": "No builds in the specified period"}
        
        # Calculate metrics
        total_builds = len(recent_builds)
        successful_builds = len([b for b in recent_builds if b.result == "succeeded"])
        failed_builds = len([b for b in recent_builds if b.result == "failed"])
        
        success_rate = (successful_builds / total_builds * 100) if total_builds > 0 else 0
        
        avg_duration = sum(b.duration_minutes for b in recent_builds) / total_builds
        
        # Load performance config
        config = self.config_loader.load_config("build_monitoring")
        perf_config = config.get("performance_metrics", {})
        duration_threshold = perf_config.get("duration_threshold_minutes", 60)
        success_rate_threshold = perf_config.get("success_rate_threshold_percent", 80)
        
        metrics = {
            "period_days": days,
            "total_builds": total_builds,
            "successful_builds": successful_builds,
            "failed_builds": failed_builds,
            "success_rate_percent": round(success_rate, 2),
            "average_duration_minutes": round(avg_duration, 2),
            "alerts": []
        }
        
        # Check thresholds
        if success_rate < success_rate_threshold:
            metrics["alerts"].append(
                f"Success rate ({success_rate:.1f}%) is below threshold ({success_rate_threshold}%)"
            )
        
        if avg_duration > duration_threshold:
            metrics["alerts"].append(
                f"Average duration ({avg_duration:.1f} min) exceeds threshold ({duration_threshold} min)"
            )
        
        logger.info(f"Metrics calculated: {success_rate:.1f}% success rate")
        return metrics
    
    # Mock methods - In real implementation these would use Azure DevOps REST API
    
    def _get_mock_pipelines(self) -> List[Pipeline]:
        """Mock method to get pipelines"""
        return [
            Pipeline(
                id=1,
                name="CI-Main",
                project="MyProject",
                folder="CI",
                latest_build_status="succeeded"
            ),
            Pipeline(
                id=2,
                name="CD-Production",
                project="MyProject",
                folder="CD",
                latest_build_status="succeeded"
            ),
            Pipeline(
                id=3,
                name="Nightly-Tests",
                project="MyProject",
                folder="Tests",
                latest_build_status="failed"
            )
        ]
    
    def _get_mock_builds(self) -> List[BuildResult]:
        """Mock method to get build results"""
        now = datetime.now()
        return [
            BuildResult(
                build_id=101,
                pipeline_name="CI-Main",
                status="completed",
                result="succeeded",
                start_time=now - timedelta(hours=2),
                finish_time=now - timedelta(hours=1, minutes=45),
                duration_minutes=15,
                triggered_by="user1@example.com"
            ),
            BuildResult(
                build_id=102,
                pipeline_name="Nightly-Tests",
                status="completed",
                result="failed",
                start_time=now - timedelta(days=1),
                finish_time=now - timedelta(days=1) + timedelta(minutes=30),
                duration_minutes=30,
                triggered_by="schedule",
                error_message="OutOfMemoryError: Java heap space"
            ),
            BuildResult(
                build_id=103,
                pipeline_name="CI-Main",
                status="completed",
                result="failed",
                start_time=now - timedelta(days=2),
                finish_time=now - timedelta(days=2) + timedelta(minutes=10),
                duration_minutes=10,
                triggered_by="user2@example.com",
                error_message="npm ERR! code ENOTFOUND"
            ),
            BuildResult(
                build_id=104,
                pipeline_name="CD-Production",
                status="completed",
                result="succeeded",
                start_time=now - timedelta(days=3),
                finish_time=now - timedelta(days=3) + timedelta(minutes=45),
                duration_minutes=45,
                triggered_by="user1@example.com"
            )
        ]


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    agent = BuildMonitoringAgent()
    
    # Example 1: Query pipeline status
    print("\n=== Example 1: Query Pipeline Status ===")
    pipelines = agent.query_pipeline_status()
    for pipeline in pipelines:
        print(f"  {pipeline['name']}: {pipeline['latest_status']}")
    
    # Example 2: Get build failures
    print("\n=== Example 2: Get Build Failures (Last 7 Days) ===")
    failures = agent.get_build_failures(days=7)
    print(f"  Total failures: {len(failures)}")
    for failure in failures:
        print(f"  - {failure['pipeline']}: {failure['failure_category']}")
    
    # Example 3: Analyze build failures
    print("\n=== Example 3: Analyze Build Failures ===")
    analysis = agent.analyze_build_failures(days=7)
    print(f"  Total failures: {analysis['total_failures']}")
    print(f"  Top categories: {analysis['failure_categories']}")
    print("  Recommendations:")
    for rec in analysis.get('recommendations', []):
        print(f"    - {rec}")
    
    # Example 4: Get build metrics
    print("\n=== Example 4: Get Build Metrics ===")
    metrics = agent.get_build_metrics(days=7)
    print(f"  Success rate: {metrics['success_rate_percent']}%")
    print(f"  Average duration: {metrics['average_duration_minutes']} minutes")
    if metrics.get('alerts'):
        print("  Alerts:")
        for alert in metrics['alerts']:
            print(f"    - {alert}")
