import requests
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GroupMe:
  BASE_URL = 'https://api.groupme.com/v3'

  def __init__(self, access_token: str):
      self.access_token = access_token
      self.headers = {
          "content-type": "application/json",
          "x-access-token": self.access_token
      }

  def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
      url = f'{self.BASE_URL}/{endpoint}'

      try:
          response = requests.request(method, url, headers=self.headers, json=data)
          response.raise_for_status()
          return response.json()['response']
      except requests.exceptions.HTTPError as err:
          logger.error(f"http error occurred: {err}")
      except requests.exceptions.RequestException as err:
          logger.error(f"request error occurred: {err}")

  def add_user(self, group_id: int, nicknames: List[str], phone_nums: List[str]) -> Dict[str, Any]:
      data = {
          'members': [
              {'nickname': nick, 'phone_number': phone}
              for nick, phone in zip(nicknames, phone_nums)
          ]
      }
      return self._make_request('post', f'groups/{group_id}/members/add', data)

  def create_group(self, name: str) -> Dict[str, Any]:
      return self._make_request('POST', 'groups', {'name': name})
  
  def destroy_group(self, group_id: int) -> Dict[str, Any]:
      return self._make_request('POST', f'groups/{group_id}/destroy')

  def remove_user(self, group_id: int, member_id: int) -> Dict[str, Any]:
      return self._make_request('POST', f'groups/{group_id}/members/{member_id}/remove')

  def send_message(self, group_id: int, source_guid: str, text: str) -> Dict[str, Any]:
      data = {'message': {'source_guid': source_guid, 'text': text}}
      return self._make_request('POST', f'groups/{group_id}/messages', data)

  def get_message(self, group_id: int) -> Dict[str, Any]:
      return self._make_request('GET', f'groups/{group_id}/messages')

  def get_groups(self, group_id: Optional[int] = None) -> Dict[str, Any]:
      endpoint = f'groups/{group_id}' if group_id else 'groups'
      return self._make_request('GET', endpoint)