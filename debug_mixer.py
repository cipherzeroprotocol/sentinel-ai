"""
Debug script to verify MixerDetector implementation
"""
import logging
import sys
import inspect
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def check_mixer_detector():
    """Check if MixerDetector is correctly implemented with days parameter"""
    try:
        # Force reload the module
        import importlib
        if 'sentinel.analysis.bounties.mixer_detector' in sys.modules:
            logger.info("Removing mixer_detector from sys.modules to force reload")
            del sys.modules['sentinel.analysis.bounties.mixer_detector']
        
        # Import the module
        from sentinel.analysis.bounties.mixer_detector import MixerDetector
        
        # Check the signature of analyze method
        sig = inspect.signature(MixerDetector.analyze)
        
        logger.info(f"MixerDetector.analyze() signature: {sig}")
        
        if 'days' in sig.parameters:
            logger.info("SUCCESS: MixerDetector.analyze() accepts 'days' parameter")
            return True
        else:
            logger.error("FAILURE: MixerDetector.analyze() does not accept 'days' parameter")
            return False
    
    except Exception as e:
        logger.error(f"Error checking MixerDetector: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting MixerDetector verification...")
    result = check_mixer_detector()
    
    if result:
        logger.info("Verification successful - MixerDetector is correctly implemented")
        # Create a test instance and verify
        try:
            from sentinel.analysis.bounties.mixer_detector import MixerDetector
            detector = MixerDetector()
            # Test with a dummy address
            test_address = "test_address"
            logger.info(f"Testing MixerDetector.analyze('{test_address}', days=30)...")
            # This should not raise a TypeError if implemented correctly
            detector.analyze(test_address, days=30)
            logger.info("Test passed - analyze() accepts days parameter")
        except Exception as e:
            logger.error(f"Test failed: {e}")
    else:
        logger.error("Verification failed - MixerDetector needs to be fixed")
    
    logger.info("Verification complete")
