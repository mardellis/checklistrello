import requests
import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ChecklistItem:
    """Data class for checklist items"""
    id: str
    name: str
    state: str
    card_id: str
    card_name: str
    checklist_id: str
    checklist_name: str
    board_id: str
    board_name: str

@dataclass
class TrelloCard:
    """Data class for Trello cards"""
    id: str
    name: str
    desc: str
    due: Optional[str]
    board_id: str
    board_name: str
    list_id: str
    list_name: str
    checklists: List[Dict]

class TrelloAPI:
    """Trello API client for fetching cards and checklist items"""
    
    def __init__(self, api_key: str, token: str):
        self.api_key = api_key.strip()
        self.token = token.strip()
        self.base_url = "https://api.trello.com/1"
        self.auth_params = {
            'key': self.api_key,
            'token': self.token
        }
        
        # Log sanitized credentials for debugging
        logger.info(f"TrelloAPI initialized - API Key: {self.api_key[:8]}... (len: {len(self.api_key)})")
        logger.info(f"Token: {self.token[:8]}... (len: {len(self.token)})")
    
    def test_connection(self) -> Dict[str, Any]:
        """Test API connection and return user info"""
        try:
            url = f"{self.base_url}/members/me"
            
            logger.info(f"Testing connection to: {url}")
            logger.info(f"Auth params: key={self.api_key[:8]}..., token={self.token[:8]}...")
            
            response = requests.get(url, params=self.auth_params, timeout=10)
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Connection successful! User: {user_data.get('username', 'Unknown')}")
                return {
                    'success': True,
                    'user': {
                        'username': user_data.get('username', 'Unknown'),
                        'fullName': user_data.get('fullName', 'Unknown'),
                        'id': user_data.get('id', 'Unknown')
                    }
                }
            elif response.status_code == 401:
                error_detail = self._analyze_401_error(response)
                logger.error(f"401 Unauthorized: {error_detail}")
                return {
                    'success': False,
                    'error': f"Authentication failed: {error_detail}"
                }
            elif response.status_code == 400:
                logger.error(f"400 Bad Request: {response.text}")
                return {
                    'success': False,
                    'error': f"Bad request - check your API key format. Got: {response.text}"
                }
            else:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code} - {response.text}"
                }
                
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            return {
                'success': False,
                'error': "Connection timeout - please check your internet connection"
            }
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return {
                'success': False,
                'error': f"Connection failed: {str(e)}"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {e}")
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}"
            }
    
    def _analyze_401_error(self, response) -> str:
        """Analyze 401 error and provide helpful feedback"""
        try:
            error_data = response.json()
            error_message = error_data.get('message', 'Unknown error')
            
            if 'invalid key' in error_message.lower():
                return "Invalid API key. Please check your API key is exactly 32 characters."
            elif 'invalid token' in error_message.lower():
                return "Invalid token. Please regenerate your token from Trello."
            elif 'unauthorized' in error_message.lower():
                return "Unauthorized access. Check both API key and token."
            else:
                return f"Authentication error: {error_message}"
                
        except:
            # If we can't parse the JSON, return the raw text
            return f"Authentication failed: {response.text[:200]}"
    
    def get_user_boards(self) -> List[Dict[str, Any]]:
        """Get all boards for the authenticated user"""
        try:
            url = f"{self.base_url}/members/me/boards"
            params = {**self.auth_params, 'filter': 'open'}
            
            logger.info(f"Fetching boards from: {url}")
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch boards: {response.status_code} - {response.text}")
                return []
            
            response.raise_for_status()
            
            boards = response.json()
            logger.info(f"Successfully fetched {len(boards)} boards")
            
            return [
                {
                    'id': board['id'],
                    'name': board['name'],
                    'url': board['url'],
                    'desc': board.get('desc', ''),
                    'dateLastActivity': board.get('dateLastActivity', '')
                }
                for board in boards
            ]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch boards: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching boards: {str(e)}")
            return []
    
    def get_board_cards(self, board_id: str) -> List[TrelloCard]:
        """Get all cards from a specific board with checklists"""
        try:
            # Get board info first
            board_info = self._get_board_info(board_id)
            if not board_info:
                logger.error(f"Could not get board info for {board_id}")
                return []
            
            # Get all cards with checklists
            url = f"{self.base_url}/boards/{board_id}/cards"
            params = {
                **self.auth_params,
                'checklists': 'all',
                'list': 'true'
            }
            
            logger.info(f"Fetching cards from board: {board_info['name']}")
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            
            cards_data = response.json()
            cards = []
            
            for card_data in cards_data:
                card = TrelloCard(
                    id=card_data['id'],
                    name=card_data['name'],
                    desc=card_data.get('desc', ''),
                    due=card_data.get('due'),
                    board_id=board_id,
                    board_name=board_info['name'],
                    list_id=card_data['idList'],
                    list_name=card_data.get('list', {}).get('name', 'Unknown List'),
                    checklists=card_data.get('checklists', [])
                )
                cards.append(card)
            
            logger.info(f"Successfully fetched {len(cards)} cards from board {board_info['name']}")
            return cards
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch cards: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching cards: {str(e)}")
            return []
    
    def get_checklist_items(self, board_id: str) -> List[ChecklistItem]:
        """Extract all checklist items from a board"""
        try:
            cards = self.get_board_cards(board_id)
            checklist_items = []
            
            for card in cards:
                for checklist in card.checklists:
                    checklist_name = checklist.get('name', 'Unnamed Checklist')
                    
                    for item in checklist.get('checkItems', []):
                        checklist_item = ChecklistItem(
                            id=item['id'],
                            name=item['name'],
                            state=item['state'],
                            card_id=card.id,
                            card_name=card.name,
                            checklist_id=checklist['id'],
                            checklist_name=checklist_name,
                            board_id=card.board_id,
                            board_name=card.board_name
                        )
                        checklist_items.append(checklist_item)
            
            logger.info(f"Extracted {len(checklist_items)} checklist items from {len(cards)} cards")
            return checklist_items
            
        except Exception as e:
            logger.error(f"Failed to extract checklist items: {str(e)}")
            return []
    
    def _get_board_info(self, board_id: str) -> Optional[Dict[str, Any]]:
        """Get basic board information"""
        try:
            url = f"{self.base_url}/boards/{board_id}"
            response = requests.get(url, params=self.auth_params, timeout=10)
            response.raise_for_status()
            
            board_data = response.json()
            return {
                'id': board_data['id'],
                'name': board_data['name'],
                'url': board_data['url']
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get board info: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting board info: {str(e)}")
            return None
    
    def update_checklist_item_name(self, card_id: str, checklist_item_id: str, new_name: str) -> bool:
        """Update checklist item name (for adding due dates to item text)"""
        try:
            url = f"{self.base_url}/cards/{card_id}/checkItem/{checklist_item_id}"
            data = {
                **self.auth_params,
                'name': new_name
            }
            
            response = requests.put(url, data=data, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Successfully updated checklist item {checklist_item_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update checklist item: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating checklist item: {str(e)}")
            return False

def validate_trello_credentials(api_key: str, token: str) -> Dict[str, Any]:
    """Validate Trello API credentials with detailed feedback"""
    
    # Clean inputs
    api_key = api_key.strip() if api_key else ""
    token = token.strip() if token else ""
    
    logger.info(f"Validating credentials - API Key length: {len(api_key)}, Token length: {len(token)}")
    
    # Check for empty credentials
    if not api_key or not token:
        return {
            'success': False,
            'error': 'Both API Key and Token are required'
        }
    
    # Check API key format
    if len(api_key) != 32:
        return {
            'success': False,
            'error': f'API Key should be exactly 32 characters long (got {len(api_key)})'
        }
    
    # Check if API key contains only valid characters (alphanumeric)
    if not api_key.isalnum():
        return {
            'success': False,
            'error': 'API Key should contain only letters and numbers'
        }
    
    # Check token format
    if len(token) != 64:
        return {
            'success': False,
            'error': f'Token should be exactly 64 characters long (got {len(token)})'
        }
    
    # Check if token contains only valid characters (alphanumeric)
    if not token.isalnum():
        return {
            'success': False,
            'error': 'Token should contain only letters and numbers'
        }
    
    # Test actual connection
    logger.info("Credentials format validated, testing connection...")
    trello = TrelloAPI(api_key, token)
    return trello.test_connection()

def get_fresh_trello_credentials_guide() -> str:
    """Get updated guide for getting Trello credentials"""
    return """
🔑 **How to get fresh Trello API credentials:**

1. **Get API Key:**
   - Go to: https://trello.com/app-key
   - Copy your API Key (32 characters)

2. **Generate Token:**
   - On the same page, click "Token" link
   - Or go directly to: https://trello.com/1/authorize?expiration=never&scope=read,write&response_type=token&name=ChecklistRello&key=YOUR_API_KEY
   - Replace YOUR_API_KEY with your actual API key
   - Click "Allow" to authorize
   - Copy the generated token (64 characters)

3. **Common Issues:**
   - Make sure API key is exactly 32 characters
   - Make sure token is exactly 64 characters
   - Don't include spaces or extra characters
   - Token expires - regenerate if needed
   - Check if your Trello account has API access enabled

4. **Test Connection:**
   - Paste both credentials in the app
   - Click "Test Connection"
   - Should show your Trello username if successful
"""

# Test function with better debugging
def test_trello_api_connection(api_key: str = "", token: str = ""):
    """Test Trello API connection with detailed debugging"""
    print("🔗 TRELLO API CONNECTION TEST")
    print("=" * 50)
    
    if not api_key or not token:
        print("❌ Please provide API key and token for testing")
        print(get_fresh_trello_credentials_guide())
        return
    
    print(f"API Key: {api_key[:8]}...{api_key[-4:]} (length: {len(api_key)})")
    print(f"Token: {token[:8]}...{token[-4:]} (length: {len(token)})")
    print()
    
    # Test validation first
    print("1. Validating credential format...")
    validation_result = validate_trello_credentials(api_key, token)
    
    if validation_result['success']:
        print("✅ Credential format is valid")
        print(f"   Connected as: {validation_result['user']['fullName']}")
        print(f"   Username: {validation_result['user']['username']}")
        
        # Test getting boards
        print("\n2. Testing board access...")
        trello = TrelloAPI(api_key, token)
        boards = trello.get_user_boards()
        
        if boards:
            print(f"✅ Successfully retrieved {len(boards)} boards:")
            for i, board in enumerate(boards[:3], 1):
                print(f"   {i}. {board['name']} (ID: {board['id'][:8]}...)")
            
            if len(boards) > 3:
                print(f"   ... and {len(boards) - 3} more boards")
                
            # Test getting checklist items from first board
            if boards:
                print(f"\n3. Testing checklist items from '{boards[0]['name']}'...")
                items = trello.get_checklist_items(boards[0]['id'])
                print(f"✅ Found {len(items)} checklist items")
                
                if items:
                    print("   Sample items:")
                    for item in items[:3]:
                        status = "✅" if item.state == "complete" else "⏳"
                        print(f"   {status} {item.name[:50]}...")
        else:
            print("⚠️  No boards found or error retrieving boards")
    else:
        print(f"❌ Validation failed: {validation_result['error']}")
        print("\n" + get_fresh_trello_credentials_guide())

if __name__ == "__main__":
    # Test with sample credentials (these won't work, user needs real ones)
    test_api_key = "3a2acba63480f371331497003fc4291"  # Sample - won't work
    test_token = "734bc8ffd72b664a9343ce882a36dde3f6cfa1148fd6773d0560463dbcb"  # Sample - won't work
    
    print("⚠️  This test uses sample credentials that won't work.")
    print("Replace with your real credentials to test properly.")
    print()
    
    test_trello_api_connection(test_api_key, test_token)