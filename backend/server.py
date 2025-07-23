from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, date

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class Heat(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    heat_number: str
    steel_type: str  # "20.64mm" or "23mm"
    quantity_kg: float
    date_received: date = Field(default_factory=date.today)
    remaining_kg: float = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.remaining_kg is None:
            self.remaining_kg = self.quantity_kg

class HeatCreate(BaseModel):
    heat_number: str
    steel_type: str
    quantity_kg: float
    date_received: Optional[date] = None

class Production(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: date
    product_type: str  # "MK-III" or "MK-V"
    quantity_produced: int
    material_consumed_kg: float = None
    
    def __init__(self, **data):
        super().__init__(**data)
        # Calculate material consumption based on product type
        if self.material_consumed_kg is None:
            if self.product_type == "MK-III":
                self.material_consumed_kg = self.quantity_produced * 0.930
            elif self.product_type == "MK-V":
                self.material_consumed_kg = self.quantity_produced * 1.15

class ProductionCreate(BaseModel):
    date: date
    product_type: str
    quantity_produced: int

class InventoryStatus(BaseModel):
    steel_type: str
    total_received_kg: float
    total_consumed_kg: float
    current_stock_kg: float
    heats: List[dict]
    low_stock_alert: bool
    reorder_recommendation: str

class DashboardData(BaseModel):
    inventory_status: List[InventoryStatus]
    recent_productions: List[Production]
    recent_heats: List[Heat]
    total_production_mkiii: int
    total_production_mkv: int

# Routes
@api_router.get("/")
async def root():
    return {"message": "Inventory Management API"}

@api_router.post("/heat", response_model=Heat)
async def add_heat(heat_data: HeatCreate):
    """Add a new heat record"""
    try:
        heat_dict = heat_data.dict()
        if heat_dict.get('date_received') is None:
            heat_dict['date_received'] = date.today()
        
        heat_obj = Heat(**heat_dict)
        
        # Check if heat number already exists
        existing_heat = await db.heats.find_one({"heat_number": heat_obj.heat_number})
        if existing_heat:
            raise HTTPException(status_code=400, detail="Heat number already exists")
        
        # Convert date to string for MongoDB storage
        heat_dict = heat_obj.dict()
        if isinstance(heat_dict['date_received'], date):
            heat_dict['date_received'] = heat_dict['date_received'].isoformat()
        
        await db.heats.insert_one(heat_dict)
        return heat_obj
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/heats", response_model=List[Heat])
async def get_heats():
    """Get all heat records"""
    try:
        heats = await db.heats.find().sort("date_received", -1).to_list(1000)
        return [Heat(**heat) for heat in heats]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/production", response_model=Production)
async def add_production(production_data: ProductionCreate):
    """Add a new production record and update inventory"""
    try:
        production_obj = Production(**production_data.dict())
        
        # Determine steel type based on product type
        steel_type = "20.64mm" if production_obj.product_type == "MK-III" else "23mm"
        
        # Find available heats for this steel type with remaining stock
        heats = await db.heats.find({
            "steel_type": steel_type,
            "remaining_kg": {"$gt": 0}
        }).sort("date_received", 1).to_list(1000)
        
        if not heats:
            raise HTTPException(status_code=400, detail=f"No stock available for {steel_type} steel")
        
        # Calculate total material needed
        material_needed = production_obj.material_consumed_kg
        
        # Check if enough material is available
        total_available = sum(heat["remaining_kg"] for heat in heats)
        if total_available < material_needed:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock. Available: {total_available:.2f}kg, Required: {material_needed:.2f}kg"
            )
        
        # Deduct material from heats (FIFO)
        remaining_needed = material_needed
        for heat in heats:
            if remaining_needed <= 0:
                break
            
            if heat["remaining_kg"] >= remaining_needed:
                # This heat can fulfill the remaining requirement
                new_remaining = heat["remaining_kg"] - remaining_needed
                await db.heats.update_one(
                    {"id": heat["id"]},
                    {"$set": {"remaining_kg": new_remaining}}
                )
                remaining_needed = 0
            else:
                # Use all remaining material from this heat
                remaining_needed -= heat["remaining_kg"]
                await db.heats.update_one(
                    {"id": heat["id"]},
                    {"$set": {"remaining_kg": 0}}
                )
        
        # Convert date to string for MongoDB storage
        production_dict = production_obj.dict()
        if isinstance(production_dict['date'], date):
            production_dict['date'] = production_dict['date'].isoformat()
        
        # Save production record
        await db.productions.insert_one(production_dict)
        return production_obj
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/productions", response_model=List[Production])
async def get_productions():
    """Get all production records"""
    try:
        productions = await db.productions.find().sort("date", -1).to_list(1000)
        return [Production(**production) for production in productions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/inventory", response_model=List[InventoryStatus])
async def get_inventory_status():
    """Get current inventory status for both steel types"""
    try:
        inventory_status = []
        
        for steel_type in ["20.64mm", "23mm"]:
            # Get all heats for this steel type
            heats = await db.heats.find({"steel_type": steel_type}).to_list(1000)
            
            # Calculate totals
            total_received = sum(heat["quantity_kg"] for heat in heats)
            current_stock = sum(heat["remaining_kg"] for heat in heats)
            total_consumed = total_received - current_stock
            
            # Prepare heat details
            heat_details = []
            for heat in heats:
                heat_details.append({
                    "heat_number": heat["heat_number"],
                    "original_quantity": heat["quantity_kg"],
                    "remaining_quantity": heat["remaining_kg"],
                    "date_received": heat["date_received"].isoformat() if isinstance(heat["date_received"], date) else heat["date_received"]
                })
            
            # Determine low stock alert (less than 100kg)
            low_stock = current_stock < 100
            
            # Generate reorder recommendation
            if current_stock < 50:
                reorder_msg = "URGENT: Order immediately!"
            elif current_stock < 100:
                reorder_msg = "LOW STOCK: Consider ordering soon"
            elif current_stock < 200:
                reorder_msg = "MEDIUM STOCK: Monitor closely"
            else:
                reorder_msg = "GOOD STOCK: No immediate action needed"
            
            inventory_status.append(InventoryStatus(
                steel_type=steel_type,
                total_received_kg=total_received,
                total_consumed_kg=total_consumed,
                current_stock_kg=current_stock,
                heats=heat_details,
                low_stock_alert=low_stock,
                reorder_recommendation=reorder_msg
            ))
        
        return inventory_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/dashboard", response_model=DashboardData)
async def get_dashboard_data():
    """Get complete dashboard data"""
    try:
        # Get inventory status
        inventory_status = await get_inventory_status()
        
        # Get recent productions (last 10)
        recent_productions = await db.productions.find().sort("date", -1).limit(10).to_list(10)
        recent_productions = [Production(**prod) for prod in recent_productions]
        
        # Get recent heats (last 10)
        recent_heats = await db.heats.find().sort("date_received", -1).limit(10).to_list(10)
        recent_heats = [Heat(**heat) for heat in recent_heats]
        
        # Calculate total production
        all_productions = await db.productions.find().to_list(1000)
        total_mkiii = sum(prod["quantity_produced"] for prod in all_productions if prod["product_type"] == "MK-III")
        total_mkv = sum(prod["quantity_produced"] for prod in all_productions if prod["product_type"] == "MK-V")
        
        return DashboardData(
            inventory_status=inventory_status,
            recent_productions=recent_productions,
            recent_heats=recent_heats,
            total_production_mkiii=total_mkiii,
            total_production_mkv=total_mkv
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()