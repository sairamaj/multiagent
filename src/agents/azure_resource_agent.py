"""
Azure Resource Agent

This agent handles Azure resource management tasks including:
- Querying VMs and resource groups
- VM cleanup based on configuration
- Resource monitoring
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
class VirtualMachine:
    """Represents an Azure Virtual Machine"""
    name: str
    resource_group: str
    location: str
    vm_size: str
    created_date: datetime
    status: str
    tags: Dict[str, str]


class AzureResourceAgent:
    """
    Agent responsible for Azure resource management operations.
    
    Uses configuration from config_loader for cleanup policies and naming patterns.
    """
    
    def __init__(self):
        """Initialize the Azure Resource Agent"""
        self.config_loader = config_loader
        logger.info("AzureResourceAgent initialized")
    
    def cleanup_old_vms(
        self,
        pattern_type: str = "ci_templates",
        dry_run: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Clean up VMs based on configuration rules.
        
        Args:
            pattern_type: VM naming pattern type (e.g., 'ci_templates', 'staging')
            dry_run: If True, only simulate cleanup. Uses config value if None.
        
        Returns:
            Dictionary with cleanup results
        """
        logger.info(f"Starting VM cleanup for pattern: {pattern_type}")
        
        # Load configuration
        vm_pattern = self.config_loader.get_vm_pattern(pattern_type)
        cleanup_config = self.config_loader.get_vm_cleanup_config()
        
        if not vm_pattern:
            return {
                "success": False,
                "error": f"Unknown VM pattern type: {pattern_type}"
            }
        
        # Get cleanup parameters from config
        keep_count = cleanup_config.get("keep_latest_count", 5)
        age_threshold_days = cleanup_config.get("age_threshold_days", 30)
        exclude_tags = cleanup_config.get("exclude_tags", [])
        require_confirmation = cleanup_config.get("require_confirmation", True)
        
        # Use dry_run from parameter or config
        if dry_run is None:
            dry_run = cleanup_config.get("dry_run", False)
        
        logger.info(f"Cleanup config: keep={keep_count}, age_days={age_threshold_days}, dry_run={dry_run}")
        
        # Get all VMs (in real implementation, this would call Azure SDK)
        all_vms = self._list_vms()
        
        # Filter VMs matching the pattern
        matching_vms = [
            vm for vm in all_vms
            if self.config_loader.matches_pattern(vm.name, pattern_type)
        ]
        
        logger.info(f"Found {len(matching_vms)} VMs matching pattern {pattern_type}")
        
        # Exclude VMs with protected tags
        vms_to_consider = [
            vm for vm in matching_vms
            if not any(tag in vm.tags.values() for tag in exclude_tags)
        ]
        
        logger.info(f"{len(vms_to_consider)} VMs after excluding protected tags")
        
        # Sort by creation date (newest first)
        sorted_vms = sorted(
            vms_to_consider,
            key=lambda x: x.created_date,
            reverse=True
        )
        
        # Identify VMs to delete (older than threshold and beyond keep count)
        vms_to_delete = []
        age_cutoff = datetime.now() - timedelta(days=age_threshold_days)
        
        for i, vm in enumerate(sorted_vms):
            # Keep the latest N VMs regardless of age
            if i < keep_count:
                continue
            
            # Delete if older than threshold
            if vm.created_date < age_cutoff:
                vms_to_delete.append(vm)
        
        logger.info(f"Identified {len(vms_to_delete)} VMs for deletion")
        
        # Execute deletion (or simulate if dry_run)
        results = {
            "success": True,
            "dry_run": dry_run,
            "pattern_type": pattern_type,
            "total_vms": len(all_vms),
            "matching_vms": len(matching_vms),
            "vms_to_delete": len(vms_to_delete),
            "deleted_vms": [],
            "kept_vms": keep_count,
            "age_threshold_days": age_threshold_days
        }
        
        if vms_to_delete:
            if dry_run:
                logger.info("DRY RUN: Would delete the following VMs:")
                for vm in vms_to_delete:
                    logger.info(f"  - {vm.name} (created: {vm.created_date})")
                    results["deleted_vms"].append({
                        "name": vm.name,
                        "resource_group": vm.resource_group,
                        "created_date": vm.created_date.isoformat(),
                        "action": "would_delete"
                    })
            else:
                if require_confirmation:
                    logger.warning("Confirmation required for VM deletion (set in config)")
                    results["requires_confirmation"] = True
                    results["pending_deletions"] = [vm.name for vm in vms_to_delete]
                else:
                    # Actually delete VMs
                    for vm in vms_to_delete:
                        try:
                            self._delete_vm(vm)
                            logger.info(f"Deleted VM: {vm.name}")
                            results["deleted_vms"].append({
                                "name": vm.name,
                                "resource_group": vm.resource_group,
                                "created_date": vm.created_date.isoformat(),
                                "action": "deleted"
                            })
                        except Exception as e:
                            logger.error(f"Failed to delete VM {vm.name}: {e}")
                            results["deleted_vms"].append({
                                "name": vm.name,
                                "error": str(e),
                                "action": "failed"
                            })
        
        return results
    
    def list_vms_by_pattern(self, pattern_type: str) -> List[Dict[str, Any]]:
        """
        List all VMs matching a specific naming pattern.
        
        Args:
            pattern_type: VM naming pattern type
        
        Returns:
            List of VM dictionaries
        """
        logger.info(f"Listing VMs for pattern: {pattern_type}")
        
        all_vms = self._list_vms()
        matching_vms = [
            {
                "name": vm.name,
                "resource_group": vm.resource_group,
                "status": vm.status,
                "created_date": vm.created_date.isoformat(),
                "vm_size": vm.vm_size,
                "tags": vm.tags
            }
            for vm in all_vms
            if self.config_loader.matches_pattern(vm.name, pattern_type)
        ]
        
        logger.info(f"Found {len(matching_vms)} matching VMs")
        return matching_vms
    
    def get_vm_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all configured VM naming patterns.
        
        Returns:
            Dictionary of pattern configurations
        """
        return self.config_loader.get_all_vm_patterns()
    
    def check_vm_compliance(self, vm_name: str) -> Dict[str, Any]:
        """
        Check if a VM name complies with any configured naming pattern.
        
        Args:
            vm_name: Name of the VM to check
        
        Returns:
            Compliance check results
        """
        patterns = self.config_loader.get_all_vm_patterns()
        
        results = {
            "vm_name": vm_name,
            "compliant": False,
            "matching_patterns": []
        }
        
        for pattern_name in patterns.keys():
            if self.config_loader.matches_pattern(vm_name, pattern_name):
                results["compliant"] = True
                results["matching_patterns"].append(pattern_name)
        
        return results
    
    # Mock methods - In real implementation these would use Azure SDK
    
    def _list_vms(self) -> List[VirtualMachine]:
        """
        Mock method to list VMs.
        In real implementation, this would use Azure SDK to query VMs.
        """
        # Example mock data
        return [
            VirtualMachine(
                name="vhds-ci-wat-template-26-1-0.beta-20260213025457",
                resource_group="rg-ci-templates",
                location="eastus",
                vm_size="Standard_D2s_v3",
                created_date=datetime(2026, 2, 13, 2, 54, 57),
                status="Running",
                tags={}
            ),
            VirtualMachine(
                name="vhds-ci-wat-template-25-2-1.release-20260115103022",
                resource_group="rg-ci-templates",
                location="eastus",
                vm_size="Standard_D2s_v3",
                created_date=datetime(2026, 1, 15, 10, 30, 22),
                status="Stopped",
                tags={}
            ),
            VirtualMachine(
                name="vhds-prod-api-1.2.3",
                resource_group="rg-production",
                location="eastus",
                vm_size="Standard_D4s_v3",
                created_date=datetime(2025, 12, 1, 9, 0, 0),
                status="Running",
                tags={"permanent": "true"}
            )
        ]
    
    def _delete_vm(self, vm: VirtualMachine):
        """
        Mock method to delete a VM.
        In real implementation, this would use Azure SDK to delete the VM.
        """
        logger.info(f"Mock: Deleting VM {vm.name}")
        # In real implementation:
        # from azure.mgmt.compute import ComputeManagementClient
        # compute_client.virtual_machines.begin_delete(vm.resource_group, vm.name)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    agent = AzureResourceAgent()
    
    # Example 1: List VMs by pattern
    print("\n=== Example 1: List CI Template VMs ===")
    ci_vms = agent.list_vms_by_pattern("ci_templates")
    for vm in ci_vms:
        print(f"  {vm['name']} - {vm['status']}")
    
    # Example 2: Check VM compliance
    print("\n=== Example 2: Check VM Name Compliance ===")
    test_names = [
        "vhds-ci-wat-template-26-1-0.beta-20260213025457",
        "random-vm-name",
        "vhds-prod-api-1.2.3"
    ]
    for name in test_names:
        result = agent.check_vm_compliance(name)
        print(f"  {name}: {'✓' if result['compliant'] else '✗'} {result.get('matching_patterns', [])}")
    
    # Example 3: Cleanup old VMs (dry run)
    print("\n=== Example 3: Cleanup Old VMs (Dry Run) ===")
    cleanup_result = agent.cleanup_old_vms(pattern_type="ci_templates", dry_run=True)
    print(f"  Total VMs: {cleanup_result['total_vms']}")
    print(f"  Matching pattern: {cleanup_result['matching_vms']}")
    print(f"  Would delete: {cleanup_result['vms_to_delete']}")
