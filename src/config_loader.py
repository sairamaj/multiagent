"""
Configuration Loader for Multi-Agent System

This module provides configuration loading and management functionality
for the Azure DevOps automation agents.
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when there's an error loading or validating configuration"""
    pass


class ConfigLoader:
    """
    Load and validate configuration files from YAML.
    
    Supports environment-specific overrides and caching for performance.
    """
    
    def __init__(self, config_dir: Optional[str] = None, environment: Optional[str] = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_dir: Path to configuration directory. Defaults to '../config' relative to this file.
            environment: Environment name (development, staging, production). Defaults to ENVIRONMENT env var or 'development'.
        """
        if config_dir is None:
            # Default to config directory relative to this file
            current_dir = Path(__file__).parent
            config_dir = current_dir.parent / "config"
        
        self.config_dir = Path(config_dir)
        
        if not self.config_dir.exists():
            raise ConfigurationError(f"Configuration directory not found: {self.config_dir}")
        
        # Determine environment
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        
        # Cache for loaded configurations
        self._configs: Dict[str, Dict[str, Any]] = {}
        
        # Load environment-specific overrides
        self._env_overrides = self._load_environment_overrides()
        
        logger.info(f"ConfigLoader initialized for environment: {self.environment}")
    
    def _load_environment_overrides(self) -> Dict[str, Any]:
        """Load environment-specific configuration overrides"""
        env_file = self.config_dir / "environments.yaml"
        
        if not env_file.exists():
            logger.warning(f"Environment config file not found: {env_file}")
            return {}
        
        try:
            with open(env_file, 'r') as f:
                env_config = yaml.safe_load(f)
            
            # Return overrides for current environment
            return env_config.get(self.environment, {})
        except Exception as e:
            logger.error(f"Error loading environment overrides: {e}")
            return {}
    
    def load_config(self, config_name: str, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load a specific configuration file.
        
        Args:
            config_name: Name of configuration file (without .yaml extension)
            force_reload: If True, bypass cache and reload from disk
        
        Returns:
            Dictionary containing configuration data
        
        Raises:
            ConfigurationError: If configuration file cannot be loaded
        """
        # Return cached config if available
        if config_name in self._configs and not force_reload:
            return self._configs[config_name]
        
        config_path = self.config_dir / f"{config_name}.yaml"
        
        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if config is None:
                raise ConfigurationError(f"Empty configuration file: {config_path}")
            
            # Apply environment-specific overrides
            config = self._apply_overrides(config, config_name)
            
            # Expand environment variables in config values
            config = self._expand_env_vars(config)
            
            # Cache the configuration
            self._configs[config_name] = config
            
            logger.debug(f"Loaded configuration: {config_name}")
            return config
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing YAML in {config_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration {config_name}: {e}")
    
    def _apply_overrides(self, config: Dict[str, Any], config_name: str) -> Dict[str, Any]:
        """Apply environment-specific overrides to configuration"""
        if not self._env_overrides:
            return config
        
        # Look for overrides specific to this config
        overrides = self._env_overrides
        
        # Deep merge overrides into config
        return self._deep_merge(config, overrides)
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge override dictionary into base dictionary"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _expand_env_vars(self, config: Any) -> Any:
        """Recursively expand environment variables in configuration values"""
        if isinstance(config, dict):
            return {k: self._expand_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._expand_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            # Extract environment variable name
            env_var = config[2:-1]
            value = os.getenv(env_var)
            if value is None:
                logger.warning(f"Environment variable not found: {env_var}")
            return value or config
        else:
            return config
    
    def get_vm_pattern(self, pattern_name: str) -> Optional[Dict[str, Any]]:
        """
        Get VM naming pattern configuration.
        
        Args:
            pattern_name: Name of the pattern (e.g., 'ci_templates', 'production')
        
        Returns:
            Pattern configuration dictionary or None if not found
        """
        config = self.load_config("azure_resources")
        return config.get("vm_naming_patterns", {}).get(pattern_name)
    
    def get_blob_retention(self, artifact_type: str) -> Optional[Dict[str, Any]]:
        """
        Get blob retention policy for specific artifact type.
        
        Args:
            artifact_type: Type of artifact (e.g., 'ci_artifacts', 'vm_images')
        
        Returns:
            Retention policy dictionary or None if not found
        """
        config = self.load_config("storage_cleanup")
        return config.get("blob_retention", {}).get(artifact_type)
    
    def get_vm_cleanup_config(self) -> Dict[str, Any]:
        """Get VM cleanup configuration"""
        config = self.load_config("azure_resources")
        return config.get("vm_cleanup", {})
    
    def get_storage_accounts(self) -> List[Dict[str, Any]]:
        """Get list of configured storage accounts"""
        config = self.load_config("storage_cleanup")
        return config.get("storage_accounts", [])
    
    def get_pipeline_monitoring_config(self) -> Dict[str, Any]:
        """Get pipeline monitoring configuration"""
        config = self.load_config("build_monitoring")
        return config.get("pipeline_monitoring", {})
    
    def get_quality_gates(self) -> List[Dict[str, Any]]:
        """Get quality gate configurations"""
        config = self.load_config("build_monitoring")
        return config.get("quality_gates", {}).get("gates", [])
    
    def matches_pattern(self, name: str, pattern_name: str) -> bool:
        """
        Check if a name matches a VM naming pattern.
        
        Args:
            name: Name to check (e.g., VM name)
            pattern_name: Pattern to match against
        
        Returns:
            True if name matches pattern, False otherwise
        """
        pattern_config = self.get_vm_pattern(pattern_name)
        
        if not pattern_config:
            logger.warning(f"Pattern not found: {pattern_name}")
            return False
        
        regex = pattern_config.get("regex")
        if not regex:
            logger.warning(f"No regex defined for pattern: {pattern_name}")
            return False
        
        try:
            return bool(re.match(regex, name))
        except re.error as e:
            logger.error(f"Invalid regex for pattern {pattern_name}: {e}")
            return False
    
    def extract_version_from_name(self, name: str, pattern_name: str) -> Optional[str]:
        """
        Extract version information from a name based on pattern.
        
        Args:
            name: Name to parse (e.g., 'vhds-ci-wat-template-26-1-0.beta-20260213025457')
            pattern_name: Pattern type
        
        Returns:
            Version string or None if not found
        """
        pattern_config = self.get_vm_pattern(pattern_name)
        
        if not pattern_config or not self.matches_pattern(name, pattern_name):
            return None
        
        # For ci_templates pattern, extract version and release type
        if pattern_name == "ci_templates":
            # Example: vhds-ci-wat-template-26-1-0.beta-20260213025457
            match = re.search(r'template-(\d+-\d+-\d+)\.(\w+)-(\d+)', name)
            if match:
                version = match.group(1).replace('-', '.')
                release_type = match.group(2)
                timestamp = match.group(3)
                return f"{version}-{release_type}"
        
        return None
    
    def get_feature_flag(self, flag_name: str) -> bool:
        """
        Check if a feature flag is enabled for current environment.
        
        Args:
            flag_name: Name of feature flag
        
        Returns:
            True if enabled, False otherwise
        """
        env_config = self.load_config("environments")
        feature_flags = env_config.get("feature_flags", {}).get(self.environment, {})
        return feature_flags.get(flag_name, False)
    
    def validate_config(self, config_name: str) -> bool:
        """
        Validate that a configuration file is properly formatted.
        
        Args:
            config_name: Name of configuration to validate
        
        Returns:
            True if valid, raises ConfigurationError otherwise
        """
        try:
            config = self.load_config(config_name, force_reload=True)
            
            # Basic validation - ensure it's a dictionary
            if not isinstance(config, dict):
                raise ConfigurationError(f"Configuration must be a dictionary: {config_name}")
            
            # Specific validation based on config type
            if config_name == "azure_resources":
                self._validate_azure_resources_config(config)
            elif config_name == "storage_cleanup":
                self._validate_storage_cleanup_config(config)
            elif config_name == "build_monitoring":
                self._validate_build_monitoring_config(config)
            
            logger.info(f"Configuration validation passed: {config_name}")
            return True
            
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed for {config_name}: {e}")
    
    def _validate_azure_resources_config(self, config: Dict[str, Any]):
        """Validate azure_resources configuration"""
        required_sections = ["vm_naming_patterns", "vm_cleanup"]
        for section in required_sections:
            if section not in config:
                raise ConfigurationError(f"Missing required section: {section}")
        
        # Validate each VM pattern has required fields
        for pattern_name, pattern in config["vm_naming_patterns"].items():
            if "regex" not in pattern:
                raise ConfigurationError(f"VM pattern {pattern_name} missing 'regex' field")
    
    def _validate_storage_cleanup_config(self, config: Dict[str, Any]):
        """Validate storage_cleanup configuration"""
        required_sections = ["blob_retention", "storage_accounts"]
        for section in required_sections:
            if section not in config:
                raise ConfigurationError(f"Missing required section: {section}")
        
        # Validate each retention policy has required fields
        for artifact_type, policy in config["blob_retention"].items():
            required_fields = ["keep_latest_count", "age_threshold_days"]
            for field in required_fields:
                if field not in policy:
                    raise ConfigurationError(
                        f"Retention policy {artifact_type} missing '{field}' field"
                    )
    
    def _validate_build_monitoring_config(self, config: Dict[str, Any]):
        """Validate build_monitoring configuration"""
        required_sections = ["pipeline_monitoring", "build_failure_analysis"]
        for section in required_sections:
            if section not in config:
                raise ConfigurationError(f"Missing required section: {section}")
    
    def reload_all(self):
        """Reload all cached configurations from disk"""
        logger.info("Reloading all configurations")
        self._configs.clear()
        self._env_overrides = self._load_environment_overrides()
    
    def get_all_vm_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Get all VM naming patterns"""
        config = self.load_config("azure_resources")
        return config.get("vm_naming_patterns", {})
    
    def get_all_blob_retention_policies(self) -> Dict[str, Dict[str, Any]]:
        """Get all blob retention policies"""
        config = self.load_config("storage_cleanup")
        return config.get("blob_retention", {})


# Singleton instance for global use
_default_loader: Optional[ConfigLoader] = None


def get_config_loader(
    config_dir: Optional[str] = None,
    environment: Optional[str] = None
) -> ConfigLoader:
    """
    Get the global ConfigLoader instance.
    
    Args:
        config_dir: Optional config directory path
        environment: Optional environment name
    
    Returns:
        ConfigLoader instance
    """
    global _default_loader
    
    if _default_loader is None:
        _default_loader = ConfigLoader(config_dir=config_dir, environment=environment)
    
    return _default_loader


# Convenience module-level instance
config_loader = get_config_loader()
