# LuxeWin FastAPI Backend Overview

## Architecture Overview

### 1. Project Structure
```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   ├── dependencies/
│   │   └── middleware/
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── models/
│   │   ├── domain/
│   │   └── schemas/
│   ├── services/
│   │   ├── raffle.py
│   │   ├── user.py
│   │   └── notification.py
│   └── utils/
├── tests/
└── alembic/
```

### 2. Core Components

#### API Routes
```python
# Example route structure
@router.get("/raffles/", response_model=List[RaffleSchema])
async def list_raffles(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=100),
    current_user: User = Depends(get_current_user)
):
    """List active raffles with pagination"""
    return await raffle_service.get_raffles(skip=skip, limit=limit)
```

#### Data Models
```python
# Pydantic models
class RaffleCreate(BaseModel):
    title: str
    description: str
    ticket_price: Decimal
    total_tickets: int
    end_date: datetime

    class Config:
        schema_extra = {
            "example": {
                "title": "Luxury Watch Raffle",
                "description": "Win a premium timepiece",
                "ticket_price": "10.00",
                "total_tickets": 1000
            }
        }
```

### 3. Key Features

#### Authentication
```python
from fastapi_security import OAuth2PasswordBearer
from app.core.security import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> User:
    return await verify_token(token)
```

#### Request Validation
```python
class TicketPurchase(BaseModel):
    raffle_id: UUID4
    quantity: conint(gt=0, le=100)
    payment_method: PaymentMethod

    @validator('quantity')
    def validate_quantity(cls, v, values):
        # Custom validation logic
        return v
```

#### Error Handling
```python
from fastapi import HTTPException
from app.core.exceptions import CustomException

@router.get("/raffle/{raffle_id}")
async def get_raffle(raffle_id: str):
    try:
        raffle = await raffle_service.get_raffle(raffle_id)
        if not raffle:
            raise HTTPException(404, "Raffle not found")
        return raffle
    except CustomException as e:
        raise HTTPException(400, str(e))
```

### 4. Services Integration

#### Supabase Integration
```python
from app.services.supabase import supabase_client

async def get_user_profile(user_id: str):
    return await supabase_client.from_('profiles')\
        .select('*')\
        .eq('id', user_id)\
        .single()\
        .execute()
```

#### Stripe Integration
```python
from app.services.payment import stripe

async def process_payment(
    amount: int,
    currency: str,
    payment_method: str
):
    try:
        return await stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            confirm=True
        )
    except stripe.error.StripeError as e:
        raise PaymentError(str(e))
```

### 5. Performance Optimizations

#### Caching
```python
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

@router.get("/popular-raffles")
@cache(expire=300)  # Cache for 5 minutes
async def get_popular_raffles():
    return await raffle_service.get_popular_raffles()
```

#### Background Tasks
```python
from fastapi import BackgroundTasks

@router.post("/purchase")
async def purchase_tickets(
    purchase: TicketPurchase,
    background_tasks: BackgroundTasks
):
    # Process purchase
    background_tasks.add_task(
        send_confirmation_email,
        purchase.user_email
    )
    return {"status": "success"}
```

### 6. Testing Strategy

#### Unit Tests
```python
async def test_create_raffle():
    raffle_data = {
        "title": "Test Raffle",
        "ticket_price": "10.00",
        "total_tickets": 100
    }
    response = await client.post("/raffles/", json=raffle_data)
    assert response.status_code == 200
    assert response.json()["title"] == raffle_data["title"]
```

#### Integration Tests
```python
async def test_purchase_flow():
    # Create raffle
    raffle = await create_test_raffle()
    
    # Purchase tickets
    purchase_data = {
        "raffle_id": raffle["id"],
        "quantity": 1
    }
    response = await client.post(
        "/purchase/",
        json=purchase_data,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
```

### 7. Deployment Configuration

#### Docker Setup
```dockerfile
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./app /app/app
```

#### Environment Variables
```env
DATABASE_URL=postgresql://user:pass@localhost/db
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
STRIPE_SECRET_KEY=your-stripe-key
NOVU_API_KEY=your-novu-key
```