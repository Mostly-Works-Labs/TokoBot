from models.ServerEconomy import ServerEconomy, UserEconomy
from datetime import datetime, timedelta
import pytz

async def get_or_create_server_economy(server_id: str) -> ServerEconomy:
    """Retrieve or create the ServerEconomy document for a server."""
    econ = await ServerEconomy.get(server_id)
    if not econ:
        econ = ServerEconomy(_id=server_id)
        await econ.insert()
    return econ

async def ensure_user(server_id: str, user_id: str):
    """Ensure a user exists in the economy. Starts with 0 wallet and 300 in bank."""
    econ = await get_or_create_server_economy(server_id)
    if user_id not in econ.users:
        econ.users[user_id] = UserEconomy(wallet=0, bank=300, job=None)
        await econ.save()

async def get_balance(server_id: str, user_id: str) -> dict:
    """Return the wallet and bank balance of a user in a server."""
    await ensure_user(server_id, user_id)
    econ = await ServerEconomy.get(server_id)
    user = econ.users[user_id]
    return {"wallet": user.wallet, "bank": user.bank}

async def add_wallet(server_id: str, user_id: str, amount: int):
    """Add coins to a user’s wallet in a server."""
    await ensure_user(server_id, user_id)
    econ = await ServerEconomy.get(server_id)
    econ.users[user_id].wallet += amount
    await econ.save()

async def deposit(server_id: str, user_id: str, amount: int) -> bool:
    """Move coins from wallet to bank. Returns True if successful."""
    await ensure_user(server_id, user_id)
    econ = await ServerEconomy.get(server_id)
    user = econ.users[user_id]
    if user.wallet >= amount:
        user.wallet -= amount
        user.bank += amount
        await econ.save()
        return True
    return False

async def withdraw(server_id: str, user_id: str, amount: int) -> bool:
    """Move coins from bank to wallet. Returns True if successful."""
    await ensure_user(server_id, user_id)
    econ = await ServerEconomy.get(server_id)
    user = econ.users[user_id]
    if user.bank >= amount:
        user.bank -= amount
        user.wallet += amount
        await econ.save()
        return True
    return False

async def can_claim_daily(server_id: str, user_id: str) -> bool:
    """Check if a user can claim daily coins (once every 24h)."""
    await ensure_user(server_id, user_id)
    econ = await ServerEconomy.get(server_id)
    user = econ.users[user_id]
    if not user.last_daily:
        return True
    last = datetime.fromisoformat(user.last_daily)
    now = datetime.now(pytz.utc)
    return (now - last) >= timedelta(hours=24)

async def claim_daily(server_id: str, user_id: str, amount: int = 500) -> bool:
    """Claim the daily reward. Returns True if claimed, False if on cooldown."""
    if not await can_claim_daily(server_id, user_id):
        return False
    econ = await ServerEconomy.get(server_id)
    user = econ.users[user_id]
    user.wallet += amount
    user.last_daily = datetime.now(pytz.utc).isoformat()
    await econ.save()
    return True

async def update_job(server_id: str, user_id: str, job_name: str):
    econ = await ServerEconomy.get(server_id)
    econ.users[user_id].job = job_name
    await econ.save()
