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
            else:
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code} - {response.text}"
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
                    'dateLastActivity': board.get('dateLastActivity', '')
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
            
            logger.info(f"Fetched {len(cards)} cards from board {board_info['name']}")
            return cards
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch cards: {str(e)}")
            return []
    
    def get_checklist_items(self, board_id: str) -> List[ChecklistItem]:
        """Extract all checklist items from a board"""
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
        
        logger.info(f"Extracted {len(checklist_items)} checklist items")
        return checklist_items
    
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
            
            logger.info(f"Updated checklist item {checklist_item_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update checklist item: {str(e)}")
            return False

def validate_trello_credentials(api_key: str, token: str) -> Dict[str, Any]:
    """Validate Trello API credentials"""
    if not api_key or not token:
        return {
            'success': False,
            'error': 'API Key and Token are required'
        }
    
    # Basic format validation
    if len(api_key) != 32:
        return {
            'success': False,
            'error': 'API Key should be 32 characters long'
        }
    
    if len(token) != 64:
        return {
            'success': False,
            'error': 'Token should be 64 characters long'
        }
    
    # Test actual connection
    trello = TrelloAPI(api_key, token)
    return trello.test_connection()

# Test function
def test_trello_api():
    """Test function - requires actual API credentials"""
    print("Trello API Test")
    print("=" * 40)
    
    # These would need to be real credentials for testing
    api_key = "your_api_key_here"
    token = "your_token_here"
    
    if api_key == "your_api_key_here":
        print("❌ Please set real API credentials to test")
        return
    
    # Test connection
    result = validate_trello_credentials(api_key, token)
    if result['success']:
        print(f"✅ Connection successful!")
        print(f"User: {result['user']['fullName']}")
        
        # Test getting boards
        trello = TrelloAPI(api_key, token)
        boards = trello.get_user_boards()
        print(f"Found {len(boards)} boards")
        
        if boards:
            # Test getting checklist items from first board
            first_board = boards[0]
            print(f"Testing with board: {first_board['name']}")
            
            items = trello.get_checklist_items(first_board['id'])
            print(f"Found {len(items)} checklist items")
            
            for item in items[:3]:  # Show first 3 items
                print(f"- {item.name} (Card: {item.card_name})")
    else:
        print(f"❌ Connection failed: {result['error']}")

if __name__ == "__main__":
    test_trello_api()
