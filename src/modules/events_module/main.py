from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from event_emitter import EventEmitter
from contextlib import asynccontextmanager

# Instantiate the EventEmitter
emitter = EventEmitter()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect the EventEmitter
    await emitter.connect()

    # Yield control back to the app to handle incoming requests
    yield

    # Shutdown: Close the EventEmitter connections
    await emitter.nats_client.close()

# Instantiate the FastAPI app and pass the lifespan context manager
app = FastAPI(lifespan=lifespan)

# Define a Pydantic model for the incoming event data
class EventData(BaseModel):
    event_type: str
    data: dict

@app.post("/emit_event")
async def emit_event(event: EventData):
    """
    Endpoint to emit a new event.
    """
    try:
        await emitter.emit_event(event.event_type, event.data)
        return {"status": "Event emitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/latest_event/{event_type}")
async def get_latest_event(event_type: str):
    """
    Endpoint to get the latest event of a specific type.
    """
    try:
        latest_event = await emitter.get_latest_event(event_type)
        if latest_event:
            return latest_event
        else:
            raise HTTPException(status_code=404, detail="No latest event found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/event_history/{ipfs_hash}")
async def get_event_history(ipfs_hash: str):
    """
    Endpoint to retrieve a historical event from IPFS.
    """
    try:
        event_history = await emitter.retrieve_event_history(ipfs_hash)
        if event_history:
            return event_history
        else:
            raise HTTPException(status_code=404, detail="Event not found on IPFS")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
