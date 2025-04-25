"""
Database access layer for address and transaction data
"""
import json
import logging
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import pandas as pd
import numpy as np

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data.config import DATABASE_URL

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Address(Base):
    """
    Address model for storing blockchain addresses
    """
    __tablename__ = 'addresses'
    
    id = Column(Integer, primary_key=True)
    address = Column(String(64), unique=True, nullable=False, index=True)
    network = Column(String(16), nullable=False, default='solana')
    entity_name = Column(String(64), nullable=True)
    entity_type = Column(String(32), nullable=True)
    labels = Column(String(256), nullable=True)  # Comma-separated labels
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    risk_score = Column(Float, nullable=True)
    risk_level = Column(String(16), nullable=True)
    risk_factors = Column(Text, nullable=True)  # JSON string
    is_contract = Column(Boolean, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="address")
    counterparties = relationship("Counterparty", back_populates="address")
    tokens = relationship("Token", secondary="address_tokens")
    
    def __repr__(self):
        return f"<Address(address='{self.address}', network='{self.network}')>"

class Transaction(Base):
    """
    Transaction model for storing blockchain transactions
    """
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    hash = Column(String(128), unique=True, nullable=False, index=True)
    address_id = Column(Integer, ForeignKey('addresses.id'), nullable=False)
    block_number = Column(Integer, nullable=True)
    block_time = Column(DateTime, nullable=True)
    success = Column(Boolean, nullable=True)
    value = Column(Float, nullable=True)
    value_usd = Column(Float, nullable=True)
    fee = Column(Float, nullable=True)
    program_id = Column(String(64), nullable=True)
    instruction_name = Column(String(64), nullable=True)
    data = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    # Relationships
    address = relationship("Address", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(hash='{self.hash}')>"

class Counterparty(Base):
    """
    Counterparty model for storing address counterparties
    """
    __tablename__ = 'counterparties'
    
    id = Column(Integer, primary_key=True)
    address_id = Column(Integer, ForeignKey('addresses.id'), nullable=False)
    counterparty_address = Column(String(64), nullable=False, index=True)
    interaction_count = Column(Integer, nullable=True)
    sent_volume = Column(Float, nullable=True)
    received_volume = Column(Float, nullable=True)
    first_interaction = Column(DateTime, nullable=True)
    last_interaction = Column(DateTime, nullable=True)
    entity_name = Column(String(64), nullable=True)
    entity_type = Column(String(32), nullable=True)
    labels = Column(String(256), nullable=True)  # Comma-separated labels
    risk_score = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    # Relationships
    address = relationship("Address", back_populates="counterparties")
    
    def __repr__(self):
        return f"<Counterparty(address_id={self.address_id}, counterparty_address='{self.counterparty_address}')>"

class Token(Base):
    """
    Token model for storing token information
    """
    __tablename__ = 'tokens'
    
    id = Column(Integer, primary_key=True)
    mint = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=True)
    symbol = Column(String(32), nullable=True)
    decimals = Column(Integer, nullable=True)
    supply = Column(Float, nullable=True)
    price_usd = Column(Float, nullable=True)
    market_cap = Column(Float, nullable=True)
    creator = Column(String(64), nullable=True)
    mint_authority = Column(String(64), nullable=True)
    freeze_authority = Column(String(64), nullable=True)
    is_nft = Column(Boolean, nullable=True)
    risk_score = Column(Float, nullable=True)
    risk_level = Column(String(16), nullable=True)
    risk_factors = Column(Text, nullable=True)  # JSON string
    metadata_json = Column(Text, nullable=True)  # Renamed from metadata
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Token(mint='{self.mint}', symbol='{self.symbol}')>"

class AddressToken(Base):
    """
    Many-to-many relationship between addresses and tokens
    """
    __tablename__ = 'address_tokens'
    
    id = Column(Integer, primary_key=True)
    address_id = Column(Integer, ForeignKey('addresses.id'), nullable=False)
    token_id = Column(Integer, ForeignKey('tokens.id'), nullable=False)
    balance = Column(Float, nullable=True)
    balance_usd = Column(Float, nullable=True)
    last_updated = Column(DateTime, nullable=False, default=datetime.now)
    
    def __repr__(self):
        return f"<AddressToken(address_id={self.address_id}, token_id={self.token_id})>"

class Program(Base):
    """
    Program model for storing program information
    """
    __tablename__ = 'programs'
    
    id = Column(Integer, primary_key=True)
    program_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)
    website = Column(String(256), nullable=True)
    twitter = Column(String(256), nullable=True)
    github = Column(String(256), nullable=True)
    verified = Column(Boolean, nullable=True)
    metadata_json = Column(Text, nullable=True)  # Renamed from metadata
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Program(program_id='{self.program_id}', name='{self.name}')>"

# Initialize database
def init_db():
    """
    Initialize the database schema
    """
    Base.metadata.create_all(engine)
    logger.info("Database initialized")

def save_address_data(address, data):
    """
    Save address data to the database
    
    Args:
        address (str): Address to save data for
        data (dict): Address data
    """
    session = Session()
    try:
        # Check if address exists
        db_address = session.query(Address).filter(Address.address == address).first()
        
        if not db_address:
            # Create new address
            db_address = Address(address=address, network='solana')
            session.add(db_address)
        
        # Update address data
        if 'entity_name' in data:
            db_address.entity_name = data['entity_name']
        
        if 'entity_type' in data:
            db_address.entity_type = data['entity_type']
        
        if 'labels' in data:
            if isinstance(data['labels'], list):
                db_address.labels = ','.join(data['labels'])
            else:
                db_address.labels = data['labels']
        
        if 'first_seen' in data:
            db_address.first_seen = data['first_seen']
        
        if 'last_seen' in data:
            db_address.last_seen = data['last_seen']
        
        if 'is_contract' in data:
            db_address.is_contract = data['is_contract']
        
        db_address.updated_at = datetime.now()
        
        session.commit()
        logger.info(f"Saved address data for {address}")
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving address data for {address}: {str(e)}")
    
    finally:
        session.close()

def save_transactions(address, transactions):
    """
    Save transactions to the database
    
    Args:
        address (str): Address the transactions belong to
        transactions (list): List of transaction data
    """
    if not transactions:
        logger.warning(f"No transactions to save for {address}")
        return
    
    session = Session()
    try:
        # Get address ID
        db_address = session.query(Address).filter(Address.address == address).first()
        
        if not db_address:
            # Create new address
            db_address = Address(address=address, network='solana')
            session.add(db_address)
            session.commit()
        
        # Save transactions
        for tx_data in transactions:
            tx_hash = None
            if 'signature' in tx_data:
                tx_hash = tx_data['signature']
            elif 'signatures' in tx_data and tx_data['signatures']:
                tx_hash = tx_data['signatures'][0]
            
            if not tx_hash:
                logger.warning(f"Transaction has no hash, skipping: {tx_data}")
                continue
            
            # Check if transaction exists
            tx = session.query(Transaction).filter(Transaction.hash == tx_hash).first()
            
            if not tx:
                # Create new transaction
                tx = Transaction(hash=tx_hash, address_id=db_address.id)
                session.add(tx)
            
            # Update transaction data
            if 'blockTime' in tx_data:
                tx.block_time = datetime.fromtimestamp(tx_data['blockTime'])
            
            if 'slot' in tx_data:
                tx.block_number = tx_data['slot']
            
            if 'meta' in tx_data and 'err' in tx_data['meta']:
                tx.success = tx_data['meta']['err'] is None
            
            if 'meta' in tx_data and 'fee' in tx_data['meta']:
                tx.fee = tx_data['meta']['fee']
            
            # Parse program ID and instruction name
            if 'transaction' in tx_data and 'message' in tx_data['transaction'] and 'instructions' in tx_data['transaction']['message']:
                instructions = tx_data['transaction']['message']['instructions']
                if instructions:
                    if 'programId' in instructions[0]:
                        tx.program_id = instructions[0]['programId']
                    
                    if 'parsed' in instructions[0] and 'type' in instructions[0]['parsed']:
                        tx.instruction_name = instructions[0]['parsed']['type']
            
            # Save full transaction data as JSON
            tx.data = json.dumps(tx_data)
            
        session.commit()
        logger.info(f"Saved {len(transactions)} transactions for {address}")
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving transactions for {address}: {str(e)}")
    
    finally:
        session.close()

def save_risk_data(address, risk_data):
    """
    Save risk data for an address
    
    Args:
        address (str): Address to save risk data for
        risk_data (dict): Risk data
    """
    if not risk_data:
        logger.warning(f"No risk data to save for {address}")
        return
    
    session = Session()
    try:
        # Get address
        db_address = session.query(Address).filter(Address.address == address).first()
        
        if not db_address:
            # Create new address
            db_address = Address(address=address, network='solana')
            session.add(db_address)
        
        # Update risk data
        if 'risk_score' in risk_data:
            db_address.risk_score = risk_data['risk_score']
        
        if 'risk_level' in risk_data:
            db_address.risk_level = risk_data['risk_level']
        
        if 'risk_factors' in risk_data:
            db_address.risk_factors = json.dumps(risk_data['risk_factors'])
        
        db_address.updated_at = datetime.now()
        
        session.commit()
        logger.info(f"Saved risk data for {address}")
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving risk data for {address}: {str(e)}")
    
    finally:
        session.close()

def save_counterparties(address, counterparties):
    """
    Save counterparties for an address
    
    Args:
        address (str): Address the counterparties belong to
        counterparties (list): List of counterparty data
    """
    if not counterparties:
        logger.warning(f"No counterparties to save for {address}")
        return
    
    session = Session()
    try:
        # Get address ID
        db_address = session.query(Address).filter(Address.address == address).first()
        
        if not db_address:
            # Create new address
            db_address = Address(address=address, network='solana')
            session.add(db_address)
            session.commit()
        
        # Save counterparties
        for cp_data in counterparties:
            cp_address = cp_data.get('address')
            
            if not cp_address:
                logger.warning(f"Counterparty has no address, skipping: {cp_data}")
                continue
            
            # Check if counterparty exists
            cp = session.query(Counterparty).filter(
                Counterparty.address_id == db_address.id,
                Counterparty.counterparty_address == cp_address
            ).first()
            
            if not cp:
                # Create new counterparty
                cp = Counterparty(
                    address_id=db_address.id,
                    counterparty_address=cp_address
                )
                session.add(cp)
            
            # Update counterparty data
            if 'interaction_count' in cp_data:
                cp.interaction_count = cp_data['interaction_count']
            
            if 'sent_volume_usd' in cp_data:
                cp.sent_volume = cp_data['sent_volume_usd']
            
            if 'received_volume_usd' in cp_data:
                cp.received_volume = cp_data['received_volume_usd']
            
            if 'first_interaction' in cp_data:
                if isinstance(cp_data['first_interaction'], int):
                    cp.first_interaction = datetime.fromtimestamp(cp_data['first_interaction'])
                else:
                    cp.first_interaction = cp_data['first_interaction']
            
            if 'last_interaction' in cp_data:
                if isinstance(cp_data['last_interaction'], int):
                    cp.last_interaction = datetime.fromtimestamp(cp_data['last_interaction'])
                else:
                    cp.last_interaction = cp_data['last_interaction']
            
            if 'entity' in cp_data and 'name' in cp_data['entity']:
                cp.entity_name = cp_data['entity']['name']
            
            if 'entity' in cp_data and 'category' in cp_data['entity']:
                cp.entity_type = cp_data['entity']['category']
            
            if 'labels' in cp_data:
                if isinstance(cp_data['labels'], list):
                    cp.labels = ','.join(cp_data['labels'])
                else:
                    cp.labels = cp_data['labels']
            
            if 'risk_score' in cp_data:
                cp.risk_score = cp_data['risk_score']
        
        session.commit()
        logger.info(f"Saved {len(counterparties)} counterparties for {address}")
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving counterparties for {address}: {str(e)}")
    
    finally:
        session.close()

def save_token_data(mint, token_data):
    """
    Save token data to the database
    
    Args:
        mint (str): Token mint address
        token_data (dict): Token data
    """
    if not token_data:
        logger.warning(f"No token data to save for {mint}")
        return
    
    session = Session()
    try:
        # Check if token exists
        token = session.query(Token).filter(Token.mint == mint).first()
        
        if not token:
            # Create new token
            token = Token(mint=mint)
            session.add(token)
        
        # Update token data
        if 'name' in token_data:
            token.name = token_data['name']
        
        if 'symbol' in token_data:
            token.symbol = token_data['symbol']
        
        if 'decimals' in token_data:
            token.decimals = token_data['decimals']
        
        if 'supply' in token_data:
            token.supply = token_data['supply']
        
        if 'price_usd' in token_data:
            token.price_usd = token_data['price_usd']
        
        if 'market_cap' in token_data:
            token.market_cap = token_data['market_cap']
        
        if 'creator' in token_data:
            token.creator = token_data['creator']
        
        if 'mint_authority' in token_data:
            token.mint_authority = token_data['mint_authority']
        
        if 'freeze_authority' in token_data:
            token.freeze_authority = token_data['freeze_authority']
        
        if 'is_nft' in token_data:
            token.is_nft = token_data['is_nft']
        
        token.updated_at = datetime.now()
        
        # Save full token data as JSON
        token.metadata_json = json.dumps(token_data) # Use renamed column
        
        session.commit()
        logger.info(f"Saved token data for {mint}")
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving token data for {mint}: {str(e)}")
    
    finally:
        session.close()

def save_token_risk_data(mint, risk_data):
    """
    Save token risk data to the database
    
    Args:
        mint (str): Token mint address
        risk_data (dict): Token risk data
    """
    if not risk_data:
        logger.warning(f"No risk data to save for token {mint}")
        return
    
    session = Session()
    try:
        # Get token
        token = session.query(Token).filter(Token.mint == mint).first()
        
        if not token:
            # Create new token
            token = Token(mint=mint)
            session.add(token)
        
        # Update risk data
        report = risk_data.get('report', {})
        summary = risk_data.get('summary', {})
        
        if report:
            # Extract data from full report
            if 'score' in report:
                token.risk_score = report['score']
            
            if 'risks' in report:
                token.risk_factors = json.dumps(report['risks'])
            
            # Extract basic token data from report
            if 'tokenMeta' in report:
                if 'name' in report['tokenMeta']:
                    token.name = report['tokenMeta']['name']
                
                if 'symbol' in report['tokenMeta']:
                    token.symbol = report['tokenMeta']['symbol']
            
            if 'creator' in report:
                token.creator = report['creator']
            
            if 'mintAuthority' in report:
                token.mint_authority = report['mintAuthority']
            
            if 'freezeAuthority' in report:
                token.freeze_authority = report['freezeAuthority']
        
        elif summary:
            # Extract data from summary
            if 'score' in summary:
                token.risk_score = summary['score']
            
            if 'risks' in summary:
                token.risk_factors = json.dumps(summary['risks'])
        
        # Determine risk level based on score
        if token.risk_score is not None:
            if token.risk_score < 20:
                token.risk_level = 'very_low'
            elif token.risk_score < 40:
                token.risk_level = 'low'
            elif token.risk_score < 60:
                token.risk_level = 'medium'
            elif token.risk_score < 80:
                token.risk_level = 'high'
            else:
                token.risk_level = 'very_high'
        
        token.updated_at = datetime.now()
        
        session.commit()
        logger.info(f"Saved risk data for token {mint}")
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving risk data for token {mint}: {str(e)}")
    
    finally:
        session.close()

def save_program_data(program_id, program_data):
    """
    Save program data to the database
    
    Args:
        program_id (str): Program ID
        program_data (dict): Program data
    """
    if not program_data:
        logger.warning(f"No program data to save for {program_id}")
        return
    
    session = Session()
    try:
        # Check if program exists
        program = session.query(Program).filter(Program.program_id == program_id).first()
        
        if not program:
            # Create new program
            program = Program(program_id=program_id)
            session.add(program)
        
        # Update program data
        if 'name' in program_data:
            program.name = program_data['name']
        
        if 'description' in program_data:
            program.description = program_data['description']
        
        if 'website' in program_data:
            program.website = program_data['website']
        
        if 'twitter' in program_data:
            program.twitter = program_data['twitter']
        
        if 'github' in program_data:
            program.github = program_data['github']
        
        if 'verified' in program_data:
            program.verified = program_data['verified']
        
        program.metadata_json = json.dumps(program_data) # Use renamed column
        program.updated_at = datetime.now()
        
        session.commit()
        logger.info(f"Saved program data for {program_id}")
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving program data for {program_id}: {str(e)}")
    
    finally:
        session.close()

def get_address_data(address):
    """
    Get all data for an address
    
    Args:
        address (str): Address to get data for
    
    Returns:
        dict: Address data
    """
    session = Session()
    try:
        # Get address
        db_address = session.query(Address).filter(Address.address == address).first()
        
        if not db_address:
            logger.warning(f"Address {address} not found in database")
            return None
        
        # Get transactions
        transactions = session.query(Transaction).filter(Transaction.address_id == db_address.id).all()
        
        # Get counterparties
        counterparties = session.query(Counterparty).filter(Counterparty.address_id == db_address.id).all()
        
        # Convert to dict
        address_data = {
            'id': db_address.id,
            'address': db_address.address,
            'network': db_address.network,
            'entity_name': db_address.entity_name,
            'entity_type': db_address.entity_type,
            'labels': db_address.labels.split(',') if db_address.labels else [],
            'first_seen': db_address.first_seen.isoformat() if db_address.first_seen else None,
            'last_seen': db_address.last_seen.isoformat() if db_address.last_seen else None,
            'risk_score': db_address.risk_score,
            'risk_level': db_address.risk_level,
            'risk_factors': json.loads(db_address.risk_factors) if db_address.risk_factors else [],
            'is_contract': db_address.is_contract,
            'created_at': db_address.created_at.isoformat(),
            'updated_at': db_address.updated_at.isoformat(),
            'transactions': [
                {
                    'hash': tx.hash,
                    'block_number': tx.block_number,
                    'block_time': tx.block_time.isoformat() if tx.block_time else None,
                    'success': tx.success,
                    'value': tx.value,
                    'value_usd': tx.value_usd,
                    'fee': tx.fee,
                    'program_id': tx.program_id,
                    'instruction_name': tx.instruction_name,
                    'data': json.loads(tx.data) if tx.data else None
                }
                for tx in transactions
            ],
            'counterparties': [
                {
                    'counterparty_address': cp.counterparty_address,
                    'interaction_count': cp.interaction_count,
                    'sent_volume': cp.sent_volume,
                    'received_volume': cp.received_volume,
                    'first_interaction': cp.first_interaction.isoformat() if cp.first_interaction else None,
                    'last_interaction': cp.last_interaction.isoformat() if cp.last_interaction else None,
                    'entity_name': cp.entity_name,
                    'entity_type': cp.entity_type,
                    'labels': cp.labels.split(',') if cp.labels else [],
                    'risk_score': cp.risk_score
                }
                for cp in counterparties
            ]
        }
        
        return address_data
    
    except Exception as e:
        logger.error(f"Error getting address data for {address}: {str(e)}")
        return None
    
    finally:
        session.close()

def get_token_data(mint):
    """
    Get all data for a token
    
    Args:
        mint (str): Token mint address
    
    Returns:
        dict: Token data
    """
    session = Session()
    try:
        # Get token
        token = session.query(Token).filter(Token.mint == mint).first()
        
        if not token:
            logger.warning(f"Token {mint} not found in database")
            return None
        
        # Convert to dict
        token_data = {
            'id': token.id,
            'mint': token.mint,
            'name': token.name,
            'symbol': token.symbol,
            'decimals': token.decimals,
            'supply': token.supply,
            'price_usd': token.price_usd,
            'market_cap': token.market_cap,
            'creator': token.creator,
            'mint_authority': token.mint_authority,
            'freeze_authority': token.freeze_authority,
            'is_nft': token.is_nft,
            'risk_score': token.risk_score,
            'risk_level': token.risk_level,
            'risk_factors': json.loads(token.risk_factors) if token.risk_factors else [],
            'metadata': json.loads(token.metadata_json) if token.metadata_json else {}, # Use renamed column
            'created_at': token.created_at.isoformat(),
            'updated_at': token.updated_at.isoformat()
        }
        
        return token_data
    
    except Exception as e:
        logger.error(f"Error getting token data for {mint}: {str(e)}")
        return None
    
    finally:
        session.close()

def get_high_risk_addresses(limit=10):
    """
    Get high risk addresses
    
    Args:
        limit (int): Maximum number of addresses to return
    
    Returns:
        list: High risk addresses
    """
    session = Session()
    try:
        # Get addresses with high risk score
        addresses = session.query(Address).filter(Address.risk_score >= 70).order_by(Address.risk_score.desc()).limit(limit).all()
        
        # Convert to list of dicts
        address_list = [
            {
                'id': addr.id,
                'address': addr.address,
                'network': addr.network,
                'entity_name': addr.entity_name,
                'entity_type': addr.entity_type,
                'labels': addr.labels.split(',') if addr.labels else [],
                'risk_score': addr.risk_score,
                'risk_level': addr.risk_level
            }
            for addr in addresses
        ]
        
        return address_list
    
    except Exception as e:
        logger.error(f"Error getting high risk addresses: {str(e)}")
        return []
    
    finally:
        session.close()

def get_high_risk_tokens(limit=10):
    """
    Get high risk tokens
    
    Args:
        limit (int): Maximum number of tokens to return
    
    Returns:
        list: High risk tokens
    """
    session = Session()
    try:
        # Get tokens with high risk score
        tokens = session.query(Token).filter(Token.risk_score >= 70).order_by(Token.risk_score.desc()).limit(limit).all()
        
        # Convert to list of dicts
        token_list = [
            {
                'id': token.id,
                'mint': token.mint,
                'name': token.name,
                'symbol': token.symbol,
                'risk_score': token.risk_score,
                'risk_level': token.risk_level
            }
            for token in tokens
        ]
        
        return token_list
    
    except Exception as e:
        logger.error(f"Error getting high risk tokens: {str(e)}")
        return []
    
    finally:
        session.close()

def export_address_data_to_csv(address, file_path):
    """
    Export address data to CSV
    
    Args:
        address (str): Address to export data for
        file_path (str): File path to save CSV to
    
    Returns:
        bool: Success status
    """
    address_data = get_address_data(address)
    
    if not address_data:
        logger.error(f"No data found for address {address}")
        return False
    
    try:
        # Export transactions
        if address_data['transactions']:
            tx_df = pd.DataFrame(address_data['transactions'])
            tx_df.to_csv(f"{file_path}_transactions.csv", index=False)
        
        # Export counterparties
        if address_data['counterparties']:
            cp_df = pd.DataFrame(address_data['counterparties'])
            cp_df.to_csv(f"{file_path}_counterparties.csv", index=False)
        
        # Export address info
        address_info = {k: v for k, v in address_data.items() if not isinstance(v, list)}
        info_df = pd.DataFrame([address_info])
        info_df.to_csv(f"{file_path}_info.csv", index=False)
        
        logger.info(f"Exported address data for {address} to {file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error exporting address data for {address} to CSV: {str(e)}")
        return False

# --- New AddressDatabase Class ---

class AddressDatabase:
    """
    Provides an object-oriented interface to the address database operations.
    """
    def __init__(self, db_path=None):
        """
        Initializes the AddressDatabase interface.

        Args:
            db_path (str, optional): Path to the database file. If provided,
                                     it could potentially override the global DATABASE_URL,
                                     though current implementation uses the global engine.
                                     Defaults to None.
        """
        # Ensure the database schema is created
        init_db()
        self.db_path = db_path if db_path else DATABASE_URL.replace("sqlite:///", "")

    def save_address_data(self, address, data):
        """Wraps the module-level save_address_data function."""
        save_address_data(address, data)

    def save_transactions(self, address, transactions):
        """Wraps the module-level save_transactions function."""
        save_transactions(address, transactions)

    def save_risk_data(self, address, risk_data):
        """Wraps the module-level save_risk_data function."""
        save_risk_data(address, risk_data)

    def save_counterparties(self, address, counterparties):
        """Wraps the module-level save_counterparties function."""
        save_counterparties(address, counterparties)

    def save_token_data(self, mint, token_data):
        """Wraps the module-level save_token_data function."""
        save_token_data(mint, token_data)

    def save_token_risk_data(self, mint, risk_data):
        """Wraps the module-level save_token_risk_data function."""
        save_token_risk_data(mint, risk_data)

    def save_program_data(self, program_id, program_data):
        """Wraps the module-level save_program_data function."""
        save_program_data(program_id, program_data)

    def get_address_data(self, address):
        """Wraps the module-level get_address_data function."""
        return get_address_data(address)

    def get_token_data(self, mint):
        """Wraps the module-level get_token_data function."""
        return get_token_data(mint)

    def get_high_risk_addresses(self, limit=10):
        """Wraps the module-level get_high_risk_addresses function."""
        return get_high_risk_addresses(limit=limit)

    def get_high_risk_tokens(self, limit=10):
        """Wraps the module-level get_high_risk_tokens function."""
        return get_high_risk_tokens(limit=limit)

    def export_address_data_to_csv(self, address, file_path):
        """Wraps the module-level export_address_data_to_csv function."""
        return export_address_data_to_csv(address, file_path)

# Initialize database if this script is run directly (optional, as class init does it)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Example usage:
    db_interface = AddressDatabase()
    print(f"AddressDatabase interface created for {db_interface.db_path}")
    # test_data = db_interface.get_address_data("SomeTestAddress")
    # print(test_data)