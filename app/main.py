from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.endpoints import test ,recognition
from app.services.cron_service import run_cron_verify_id
from apscheduler.schedulers.asyncio import AsyncIOScheduler # type: ignore
from app.database.config import conect_to_firestoreDataBase
app = FastAPI()

db = conect_to_firestoreDataBase()

#routes
@app.get("/")
def read_root():
    return {"message": "Hello, from Identity Identifier Server"}

#Test routes , only for testing purpose
app.include_router(test.router, prefix="/test", tags=["test"])

# Recognition routes
app.include_router(recognition.router, prefix="/recognition", tags=["recognition"])


# URL not found exception
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "message": "The path was not found. Check the URL or consult the documentation."
        }
    )
    
#CRON JOBS    
LOCK_DOC_PATH = ('cronLocks', 'taskLock')

async def cron_task():
  await  run_cron_verify_id()


async def scheduled_job():
    try:
        lock_ref = db.collection(LOCK_DOC_PATH[0]).document(LOCK_DOC_PATH[1])
        lock_doc = lock_ref.get()

        if lock_doc.exists and lock_doc.to_dict().get("locked", False):
            print("La tarea cron ya está en ejecución. Se omite esta ejecución.")
            return

        lock_ref.set({"locked": True})
        print("Tarea cron iniciada.")

        await cron_task()

        lock_ref.set({"locked": False})
        print("Tarea cron completada y desbloqueada.")
    except Exception as e:
        print(f"Error al ejecutar la tarea cron: {e}")
        lock_ref.set({"locked": False})

scheduler = AsyncIOScheduler()
scheduler.add_job(scheduled_job, 'interval', seconds=5, max_instances=2)
scheduler.start()
