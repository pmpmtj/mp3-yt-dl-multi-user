"""
run_all_tests.py

Main test runner for all database tests.
Runs comprehensive database tests including connection, operations, and utilities.

This script follows the project's architecture guidelines:
- Uses centralized logging from /src/common/logging_config.py
- Uses path utilities from /path_utils/path_utils.py
- Handles both frozen (PyInstaller) and regular Python execution
- Self-contained module with proper error handling
- Production-minded development approach
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to Python path for imports
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from src.common.logging_config import setup_logging, get_logger
from path_utils.path_utils import get_script_directories, resolve_path
from .test_database_connection import DatabaseConnectionTester
from .test_database_operations import DatabaseOperationsTester


class DatabaseTestRunner:
    """
    Database test runner.
    
    Runs all database tests and provides comprehensive reporting.
    """
    
    def __init__(self):
        """Initialize the database test runner."""
        # Setup logging
        setup_logging(debug_mode=True)
        self.logger = get_logger('db_test_runner')
        
        # Get script directories
        self.script_dir, self.base_dir = get_script_directories()
        self.logger.debug(f"Script directories: SCRIPT_DIR={self.script_dir}, BASE_DIR={self.base_dir}")
        
        # Test results
        self.test_results = []
        
        self.logger.info("DatabaseTestRunner initialized")
    
    def run_connection_test(self) -> bool:
        """
        Run database connection test.
        
        Returns:
            bool: True if test passed, False otherwise
        """
        self.logger.info("Running database connection test...")
        
        try:
            tester = DatabaseConnectionTester()
            success = tester.run_comprehensive_test()
            tester.cleanup()
            
            self.test_results.append({
                'test_name': 'Database Connection Test',
                'success': success,
                'description': 'Tests database connectivity and basic operations'
            })
            
            return success
            
        except Exception as e:
            self.logger.error(f"Connection test failed with exception: {e}")
            self.test_results.append({
                'test_name': 'Database Connection Test',
                'success': False,
                'description': 'Tests database connectivity and basic operations',
                'error': str(e)
            })
            return False
    
    def run_operations_test(self) -> bool:
        """
        Run database operations test.
        
        Returns:
            bool: True if test passed, False otherwise
        """
        self.logger.info("Running database operations test...")
        
        try:
            tester = DatabaseOperationsTester()
            success = tester.run_comprehensive_test()
            tester.cleanup()
            
            self.test_results.append({
                'test_name': 'Database Operations Test',
                'success': success,
                'description': 'Tests CRUD operations, models, migrations, and utilities'
            })
            
            return success
            
        except Exception as e:
            self.logger.error(f"Operations test failed with exception: {e}")
            self.test_results.append({
                'test_name': 'Database Operations Test',
                'success': False,
                'description': 'Tests CRUD operations, models, migrations, and utilities',
                'error': str(e)
            })
            return False
    
    def run_all_tests(self) -> bool:
        """
        Run all database tests.
        
        Returns:
            bool: True if all tests passed, False otherwise
        """
        self.logger.info("=== Starting All Database Tests ===")
        
        # Run connection test
        connection_success = self.run_connection_test()
        
        # Run operations test
        operations_success = self.run_operations_test()
        
        # Calculate overall success
        overall_success = connection_success and operations_success
        
        # Generate report
        self.generate_report()
        
        if overall_success:
            self.logger.info("=== All Database Tests Completed Successfully ===")
        else:
            self.logger.error("=== Some Database Tests Failed ===")
        
        return overall_success
    
    def generate_report(self):
        """Generate test report."""
        self.logger.info("=== Database Test Report ===")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        self.logger.info(f"Total Tests: {total_tests}")
        self.logger.info(f"Passed: {passed_tests}")
        self.logger.info(f"Failed: {failed_tests}")
        self.logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        self.logger.info("\nTest Details:")
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            self.logger.info(f"{status} - {result['test_name']}")
            self.logger.info(f"    Description: {result['description']}")
            if not result['success'] and 'error' in result:
                self.logger.error(f"    Error: {result['error']}")
        
        self.logger.info("=== End Database Test Report ===")
    
    def print_summary(self):
        """Print test summary to console."""
        print("\n" + "="*60)
        print("DATABASE TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nTest Results:")
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test_name']}")
            if not result['success'] and 'error' in result:
                print(f"    Error: {result['error']}")
        
        print("="*60)
        
        if failed_tests == 0:
            print("\n🎉 All database tests passed! Database is fully functional.")
        else:
            print(f"\n⚠️  {failed_tests} test(s) failed. Check the logs for details.")


def main():
    """Main function to run all database tests."""
    print("PostgreSQL Database Test Suite")
    print("=" * 40)
    
    runner = DatabaseTestRunner()
    
    try:
        success = runner.run_all_tests()
        runner.print_summary()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
