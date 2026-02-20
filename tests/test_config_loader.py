"""
Unit tests for ConfigLoader

Tests configuration loading, validation, and pattern matching functionality.
"""

import unittest
import os
import tempfile
import yaml
from pathlib import Path
from datetime import datetime

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config_loader import ConfigLoader, ConfigurationError


class TestConfigLoader(unittest.TestCase):
    """Test cases for ConfigLoader class"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test configuration directory"""
        cls.test_config_dir = Path(__file__).parent.parent / "config"
        
        # Verify config directory exists
        if not cls.test_config_dir.exists():
            raise unittest.SkipTest("Config directory not found - run from project root")
    
    def setUp(self):
        """Set up test fixtures"""
        self.loader = ConfigLoader(
            config_dir=str(self.test_config_dir),
            environment="development"
        )
    
    def test_loader_initialization(self):
        """Test ConfigLoader initializes correctly"""
        self.assertIsNotNone(self.loader)
        self.assertEqual(self.loader.environment, "development")
        self.assertTrue(self.loader.config_dir.exists())
    
    def test_load_azure_resources_config(self):
        """Test loading azure_resources configuration"""
        config = self.loader.load_config("azure_resources")
        
        self.assertIsNotNone(config)
        self.assertIn("vm_naming_patterns", config)
        self.assertIn("vm_cleanup", config)
    
    def test_load_storage_cleanup_config(self):
        """Test loading storage_cleanup configuration"""
        config = self.loader.load_config("storage_cleanup")
        
        self.assertIsNotNone(config)
        self.assertIn("blob_retention", config)
        self.assertIn("storage_accounts", config)
    
    def test_load_build_monitoring_config(self):
        """Test loading build_monitoring configuration"""
        config = self.loader.load_config("build_monitoring")
        
        self.assertIsNotNone(config)
        self.assertIn("pipeline_monitoring", config)
        self.assertIn("build_failure_analysis", config)
    
    def test_config_caching(self):
        """Test that configurations are cached"""
        # Load config twice
        config1 = self.loader.load_config("azure_resources")
        config2 = self.loader.load_config("azure_resources")
        
        # Should return the same object from cache
        self.assertIs(config1, config2)
    
    def test_force_reload(self):
        """Test force reload bypasses cache"""
        config1 = self.loader.load_config("azure_resources")
        config2 = self.loader.load_config("azure_resources", force_reload=True)
        
        # Should return different objects
        self.assertIsNot(config1, config2)
        # But content should be the same
        self.assertEqual(config1, config2)
    
    def test_get_vm_pattern(self):
        """Test getting VM naming patterns"""
        # Test ci_templates pattern
        ci_pattern = self.loader.get_vm_pattern("ci_templates")
        self.assertIsNotNone(ci_pattern)
        self.assertIn("regex", ci_pattern)
        self.assertIn("pattern", ci_pattern)
        
        # Test production pattern
        prod_pattern = self.loader.get_vm_pattern("production")
        self.assertIsNotNone(prod_pattern)
        
        # Test non-existent pattern
        invalid_pattern = self.loader.get_vm_pattern("nonexistent")
        self.assertIsNone(invalid_pattern)
    
    def test_get_blob_retention(self):
        """Test getting blob retention policies"""
        # Test ci_artifacts retention
        ci_retention = self.loader.get_blob_retention("ci_artifacts")
        self.assertIsNotNone(ci_retention)
        self.assertIn("keep_latest_count", ci_retention)
        self.assertIn("age_threshold_days", ci_retention)
        
        # Test vm_images retention
        vm_retention = self.loader.get_blob_retention("vm_images")
        self.assertIsNotNone(vm_retention)
        
        # Test non-existent retention
        invalid_retention = self.loader.get_blob_retention("nonexistent")
        self.assertIsNone(invalid_retention)
    
    def test_matches_pattern_ci_templates(self):
        """Test pattern matching for CI template VMs"""
        # Valid CI template names
        valid_names = [
            "vhds-ci-wat-template-26-1-0.beta-20260213025457",
            "vhds-ci-wat-template-25-2-1.release-20260115103022",
            "vhds-ci-wat-template-24-3-5.rc-20251220143015"
        ]
        
        for name in valid_names:
            result = self.loader.matches_pattern(name, "ci_templates")
            self.assertTrue(result, f"Should match: {name}")
        
        # Invalid names
        invalid_names = [
            "random-vm-name",
            "vhds-prod-api-1.2.3",
            "vhds-ci-wat-template-invalid"
        ]
        
        for name in invalid_names:
            result = self.loader.matches_pattern(name, "ci_templates")
            self.assertFalse(result, f"Should not match: {name}")
    
    def test_matches_pattern_production(self):
        """Test pattern matching for production VMs"""
        # Valid production names
        valid_names = [
            "vhds-prod-api-1.2.3",
            "vhds-prod-web-2.0.1"
        ]
        
        for name in valid_names:
            result = self.loader.matches_pattern(name, "production")
            self.assertTrue(result, f"Should match: {name}")
        
        # Invalid names
        invalid_names = [
            "vhds-ci-wat-template-26-1-0.beta-20260213025457",
            "random-vm-name",
            "vhds-prod-api"
        ]
        
        for name in invalid_names:
            result = self.loader.matches_pattern(name, "production")
            self.assertFalse(result, f"Should not match: {name}")
    
    def test_extract_version_from_ci_template(self):
        """Test version extraction from CI template names"""
        name = "vhds-ci-wat-template-26-1-0.beta-20260213025457"
        version = self.loader.extract_version_from_name(name, "ci_templates")
        
        self.assertIsNotNone(version)
        self.assertIn("26.1.0", version)
        self.assertIn("beta", version)
    
    def test_get_vm_cleanup_config(self):
        """Test getting VM cleanup configuration"""
        cleanup_config = self.loader.get_vm_cleanup_config()
        
        self.assertIsNotNone(cleanup_config)
        self.assertIn("keep_latest_count", cleanup_config)
        self.assertIn("age_threshold_days", cleanup_config)
        self.assertIn("exclude_tags", cleanup_config)
    
    def test_get_storage_accounts(self):
        """Test getting storage account configurations"""
        accounts = self.loader.get_storage_accounts()
        
        self.assertIsNotNone(accounts)
        self.assertIsInstance(accounts, list)
        self.assertGreater(len(accounts), 0)
        
        # Check first account structure
        if accounts:
            account = accounts[0]
            self.assertIn("name", account)
            self.assertIn("containers", account)
    
    def test_get_pipeline_monitoring_config(self):
        """Test getting pipeline monitoring configuration"""
        monitoring_config = self.loader.get_pipeline_monitoring_config()
        
        self.assertIsNotNone(monitoring_config)
        self.assertIn("check_interval_minutes", monitoring_config)
        self.assertIn("monitored_pipelines", monitoring_config)
    
    def test_get_quality_gates(self):
        """Test getting quality gate configurations"""
        gates = self.loader.get_quality_gates()
        
        self.assertIsNotNone(gates)
        self.assertIsInstance(gates, list)
        
        # Check gate structure if any exist
        if gates:
            gate = gates[0]
            self.assertIn("name", gate)
            self.assertIn("threshold", gate)
    
    def test_environment_overrides(self):
        """Test environment-specific configuration overrides"""
        # Create loader with development environment
        dev_loader = ConfigLoader(
            config_dir=str(self.test_config_dir),
            environment="development"
        )
        
        # Load config and check for dev overrides
        config = dev_loader.load_config("azure_resources")
        cleanup = config.get("vm_cleanup", {})
        
        # Development should have more aggressive cleanup (fewer days)
        # Check if environment overrides are applied
        self.assertIn("keep_latest_count", cleanup)
    
    def test_validate_azure_resources_config(self):
        """Test validation of azure_resources configuration"""
        try:
            result = self.loader.validate_config("azure_resources")
            self.assertTrue(result)
        except ConfigurationError as e:
            self.fail(f"Validation failed: {e}")
    
    def test_validate_storage_cleanup_config(self):
        """Test validation of storage_cleanup configuration"""
        try:
            result = self.loader.validate_config("storage_cleanup")
            self.assertTrue(result)
        except ConfigurationError as e:
            self.fail(f"Validation failed: {e}")
    
    def test_validate_build_monitoring_config(self):
        """Test validation of build_monitoring configuration"""
        try:
            result = self.loader.validate_config("build_monitoring")
            self.assertTrue(result)
        except ConfigurationError as e:
            self.fail(f"Validation failed: {e}")
    
    def test_get_all_vm_patterns(self):
        """Test getting all VM patterns"""
        patterns = self.loader.get_all_vm_patterns()
        
        self.assertIsNotNone(patterns)
        self.assertIsInstance(patterns, dict)
        self.assertIn("ci_templates", patterns)
        self.assertIn("production", patterns)
    
    def test_get_all_blob_retention_policies(self):
        """Test getting all blob retention policies"""
        policies = self.loader.get_all_blob_retention_policies()
        
        self.assertIsNotNone(policies)
        self.assertIsInstance(policies, dict)
        self.assertIn("ci_artifacts", policies)
        self.assertIn("vm_images", policies)
    
    def test_get_feature_flag(self):
        """Test getting feature flags"""
        # Test for development environment
        auto_cleanup_enabled = self.loader.get_feature_flag("enable_auto_cleanup")
        self.assertIsInstance(auto_cleanup_enabled, bool)
        
        rag_enabled = self.loader.get_feature_flag("enable_rag")
        self.assertIsInstance(rag_enabled, bool)
    
    def test_nonexistent_config_file(self):
        """Test loading non-existent configuration file"""
        with self.assertRaises(ConfigurationError):
            self.loader.load_config("nonexistent_config")
    
    def test_invalid_config_directory(self):
        """Test initialization with invalid config directory"""
        with self.assertRaises(ConfigurationError):
            ConfigLoader(config_dir="/nonexistent/path")
    
    def test_reload_all(self):
        """Test reloading all configurations"""
        # Load some configs
        self.loader.load_config("azure_resources")
        self.loader.load_config("storage_cleanup")
        
        # Check cache is populated
        self.assertGreater(len(self.loader._configs), 0)
        
        # Reload all
        self.loader.reload_all()
        
        # Cache should be cleared
        self.assertEqual(len(self.loader._configs), 0)


class TestConfigLoaderWithTempFiles(unittest.TestCase):
    """Test ConfigLoader with temporary configuration files"""
    
    def setUp(self):
        """Create temporary config directory and files"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        
        # Create test configuration
        test_config = {
            "test_section": {
                "value": "test",
                "number": 42
            }
        }
        
        config_file = self.config_dir / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(test_config, f)
        
        # Create environments.yaml
        env_config = {
            "development": {
                "test_section": {
                    "number": 100
                }
            }
        }
        
        env_file = self.config_dir / "environments.yaml"
        with open(env_file, 'w') as f:
            yaml.dump(env_config, f)
        
        self.loader = ConfigLoader(
            config_dir=str(self.config_dir),
            environment="development"
        )
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_environment_override_applied(self):
        """Test that environment overrides are properly applied"""
        config = self.loader.load_config("test_config")
        
        # Original value
        self.assertEqual(config["test_section"]["value"], "test")
        
        # Overridden value from development environment
        self.assertEqual(config["test_section"]["number"], 100)
    
    def test_env_var_expansion(self):
        """Test environment variable expansion in config"""
        # Set test environment variable
        os.environ["TEST_VAR"] = "expanded_value"
        
        # Create config with env var reference
        test_config = {
            "setting": "${TEST_VAR}"
        }
        
        config_file = self.config_dir / "env_test.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(test_config, f)
        
        loader = ConfigLoader(config_dir=str(self.config_dir))
        config = loader.load_config("env_test")
        
        self.assertEqual(config["setting"], "expanded_value")
        
        # Clean up
        del os.environ["TEST_VAR"]


class TestPatternMatching(unittest.TestCase):
    """Focused tests for pattern matching functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        config_dir = Path(__file__).parent.parent / "config"
        self.loader = ConfigLoader(config_dir=str(config_dir))
    
    def test_ci_template_pattern_variations(self):
        """Test various CI template naming variations"""
        test_cases = [
            # (name, should_match)
            ("vhds-ci-wat-template-26-1-0.beta-20260213025457", True),
            ("vhds-ci-wat-template-1-0-0.release-19700101000000", True),
            ("vhds-ci-wat-template-99-99-99.rc-99991231235959", True),
            ("vhds-ci-wat-template-26-1-0.invalid-20260213025457", False),
            ("vhds-ci-wat-template-26.1.0.beta-20260213025457", False),
            ("vhds-ci-wat-template-26-1-0.beta", False),
            ("vhds-ci-template-26-1-0.beta-20260213025457", False),
        ]
        
        for name, should_match in test_cases:
            result = self.loader.matches_pattern(name, "ci_templates")
            self.assertEqual(
                result,
                should_match,
                f"Pattern match failed for: {name} (expected {should_match}, got {result})"
            )


if __name__ == "__main__":
    unittest.main()
