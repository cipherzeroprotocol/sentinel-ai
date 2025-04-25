"""
Address classification model for detecting wallet types
"""
import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
import joblib
import os
import sys
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data.config import MODEL_DIR

logger = logging.getLogger(__name__)

# Define model file path
MODEL_FILE = os.path.join(MODEL_DIR, "address_classifier.joblib")

class AddressClassifier:
    """
    Address classification model for identifying wallet types
    """
    
    # Address classification types
    WALLET_TYPES = {
        "exchange": 0,
        "mixer": 1,
        "whale": 2,
        "mule": 3,
        "team": 4,
        "normal": 5
    }
    
    WALLET_TYPE_NAMES = {v: k for k, v in WALLET_TYPES.items()}
    
    def __init__(self):
        self.model = None
        self.load_model()
    
    def load_model(self):
        """
        Load the model from disk if it exists
        """
        if os.path.exists(MODEL_FILE):
            try:
                self.model = joblib.load(MODEL_FILE)
                logger.info(f"Loaded address classifier model from {MODEL_FILE}")
                return True
            except Exception as e:
                logger.error(f"Error loading model: {str(e)}")
        
        # If model doesn't exist or error loading, create a new one
        self.model = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
        ])
        
        logger.info("Created new address classifier model")
        return False
    
    def save_model(self):
        """
        Save the model to disk
        """
        try:
            os.makedirs(os.path.dirname(MODEL_FILE), exist_ok=True)
            joblib.dump(self.model, MODEL_FILE)
            logger.info(f"Saved address classifier model to {MODEL_FILE}")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            return False
    
    def extract_features(self, transactions, address):
        """
        Extract features from transaction data for a given address
        
        Args:
            transactions (list): List of transactions
            address (str): Address to extract features for
            
        Returns:
            dict: Dictionary of extracted features
        """
        if not transactions:
            logger.warning(f"No transactions provided for address {address}")
            return self._get_default_features()
        
        try:
            # Create dataframe
            df = pd.DataFrame(transactions)
            
            # Transaction count features
            total_count = len(df)
            
            # Extract block times
            if 'block_time' in df.columns:
                df['datetime'] = pd.to_datetime(df['block_time'])
            elif 'blockTime' in df.columns:
                df['datetime'] = pd.to_datetime(df['blockTime'], unit='s')
            else:
                df['datetime'] = pd.to_datetime('now')
            
            # Sort by time
            df = df.sort_values('datetime')
            
            # Calculate time features
            if len(df) > 1:
                time_range = (df['datetime'].max() - df['datetime'].min()).total_seconds() / 86400  # days
                avg_interval = time_range / (len(df) - 1) if len(df) > 1 else 0
            else:
                time_range = 0
                avg_interval = 0
            
            # Calculate activity features
            if time_range > 0:
                activity_density = total_count / time_range
            else:
                activity_density = 0
            
            # Calculate value features
            if 'amount' in df.columns:
                total_value = df['amount'].sum()
                avg_value = df['amount'].mean()
                max_value = df['amount'].max()
                value_std = df['amount'].std()
            elif 'amount_usd' in df.columns:
                total_value = df['amount_usd'].sum()
                avg_value = df['amount_usd'].mean()
                max_value = df['amount_usd'].max()
                value_std = df['amount_usd'].std()
            else:
                total_value = 0
                avg_value = 0
                max_value = 0
                value_std = 0
            
            # Calculate interaction features
            counterparties = set()
            
            # Extract counterparty addresses
            for tx in transactions:
                if 'sender' in tx and 'wallet' in tx['sender'] and tx['sender']['wallet'] != address:
                    counterparties.add(tx['sender']['wallet'])
                
                if 'receiver' in tx and 'wallet' in tx['receiver'] and tx['receiver']['wallet'] != address:
                    counterparties.add(tx['receiver']['wallet'])
                
                # Extract from recipients if present
                if 'recipients' in tx:
                    for recipient in tx['recipients']:
                        if 'address' in recipient and recipient['address'] != address:
                            counterparties.add(recipient['address'])
            
            unique_counterparties = len(counterparties)
            
            # Calculate counterparty features
            if total_count > 0:
                counterparty_ratio = unique_counterparties / total_count
            else:
                counterparty_ratio = 0
            
            # Extract program features
            programs = set()
            for tx in transactions:
                if 'program_id' in tx:
                    programs.add(tx['program_id'])
                elif 'program' in tx and 'id' in tx['program']:
                    programs.add(tx['program']['id'])
            
            unique_programs = len(programs)
            
            # Calculate recency features
            now = datetime.now()
            recent_txs = df[df['datetime'] > (now - timedelta(days=7))]
            recent_count = len(recent_txs)
            
            # Calculate regularity features
            if len(df) > 1:
                # Calculate time intervals between transactions
                intervals = np.diff(df['datetime'].astype(int)) / 1e9  # Convert to seconds
                interval_std = np.std(intervals)
                
                # Calculate regularity (lower std = more regular)
                if np.mean(intervals) > 0:
                    regularity = 1 / (interval_std / np.mean(intervals) + 1)
                else:
                    regularity = 0
            else:
                regularity = 0
            
            features = {
                'total_count': total_count,
                'time_range_days': time_range,
                'avg_interval_days': avg_interval,
                'activity_density': activity_density,
                'total_value': total_value,
                'avg_value': avg_value,
                'max_value': max_value,
                'value_std': value_std,
                'unique_counterparties': unique_counterparties,
                'counterparty_ratio': counterparty_ratio,
                'unique_programs': unique_programs,
                'recent_count_7d': recent_count,
                'regularity': regularity
            }
            
            return features
        
        except Exception as e:
            logger.error(f"Error extracting features: {str(e)}")
            return self._get_default_features()
    
    def _get_default_features(self):
        """
        Return default features when extraction fails
        """
        return {
            'total_count': 0,
            'time_range_days': 0,
            'avg_interval_days': 0,
            'activity_density': 0,
            'total_value': 0,
            'avg_value': 0,
            'max_value': 0,
            'value_std': 0,
            'unique_counterparties': 0,
            'counterparty_ratio': 0,
            'unique_programs': 0,
            'recent_count_7d': 0,
            'regularity': 0
        }
    
    def predict(self, transactions, address):
        """
        Predict the type of wallet based on transaction data
        
        Args:
            transactions (list): List of transactions
            address (str): Address to classify
            
        Returns:
            dict: Classification results
        """
        # Extract features
        features = self.extract_features(transactions, address)
        
        # Handle case where model is not trained
        if not self.is_trained():
            # Define simple rule-based classification
            return self._rule_based_classification(features)
        
        # Convert features to array
        X = np.array([list(features.values())])
        
        # Make prediction
        prediction = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        
        # Get top classes and probabilities
        top_classes = np.argsort(probabilities)[::-1]
        top_probabilities = probabilities[top_classes]
        
        # Format results
        results = {
            'predicted_class': self.WALLET_TYPE_NAMES[prediction],
            'confidence': float(probabilities[prediction]),
            'top_classes': [
                {
                    'class': self.WALLET_TYPE_NAMES[cls],
                    'probability': float(prob)
                }
                for cls, prob in zip(top_classes[:3], top_probabilities[:3])
            ],
            'features': features
        }
        
        return results
    
    def _rule_based_classification(self, features):
        """
        Simple rule-based classification when model is not trained
        
        Args:
            features (dict): Extracted features
            
        Returns:
            dict: Classification results
        """
        # Define simple rules
        if features['total_count'] > 1000 and features['unique_counterparties'] > 100:
            wallet_type = 'exchange'
            confidence = 0.7
        elif features['activity_density'] > 10 and features['counterparty_ratio'] < 0.1:
            wallet_type = 'mixer'
            confidence = 0.6
        elif features['max_value'] > 100000:
            wallet_type = 'whale'
            confidence = 0.6
        elif features['total_count'] < 10 and features['time_range_days'] < 7:
            wallet_type = 'mule'
            confidence = 0.5
        else:
            wallet_type = 'normal'
            confidence = 0.5
        
        # Format results
        results = {
            'predicted_class': wallet_type,
            'confidence': confidence,
            'top_classes': [
                {
                    'class': wallet_type,
                    'probability': confidence
                }
            ],
            'features': features,
            'method': 'rule-based'  # Indicate this is a rule-based classification
        }
        
        return results
    
    def train(self, training_data):
        """
        Train the model with labeled data
        
        Args:
            training_data (list): List of dictionaries with 'features' and 'label' keys
            
        Returns:
            float: Model accuracy
        """
        if not training_data:
            logger.error("No training data provided")
            return 0.0
        
        try:
            # Extract features and labels
            X = []
            y = []
            
            for item in training_data:
                if 'features' in item and 'label' in item:
                    X.append(list(item['features'].values()))
                    y.append(self.WALLET_TYPES.get(item['label'], self.WALLET_TYPES['normal']))
            
            # Convert to numpy arrays
            X = np.array(X)
            y = np.array(y)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Train model
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            accuracy = self.model.score(X_test, y_test)
            
            # Save model
            self.save_model()
            
            logger.info(f"Trained address classifier model with accuracy: {accuracy:.4f}")
            
            return accuracy
        
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return 0.0
    
    def is_trained(self):
        """
        Check if the model is trained
        
        Returns:
            bool: True if model is trained, False otherwise
        """
        if self.model is None:
            return False
        
        if not hasattr(self.model, 'predict_proba'):
            return False
        
        # Check if classifier is fitted
        clf = self.model.named_steps.get('classifier')
        if clf is None:
            return False
        
        return hasattr(clf, 'classes_')

if __name__ == "__main__":
    # For testing
    logging.basicConfig(level=logging.INFO)
    
    # Create model
    model = AddressClassifier()
    
    # Test prediction with sample data
    sample_transactions = [
        {
            "signature": "4rLWBzM7XQu42u3UwTyjvMdZ6caRZtQJDKHdf5TdF9ymGdxVEohHdnD3YzgcXSBP8HLfBnb9BppNH6JGPLAMJnNa",
            "block_time": "2023-05-01T12:00:00",
            "amount": 1000,
            "sender": {"wallet": "sender_address"},
            "receiver": {"wallet": "receiver_address"}
        },
        {
            "signature": "5mVd8CmQ7NnVj4EVbD4NUwnjmYDgCkm2bGEpL5xQdKW8cYr7vzkk87Qa5Go8PdPWMmY3Gdrd1G32xVDGzaMVfR82",
            "block_time": "2023-05-02T12:00:00",
            "amount": 2000,
            "sender": {"wallet": "sender_address"},
            "receiver": {"wallet": "receiver_address2"}
        }
    ]
    
    result = model.predict(sample_transactions, "test_address")
    print(f"Prediction: {result['predicted_class']} with confidence {result['confidence']:.4f}")
    print(f"Features: {result['features']}")