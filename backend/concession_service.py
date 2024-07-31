import uuid
import random
import asyncio
import gspread
import logging
from datetime import datetime, timedelta
from groupme import GroupMe
from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound
from google.oauth2.service_account import Credentials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConcessionService:
  """
  A service class for managing concession-related operations
  """

  def __init__(self, access_token: str, credentials: Credentials):
    """
    Initialize the ConcessionService.

    Args:
      access_token (str): The acess token for the GroupME API.
      credentials (Credentials): The credentials for accessing Google Sheets.
    """
    self.api = GroupMe(access_token)
    self.client = gspread.authorize(credentials)
    self.sheet = None
    self.worksheet = None
    self.group_id = None
    self.message_id = None

  async def initialize_worksheet(self, sheet_url: str, sheet_num: int):
    """
    Initialize the Google Sheet worksheet.

    Args:
        sheet_url (str): The URL of the Google Sheet.
        sheet_num (int): The index of the worksheet to use (1-based).

    Raises:
        SpreadsheetNotFound: If the provided URL is invalid.
        WorksheetNotFound: If the provided sheet number is invalid.
    """
    try: 
      self.sheet = await asyncio.to_thread(self.client.open_by_url, sheet_url)
      self.worksheet = await asyncio.to_thread(self.sheet.get_worksheet, sheet_num - 1)
    except SpreadsheetNotFound:
      logging.error("Invalid spreadsheet URL")
    except WorksheetNotFound:
      logging.error("Invalid sheet number")
    except Exception as e:
      logging.error(f"Error initializing worksheet: {repr(e)}")

  async def create_group(self, name: str):
    """
    Create a new GroupMe group.

    Args:
        name (str): The name of the group to create.
    """
    result = await asyncio.to_thread(self.api.create_group, name)
    self.group_id = result['id']

  async def add_users(self):
    """
    Add users to the GroupMe group based on information from the worksheet.

    This method reads nicknames and phone numbers from the worksheet
    and adds the corresponding users to the GroupMe group.
    """
    nickname = await asyncio.to_thread(self.worksheet.col_values, 2) # hardcoded
    nickname = nickname[1:]
    phone_nums = await asyncio.to_thread(self.worksheet.col_values, 7) # hardcoded
    phone_nums = phone_nums[1:]

    phone_nums = ['+1 ' + num for num in phone_nums]

    await asyncio.to_thread(self.api.add_user, self.group_id, nickname, phone_nums)

  async def create_columns(self):
    """
    Create additional columns in the worksheet for tracking user data.

    This method adds 'User ID', 'Confirmed', and 'Picked' columns to the worksheet.
    """
    num_rows = len(await asyncio.to_thread(self.worksheet.col_values, 2)) - 1
    num_cols = len(await asyncio.to_thread(self.worksheet.row_values, 1))

    picked_data = ['Picked'] + ['-'] * num_rows
    confirmed_data = ['Confirmed'] + ['-'] * num_rows
    user_id_data = ['User ID']

    members = await asyncio.to_thread(self.api.get_groups, self.group_id)
    members = members['members']
    members_dict = {member['nickname']: member['user_id'] for member in members}

    nickname_list = await asyncio.to_thread(self.worksheet.col_values, 2) # hardcoded
    nickname_list = nickname_list[1:]

    for nickname in nickname_list:
      if nickname in members_dict:
        user_id_data.append(members_dict[nickname])

    await asyncio.to_thread(self.worksheet.insert_cols, [user_id_data, confirmed_data, picked_data], num_cols + 1)

  async def begin_confirm(self, game_date: str, wait_time: int):
    """
    Send a confirmation message to the GroupMe group

    Args:
        game_date (str): The date and time of the game in "YYYY-MM-DDTHH:MM" format.
    """
    parsed_time = datetime.strptime(game_date, "%Y-%m-%dT%H:%M")
    date = parsed_time.strftime("%B %d, %Y")
    time = parsed_time.strftime("%I:%M %p")
    arrive_time = (parsed_time - timedelta(hours=2)).strftime("%I:%M %p")


    msg = f"""
    There is a concession on {date} at {time}
    You are expected to arrive 2 hours early at {arrive_time}

    React with 👍 or 👎 to confirm/deny your attendance in the coming concession!

    This poll will close in {wait_time} minutes
    """

    data = await asyncio.to_thread(self.api.send_message, self.group_id, str(uuid.uuid4()), msg)
    self.message_id = data['message']['id']

  async def wait_time(self, wait_time: int):
    """
    Waiting for users to react to the GroupMe message

    Args:
        wait_time (int): The number of minutes to wait for responses.
    """
    await asyncio.sleep(wait_time)

  async def pick_random(self, num_ppl: int):
    """
    Randomly select users who confirmed their attendance.

    Args:
        num_ppl (int): The number of people to select.

    This method selects random users who confirmed their attendance,
    updates the worksheet, and sends a message with the selected users.
    """
    messages = await asyncio.to_thread(self.api.get_message, self.group_id)
    message = next((msg for msg in messages['messages'] if msg['id'] == self.message_id), None)

    if 'reactions' not in message.keys():
      await asyncio.to_thread(self.api.send_message, self.group_id, str(uuid.uuid4()), 'No reactions found!')
      return

    reactions = message['reactions']
    accepted_users = next((r['user_ids'] for r in reactions if r['code'] == '👍'), [])
    denied_users = next((r['user_ids'] for r in reactions if r['code'] == '👎'), [])
    picked_users = random.sample(accepted_users, min(len(accepted_users), num_ppl))

    # Updating columns
    confirmed_col = self.worksheet.find('Confirmed').col
    picked_col = self.worksheet.find('Picked').col

    update_tasks = [
        *[asyncio.to_thread(self.worksheet.update_cell, self.worksheet.find(id).row, confirmed_col, 'TRUE') for id in accepted_users],
        *[asyncio.to_thread(self.worksheet.update_cell, self.worksheet.find(id).row, confirmed_col, 'FALSE') for id in denied_users],
        *[asyncio.to_thread(self.worksheet.update_cell, self.worksheet.find(id).row, picked_col, 'TRUE') for id in picked_users]
    ]
    await asyncio.gather(*update_tasks)

    picked_names = [await asyncio.to_thread(self.worksheet.cell, self.worksheet.find(id).row, 2) for id in picked_users] # hardcoded
    picked_names = [cell.value for cell in picked_names] 

    await asyncio.to_thread(self.api.send_message, self.group_id, str(uuid.uuid4()), f"Selected People:\n {'\n'.join(picked_names)}")

  async def terminate(self):
    """
    Clean up resources and terminate the service.

    This method removes added columns from the worksheet and should handle
    any necessary cleanup operations.
    """
    try: 
      columns = ['User ID', 'Confirmed', 'Picked']
      for col in columns:
        cell = self.worksheet.find(col)
        if cell:
          self.worksheet.delete_columns(cell.col)
      # self.api.destroy_group(self.group_id)
    except Exception as e:
      print(repr(e))
