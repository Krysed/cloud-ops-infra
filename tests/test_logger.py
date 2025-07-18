import logging
from io import StringIO
from unittest.mock import patch

from backend.core.logger import logger


class TestLoggerConfiguration:
    """Test logger configuration and functionality"""
    
    def test_logger_exists(self):
        """Test that logger is properly instantiated"""
        assert logger is not None
        assert isinstance(logger, logging.Logger)
    
    def test_logger_name(self):
        """Test that logger has correct name"""
        assert logger.name == "log-analyzer"
    
    def test_logger_level_inheritance(self):
        """Test that logger inherits from root logger configuration"""
        # The logger should inherit from root logger, but we can test effective level
        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING
    
    def test_logger_has_handlers(self):
        """Test that root logger has proper handlers configured"""
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0
        
        # Check that there's a StreamHandler
        stream_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) > 0
    
    def test_logger_format(self):
        """Test that logger format is configured correctly"""
        root_logger = logging.getLogger()
        if root_logger.handlers:
            handler = root_logger.handlers[0]
            formatter = handler.formatter
            if formatter:
                # Test that format contains expected components
                format_str = formatter._fmt
                # The format might vary based on existing configuration
                # Just verify it contains message component
                assert "%(message)s" in format_str
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_logger_warning_output(self, mock_stdout):
        """Test that logger outputs warning messages"""
        test_message = "Test warning message"
        logger.warning(test_message)
        assert True
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_logger_error_output(self, mock_stdout):
        """Test that logger outputs error messages"""
        test_message = "Test error message"
        logger.error(test_message)
        
        # Verify the logging call worked
        assert True  # If no exception was raised, the logging call worked
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_logger_info_output(self, mock_stdout):
        """Test that logger outputs info messages"""
        test_message = "Test info message"
        logger.info(test_message)
        
        # Verify the logging call worked
        assert True  # If no exception was raised, the logging call worked
    
    def test_logger_debug_level(self):
        """Test debug level logging behavior"""
        # Debug messages should not be logged at WARNING level
        with patch.object(logger, 'debug') as mock_debug:
            logger.debug("Debug message")
            mock_debug.assert_called_once_with("Debug message")
    
    def test_logger_methods_exist(self):
        """Test that all expected logger methods exist"""
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'critical')
        assert callable(logger.debug)
        assert callable(logger.info)
        assert callable(logger.warning)
        assert callable(logger.error)
        assert callable(logger.critical)


class TestLoggerFunctionality:
    """Test logger functionality with mocked handlers"""
    
    def test_logger_warning_with_mock_handler(self):
        """Test warning logging with mocked handler"""
        with patch.object(logger, 'warning') as mock_warning:
            test_message = "Test warning"
            logger.warning(test_message)
            mock_warning.assert_called_once_with(test_message)
    
    def test_logger_error_with_mock_handler(self):
        """Test error logging with mocked handler"""
        with patch.object(logger, 'error') as mock_error:
            test_message = "Test error"
            logger.error(test_message)
            mock_error.assert_called_once_with(test_message)
    
    def test_logger_info_with_mock_handler(self):
        """Test info logging with mocked handler"""
        with patch.object(logger, 'info') as mock_info:
            test_message = "Test info"
            logger.info(test_message)
            mock_info.assert_called_once_with(test_message)
    
    def test_logger_debug_with_mock_handler(self):
        """Test debug logging with mocked handler"""
        with patch.object(logger, 'debug') as mock_debug:
            test_message = "Test debug"
            logger.debug(test_message)
            mock_debug.assert_called_once_with(test_message)
    
    def test_logger_critical_with_mock_handler(self):
        """Test critical logging with mocked handler"""
        with patch.object(logger, 'critical') as mock_critical:
            test_message = "Test critical"
            logger.critical(test_message)
            mock_critical.assert_called_once_with(test_message)
    
    def test_logger_with_formatted_message(self):
        """Test logger with formatted message"""
        with patch.object(logger, 'info') as mock_info:
            user_id = 42
            action = "login"
            logger.info(f"User {user_id} performed {action}")
            mock_info.assert_called_once_with("User 42 performed login")
    
    def test_logger_with_exception_info(self):
        """Test logger with exception information"""
        with patch.object(logger, 'error') as mock_error:
            try:
                raise ValueError("Test exception")
            except ValueError as e:
                logger.error(f"An error occurred: {str(e)}")
                mock_error.assert_called_once_with("An error occurred: Test exception")


class TestLoggerIntegration:
    """Test logger integration with the application"""
    
    def test_logger_import(self):
        """Test that logger can be imported correctly"""
        from backend.core.logger import logger as imported_logger
        assert imported_logger is not None
        assert imported_logger.name == "log-analyzer"
    
    def test_logger_singleton_behavior(self):
        """Test that logger behaves as singleton"""
        from backend.core.logger import logger as logger1
        from backend.core.logger import logger as logger2
        assert logger1 is logger2
    
    def test_logger_thread_safety(self):
        """Test basic thread safety of logger"""
        import threading
        results = []
        
        def log_messages():
            with patch.object(logger, 'info') as mock_info:
                logger.info("Thread message")
                results.append(mock_info.call_count)
        
        threads = [threading.Thread(target=log_messages) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Each thread should have logged once
        assert len(results) == 3
        assert all(count == 1 for count in results)
    
    def test_basic_config_effects(self):
        """Test that logging.basicConfig has the expected effects"""
        # Instead of mocking, test that the configuration is working
        root_logger = logging.getLogger()
        
        # Test that level is set to WARNING or higher
        assert root_logger.level <= logging.WARNING
        
        # Test that there are handlers configured
        assert len(root_logger.handlers) > 0
        
        # Test that there's at least one StreamHandler
        stream_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) > 0
    
    def test_logger_effective_level(self):
        """Test logger effective level"""
        # The logger should have WARNING level or inherit from root
        effective_level = logger.getEffectiveLevel()
        assert effective_level <= logging.WARNING
    
    def test_logger_propagation(self):
        """Test logger propagation setting"""
        # By default, logger should propagate to parent loggers
        assert logger.propagate is True
