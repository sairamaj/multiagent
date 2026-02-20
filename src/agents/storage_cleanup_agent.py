"""
Storage Cleanup Agent

This agent handles Azure Storage blob cleanup tasks including:
- Cleaning up old artifacts based on retention policies
- Managing storage account containers
- Monitoring storage usage
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

# Import config loader
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config_loader import config_loader

logger = logging.getLogger(__name__)


@dataclass
class Blob:
    """Represents an Azure Storage Blob"""
    name: str
    container: str
    storage_account: str
    size_bytes: int
    last_modified: datetime
    content_type: str
    tags: Dict[str, str]


class StorageCleanupAgent:
    """
    Agent responsible for Azure Storage cleanup operations.
    
    Uses configuration from config_loader for retention policies.
    """
    
    def __init__(self):
        """Initialize the Storage Cleanup Agent"""
        self.config_loader = config_loader
        logger.info("StorageCleanupAgent initialized")
    
    def cleanup_old_blobs(
        self,
        artifact_type: str = "ci_artifacts",
        storage_account: Optional[str] = None,
        dry_run: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Clean up blobs based on retention policy.
        
        Args:
            artifact_type: Type of artifact (e.g., 'ci_artifacts', 'vm_images')
            storage_account: Specific storage account to clean (optional)
            dry_run: If True, only simulate cleanup. Uses config value if None.
        
        Returns:
            Dictionary with cleanup results
        """
        logger.info(f"Starting blob cleanup for artifact type: {artifact_type}")
        
        # Load retention policy
        retention = self.config_loader.get_blob_retention(artifact_type)
        
        if not retention:
            return {
                "success": False,
                "error": f"Unknown artifact type: {artifact_type}"
            }
        
        # Get cleanup parameters from config
        keep_count = retention.get("keep_latest_count", 5)
        age_days = retention.get("age_threshold_days", 90)
        pattern = retention.get("pattern", "*")
        size_limit_gb = retention.get("size_limit_gb")
        
        # Get safety settings
        safety_config = self.config_loader.load_config("storage_cleanup").get("safety", {})
        exclude_tags = safety_config.get("exclude_tags", [])
        min_versions = safety_config.get("minimum_versions_to_keep", 2)
        max_batch = safety_config.get("max_delete_batch_size", 100)
        
        # Use dry_run from parameter or config
        if dry_run is None:
            dry_run = safety_config.get("dry_run", False)
        
        logger.info(f"Cleanup config: keep={keep_count}, age_days={age_days}, pattern={pattern}, dry_run={dry_run}")
        
        # Get containers to clean
        containers = retention.get("containers", [])
        
        if not containers:
            logger.warning(f"No containers configured for artifact type: {artifact_type}")
            return {"success": False, "error": "No containers configured"}
        
        # Process each container
        results = {
            "success": True,
            "dry_run": dry_run,
            "artifact_type": artifact_type,
            "containers_processed": 0,
            "total_blobs": 0,
            "blobs_deleted": 0,
            "space_freed_gb": 0.0,
            "deleted_blobs": []
        }
        
        for container in containers:
            container_result = self._cleanup_container(
                container=container,
                pattern=pattern,
                keep_count=keep_count,
                age_days=age_days,
                exclude_tags=exclude_tags,
                min_versions=min_versions,
                max_batch=max_batch,
                dry_run=dry_run
            )
            
            results["containers_processed"] += 1
            results["total_blobs"] += container_result["total_blobs"]
            results["blobs_deleted"] += container_result["blobs_deleted"]
            results["space_freed_gb"] += container_result["space_freed_gb"]
            results["deleted_blobs"].extend(container_result["deleted_blobs"])
        
        logger.info(f"Cleanup completed: {results['blobs_deleted']} blobs, {results['space_freed_gb']:.2f} GB freed")
        
        return results
    
    def _cleanup_container(
        self,
        container: str,
        pattern: str,
        keep_count: int,
        age_days: int,
        exclude_tags: List[str],
        min_versions: int,
        max_batch: int,
        dry_run: bool
    ) -> Dict[str, Any]:
        """Clean up blobs in a specific container"""
        logger.info(f"Cleaning container: {container}")
        
        # List blobs in container (mock in this example)
        all_blobs = self._list_blobs(container, pattern)
        
        # Exclude protected blobs
        blobs_to_consider = [
            blob for blob in all_blobs
            if not any(tag in blob.tags.values() for tag in exclude_tags)
        ]
        
        # Sort by last modified (newest first)
        sorted_blobs = sorted(
            blobs_to_consider,
            key=lambda x: x.last_modified,
            reverse=True
        )
        
        # Ensure we keep minimum versions
        actual_keep_count = max(keep_count, min_versions)
        
        # Identify blobs to delete
        blobs_to_delete = []
        age_cutoff = datetime.now() - timedelta(days=age_days)
        
        for i, blob in enumerate(sorted_blobs):
            # Keep the latest N blobs
            if i < actual_keep_count:
                continue
            
            # Delete if older than threshold
            if blob.last_modified < age_cutoff:
                blobs_to_delete.append(blob)
                
                # Respect batch size limit
                if len(blobs_to_delete) >= max_batch:
                    logger.warning(f"Reached max batch size ({max_batch}), stopping")
                    break
        
        # Execute deletion
        space_freed = 0.0
        deleted_blobs = []
        
        for blob in blobs_to_delete:
            if dry_run:
                logger.info(f"DRY RUN: Would delete blob {blob.name}")
                action = "would_delete"
            else:
                try:
                    self._delete_blob(blob)
                    logger.info(f"Deleted blob: {blob.name}")
                    action = "deleted"
                except Exception as e:
                    logger.error(f"Failed to delete blob {blob.name}: {e}")
                    action = "failed"
            
            space_freed += blob.size_bytes / (1024**3)  # Convert to GB
            deleted_blobs.append({
                "name": blob.name,
                "container": blob.container,
                "size_mb": blob.size_bytes / (1024**2),
                "last_modified": blob.last_modified.isoformat(),
                "action": action
            })
        
        return {
            "container": container,
            "total_blobs": len(all_blobs),
            "blobs_deleted": len(blobs_to_delete),
            "space_freed_gb": space_freed,
            "deleted_blobs": deleted_blobs
        }
    
    def get_storage_usage(self, artifact_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get storage usage statistics.
        
        Args:
            artifact_type: Optional artifact type to filter by
        
        Returns:
            Storage usage statistics
        """
        logger.info("Getting storage usage statistics")
        
        if artifact_type:
            retention = self.config_loader.get_blob_retention(artifact_type)
            containers = retention.get("containers", []) if retention else []
        else:
            # Get all containers from all retention policies
            policies = self.config_loader.get_all_blob_retention_policies()
            containers = []
            for policy in policies.values():
                containers.extend(policy.get("containers", []))
        
        total_size = 0
        total_blobs = 0
        container_stats = []
        
        for container in containers:
            blobs = self._list_blobs(container, "*")
            size = sum(blob.size_bytes for blob in blobs)
            
            total_size += size
            total_blobs += len(blobs)
            
            container_stats.append({
                "container": container,
                "blob_count": len(blobs),
                "size_gb": size / (1024**3)
            })
        
        return {
            "total_containers": len(containers),
            "total_blobs": total_blobs,
            "total_size_gb": total_size / (1024**3),
            "container_stats": container_stats
        }
    
    def get_retention_policies(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all configured blob retention policies.
        
        Returns:
            Dictionary of retention policies
        """
        return self.config_loader.get_all_blob_retention_policies()
    
    # Mock methods - In real implementation these would use Azure SDK
    
    def _list_blobs(self, container: str, pattern: str) -> List[Blob]:
        """
        Mock method to list blobs.
        In real implementation, this would use Azure SDK.
        """
        # Example mock data
        return [
            Blob(
                name="build-2026-02-10.zip",
                container=container,
                storage_account="devopsartifacts",
                size_bytes=104857600,  # 100 MB
                last_modified=datetime(2026, 2, 10, 14, 30, 0),
                content_type="application/zip",
                tags={}
            ),
            Blob(
                name="build-2026-01-15.zip",
                container=container,
                storage_account="devopsartifacts",
                size_bytes=98304000,  # 93.75 MB
                last_modified=datetime(2026, 1, 15, 10, 20, 0),
                content_type="application/zip",
                tags={}
            ),
            Blob(
                name="build-2025-12-20.zip",
                container=container,
                storage_account="devopsartifacts",
                size_bytes=102400000,  # 97.66 MB
                last_modified=datetime(2025, 12, 20, 8, 15, 0),
                content_type="application/zip",
                tags={"permanent": "true"}
            )
        ]
    
    def _delete_blob(self, blob: Blob):
        """
        Mock method to delete a blob.
        In real implementation, this would use Azure SDK.
        """
        logger.info(f"Mock: Deleting blob {blob.name}")
        # In real implementation:
        # from azure.storage.blob import BlobServiceClient
        # blob_client.delete_blob(blob.name)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    agent = StorageCleanupAgent()
    
    # Example 1: Get retention policies
    print("\n=== Example 1: Get Retention Policies ===")
    policies = agent.get_retention_policies()
    for artifact_type, policy in policies.items():
        print(f"  {artifact_type}: keep {policy['keep_latest_count']}, age {policy['age_threshold_days']} days")
    
    # Example 2: Get storage usage
    print("\n=== Example 2: Get Storage Usage ===")
    usage = agent.get_storage_usage()
    print(f"  Total containers: {usage['total_containers']}")
    print(f"  Total blobs: {usage['total_blobs']}")
    print(f"  Total size: {usage['total_size_gb']:.2f} GB")
    
    # Example 3: Cleanup old blobs (dry run)
    print("\n=== Example 3: Cleanup Old Blobs (Dry Run) ===")
    cleanup_result = agent.cleanup_old_blobs(artifact_type="ci_artifacts", dry_run=True)
    print(f"  Containers processed: {cleanup_result['containers_processed']}")
    print(f"  Blobs to delete: {cleanup_result['blobs_deleted']}")
    print(f"  Space to free: {cleanup_result['space_freed_gb']:.2f} GB")
