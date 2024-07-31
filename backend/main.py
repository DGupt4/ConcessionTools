import os
import uuid
import asyncio
import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from google.oauth2 import service_account
from dotenv import load_dotenv

from concession_service import ConcessionService

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = './credentials.json'
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

app = FastAPI()
current_job = None

class ProcessRequest(BaseModel):
  group_name: str
  game_date: str
  sheet_url: str
  sheet_num: int
  num_ppl: int
  wait_time: int

class JobStatus(BaseModel):
  job_id: str
  status: str

async def process_all_steps(request: ProcessRequest):
  global current_job
  try:
    concession_service = ConcessionService(os.getenv('ACCESS_TOKEN'), credentials)

    steps = [
      ('initializing', concession_service.initialize_worksheet(request.sheet_url, request.sheet_num)),
      ('creating group', concession_service.create_group(request.group_name)),
      ('adding users', concession_service.add_users()),
      ('gathering data', concession_service.create_columns()),
      ('sending react message', concession_service.begin_confirm(request.game_date, request.wait_time)),
      ('waiting time', concession_service.wait_time(request.wait_time)), 
      ('picking people', concession_service.pick_random(request.num_ppl))
    ]

    for step_status, step in steps:
      if current_job.status == 'terminated':
        logger.info("Job terminated")
        break

      current_job.status = step_status
      logger.info(f" Starting step: {step_status}")
      await step
      logger.info(f" Completed step: {step_status}")
    
    if current_job.status != 'terminated':
      current_job.status = 'completed'
      logger.info("Job completed successfully")
  except Exception as e:
    logger.error(f"Error during job execution: {repr(e)}")
    current_job.status = 'failed'
    # await concession_service.terminate()
  finally:
    if current_job.status in ['completed', 'terminated', 'failed']:
      current_job = None

@app.post('/start_process')
async def start_process(request: ProcessRequest, background_tasks: BackgroundTasks):
  global current_job
  if current_job is not None:
      raise HTTPException(status_code=409, detail='A job is already running')  

  job_id = str(uuid.uuid4())
  current_job = JobStatus(job_id=job_id, status='started')
  background_tasks.add_task(process_all_steps, request)
  return {'job_id': job_id, 'status': 'started'}

@app.post('/terminate_job')
async def terminate_job():
  global current_job
  if current_job is None:
      return {'message': 'No jobs to terminate!'}
  current_job.status = 'terminated' 
  return {'message': 'Job termination requested'}

@app.get('/job_status')
async def job_status():
  global current_job
  if current_job:
    return {'status': current_job.status}
  return {'status': 'idle'}