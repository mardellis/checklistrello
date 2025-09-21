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
        self.api_key = api_key
        self.token = token
        self.base_url = "https://api.trello.com/1"
        self.auth_params = {
            'key': self.api_key,
            'token': self.token
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test API connection and return user info"""
        try:
            url = f"{self.base_url}/members/me"
            response = requests.get(url, params=self.auth_params, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    'success': True,
                    'user': {
                        'username': user_data.get('username', 'Unknown'),
                        'fullName': user_data.get('fullName', 'Unknown'),
                        'id': user_data.get('id', 'Unknown')
                    }
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'error': "Invalid API credentials. Please get fresh credentials from https://trello.com/app-key"
                }
            elif response.status_code == 403:
                return {
                    'success': False,
                    'error': "Access denied. Check your token permissions."
                }
            else:
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code} - {response.text[:100]}"
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': "Connection timeout. Please check your internet connection."
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                'success': False,
                'error': f"Connection failed: {str(e)}"
            }
    
    def get_user_boards(self) -> List[Dict[str, Any]]:
        """Get all boards for the authenticated user"""
        try:
            url = f"{self.base_url}/members/me/boards"
            params = {**self.auth_params, 'filter': 'open'}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            boards = response.json()
            return [
                {
                    'id': board['id'],
                    'name': board['name'],
                    'url': board['url'],
                    'desc': board.get('desc', ''),
                    'dateLastActivity': board.get('dateLastActivity', ''),
                    'shortUrl': board.get('shortUrl', '')
                }
                for board in boards
            ]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch boards: {str(e)}")
            return []
    
    def get_board_cards(self, board_id: str) -> List[TrelloCard]:
        """Get all cards from a specific board with checklists"""
        try:
            # Get board info first
            board_info = self._get_board_info(board_id)
            if not board_info:
                logger.warning(f"Could not get board info for {board_id}")
                return []

            # Get all cards with checklists
            url = f"{self.base_url}/boards/{board_id}/cards"
            params = {
                **self.auth_params,
                'checklists': 'all',
                'list': 'true'
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            cards_data = response.json()
            cards = []
            
            for card_data in cards_data:
                # Handle list information safely
                list_info = card_data.get('list', {})
                list_name = list_info.get('name', 'Unknown List') if isinstance(list_info, dict) else 'Unknown List'
                
                card = TrelloCard(
                    id=card_data['id'],
                    name=card_data['name'],
                    desc=card_data.get('desc', ''),
                    due=card_data.get('due'),
                    board_id=board_id,
                    board_name=board_info['name'],
                    list_id=card_data.get('idList', ''),
                    list_name=list_name,
                    checklists=card_data.get('checklists', [])
                )
                cards.append(card)
            
            logger.info(f"Fetched {len(cards)} cards from board '{board_info['name']}'")
            return cards
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch cards from board {board_id}: {str(e)}")
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
                    checklist_id = checklist.get('id', '')
                    
                    for item in checklist.get('checkItems', []):
                        checklist_item = ChecklistItem(
                            id=item['id'],
                            name=item['name'],
                            state=item['state'],  # 'complete' or 'incomplete'
                            card_id=card.id,
                            card_name=card.name,
                            checklist_id=checklist_id,
                            checklist_name=checklist_name,
                            board_id=card.board_id,
                            board_name=card.board_name
                        )
                        checklist_items.append(checklist_item)
            
            logger.info(f"Extracted {len(checklist_items)} checklist items from {len(cards)} cards")
            return checklist_items
            
        except Exception as e:
            logger.error(f"Error extracting checklist items: {str(e)}")
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
                'url': board_data['url'],
                'desc': board_data.get('desc', ''),
                'closed': board_data.get('closed', False)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get board info for {board_id}: {str(e)}")
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
            
            logger.info(f"Updated checklist item {checklist_item_id} with new name")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update checklist item {checklist_item_id}: {str(e)}")
            return False
    
    def get_board_lists(self, board_id: str) -> List[Dict[str, Any]]:
        """Get all lists from a board"""
        try:
            url = f"{self.base_url}/boards/{board_id}/lists"
            response = requests.get(url, params=self.auth_params, timeout=10)
            response.raise_for_status()
            
            lists_data = response.json()
            return [
                {
                    'id': list_item['id'],
                    'name': list_item['name'],
                    'pos': list_item.get('pos', 0),
                    'closed': list_item.get('closed', False)
                }
                for list_item in lists_data if not list_item.get('closed', False)
            ]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch lists: {str(e)}")
            return []

def validate_trello_credentials(api_key: str, token: str) -> Dict[str, Any]:
    """Validate Trello API credentials with comprehensive checks"""
    # Basic validation
    if not api_key or not token:
        return {
            'success': False,
            'error': 'Both API Key and Token are required'
        }
    
    # Clean the credentials
    api_key = api_key.strip()
    token = token.strip()
    
    # Format validation
    if len(api_key) != 32:
        return {
            'success': False,
            'error': f'API Key should be exactly 32 characters (got {len(api_key)})'
        }
    
    # Token can be 64 characters or longer (some new tokens are longer)
    if len(token) < 64:
        return {
            'success': False,
            'error': f'Token should be at least 64 characters (got {len(token)})'
        }
    
    # Check if credentials contain valid characters
    if not api_key.isalnum():
        return {
            'success': False,
            'error': 'API Key should only contain letters and numbers'
        }
    
    # Test actual connection
    try:
        trello = TrelloAPI(api_key, token)
        return trello.test_connection()
    except Exception as e:
        return {
            'success': False,
            'error': f'Validation error: {str(e)}'
        }

def get_trello_credentials_guide() -> str:
    """Get step-by-step guide for getting Trello credentials"""
    return """
📝 **How to get your Trello API credentials:**

1. **Get API Key:**
   - Go to: https://trello.com/app-key
   - Copy the **32-character API Key** (first box)

2. **Generate Token:**
   - On the same page, click **"Generate a Token"**
   - Copy the **64+ character Token** (second box)
   - Make sure to authorize the token for your account

3. **Security Notes:**
   - Keep these credentials private
   - Tokens can expire - generate new ones if needed
   - You can revoke tokens anytime from your Trello account

4. **Troubleshooting:**
   - If you get 401 errors, your token may have expired
   - If you get 403 errors, check token permissions
   - Make sure you're logged into the correct Trello account
    """

# Test function
def test_trello_api():
    """Test function for development"""
    print("🔗 TRELLO API TEST")
    print("=" * 40)
    
    # These would need to be real credentials for testing
    api_key = "your_api_key_here" 
    token = "your_token_here"
    
    if api_key == "your_api_key_here":
        print("❌ Please set real API credentials to test")
        print(get_trello_credentials_guide())
        return
    
    # Test validation
    print("Testing credential validation...")
    result = validate_trello_credentials(api_key, token)
    
    if result['success']:
        print(f"✅ Connection successful!")
        print(f"User: {result['user']['fullName']} (@{result['user']['username']})")
        
        # Test getting boards
        trello = TrelloAPI(api_key, token)
        boards = trello.get_user_boards()
        print(f"\n📋 Found {len(boards)} boards:")
        
        for i, board in enumerate(boards[:3], 1):  # Show first 3 boards
            print(f"{i}. {board['name']} (ID: {board['id'][:8]}...)")
        
        if boards:
            # Test getting checklist items from first board
            first_board = boards[0]
            print(f"\n🔍 Testing checklist items from: {first_board['name']}")
            
            items = trello.get_checklist_items(first_board['id'])
            print(f"Found {len(items)} checklist items")
            
            for item in items[:3]:  # Show first 3 items
                status = "✅" if item.state == 'complete' else "⏳"
                print(f"  {status} {item.name[:50]} (Card: {item.card_name})")
                
    else:
        print(f"❌ Connection failed: {result['error']}")
        print("\n" + get_trello_credentials_guide())

if __name__ == "__main__":
    test_trello_api()