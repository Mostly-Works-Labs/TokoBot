from pyvolt.ext import commands
from utils.economy import *
from tools.db_funcs import *
from bot import Toko
from pathlib import Path
from datetime import datetime, timedelta


import pyvolt
import random
import json
import time
import textwrap

COIN_EMOJI = ":01JXTVCNYB53TC48R7JJ14SMMB:"
COOLDOWN_SECONDS = 10
user_cooldowns: dict[str, float] = {}

ROULETTE_COLORS = {
    0: "green",
    1: "red", 2: "black", 3: "red", 4: "black", 5: "red", 6: "black",
    7: "red", 8: "black", 9: "red", 10: "black", 11: "black", 12: "red",
    13: "black", 14: "red", 15: "black", 16: "red", 17: "black", 18: "red",
    19: "red", 20: "black", 21: "red", 22: "black", 23: "red", 24: "black",
    25: "red", 26: "black", 27: "red", 28: "black", 29: "black", 30: "red",
    31: "black", 32: "red", 33: "black", 34: "red", 35: "black", 36: "red"
}

JOBS_PATH = Path(__file__).parent / ".." / "data" / "jobs.json"
JOBS_PATH = JOBS_PATH.resolve()

with open(JOBS_PATH, "r") as f:
    JOBS = json.load(f)

FAILURE_MESSAGES = [
    "You lied on your résumé and got caught.",
    "You showed up late to the interview and spilled coffee on your boss.",
    "You forgot your own name during the interview.",
    "They said you were 'too creative' for the janitor role.",
    "The AI doing interviews rejected you instantly.",
    "You called the boss 'mom' — yeah..."
]

SUCCESS_MESSAGES = [
    "The boss felt bad and hired you anyway.",
    "You barely made it, but hey, a job's a job!",
    "You impressed them by juggling three staplers.",
    "They liked your meme portfolio.",
    "You bribed the interviewer with cookies and it worked."
]

RARITY_WEIGHTS = {
    "common": 10,
    "uncommon": 5,
    "rare": 2,
    "legendary": 1,
    "silly": 3,
    "risky": 2
}

class Economy(commands.Gear):
    def __init__(self, bot: Toko):
        self.bot = bot

    def get_avatar_url(self, user: pyvolt.User) -> str:
        if user.avatar:
            return user.avatar.url()
        return self.bot.http.url_for(
            pyvolt.routes.USERS_GET_DEFAULT_AVATAR.compile(user_id=user.id)
        )

    @commands.server_only()
    @commands.command(name="balance", aliases=["bal"])
    async def balance_command(self, ctx: commands.Context):
        user_id = ctx.author.id
        server_id = ctx.server.id
        await ensure_user(server_id, user_id)
        balance = await get_balance(server_id, user_id)
        total = balance["wallet"] + balance["bank"]

        embed = pyvolt.SendableEmbed(
            title=f"{ctx.author.name}",
            description=textwrap.dedent(f"""
                | Cash: | Bank: | Total: |
                |------:|------:|-------:|
                | {COIN_EMOJI} {balance['wallet']} | {COIN_EMOJI} {balance['bank']} | {COIN_EMOJI} {total} |
            """).strip(),
            color="#DDF3FF",
            icon_url=self.get_avatar_url(ctx.author)
        )
        await ctx.message.reply(embeds=[embed], silent=True)

    @commands.server_only()
    @commands.command(name="coinflip", aliases=["cf"])
    async def coinflip_command(self, ctx: commands.Context, amount: str = "100"):
        user_id = ctx.author.id
        server_id = ctx.server.id
        now = time.time()
        last_used = user_cooldowns.get(user_id, 0)
        if now - last_used < COOLDOWN_SECONDS:
            wait = round(COOLDOWN_SECONDS - (now - last_used))
            return await ctx.message.reply(f"🕒 Try again in `{wait}s`.", silent=True)

        await ensure_user(server_id, user_id)
        balance = await get_balance(server_id, user_id)
        if amount.lower() == "all":
            amount = balance["wallet"]
        elif amount.isdigit():
            amount = int(amount)
        else:
            return await ctx.message.reply("❌ Invalid amount. Use a number or `all`.", silent=True)

        if amount <= 0 or balance["wallet"] < amount:
            return await ctx.message.reply("❌ Invalid or insufficient amount.", silent=True)

        win = random.choices([True, False], weights=[35, 65])[0]
        if win:
            await add_wallet(server_id, user_id, amount)
            result = f"🎉 **You won** {COIN_EMOJI} `{amount}`!"
            color = "#A162FF"
        else:
            await add_wallet(server_id, user_id, -amount)
            result = f"💀 **You lost** {COIN_EMOJI} `{amount}`."
            color = "#FF6B6B"

        user_cooldowns[user_id] = now
        embed = pyvolt.SendableEmbed(
            title="🎲 Coin Flip",
            description=result,
            color=color,
            icon_url=self.get_avatar_url(ctx.author)
        )
        await ctx.message.reply(embeds=[embed], silent=True)

    @commands.server_only()
    @commands.command(name="deposit", aliases=["dep"])
    async def deposit_command(self, ctx: commands.Context, amount: str = "0"):
        user_id = ctx.author.id
        server_id = ctx.server.id
        await ensure_user(server_id, user_id)
        balance = await get_balance(server_id, user_id)

        if amount.lower() == "all":
            amount = balance["wallet"]
        elif amount.isdigit():
            amount = int(amount)
        else:
            return await ctx.message.reply("❌ Invalid amount.", silent=True)

        if amount <= 0 or balance["wallet"] < amount:
            return await ctx.message.reply("❌ Invalid or insufficient amount.", silent=True)

        await deposit(server_id, user_id, amount)
        await ctx.message.reply(
            embeds=[pyvolt.SendableEmbed(
                title="🏦 Deposit",
                description=f"Deposited {COIN_EMOJI} `{amount}` to your bank.",
                color="#00B894",
                icon_url=self.get_avatar_url(ctx.author)
            )], silent=True
        )

    @commands.server_only()
    @commands.command(name="withdraw", aliases=["wd"])
    async def withdraw_command(self, ctx: commands.Context, amount: str = "0"):
        user_id = ctx.author.id
        server_id = ctx.server.id
        await ensure_user(server_id, user_id)
        balance = await get_balance(server_id, user_id)

        if amount.lower() == "all":
            amount = balance["bank"]
        elif amount.isdigit():
            amount = int(amount)
        else:
            return await ctx.message.reply("❌ Invalid amount.", silent=True)

        if amount <= 0 or balance["bank"] < amount:
            return await ctx.message.reply("❌ Invalid or insufficient amount.", silent=True)

        await withdraw(server_id, user_id, amount)
        await ctx.message.reply(
            embeds=[pyvolt.SendableEmbed(
                title="💸 Withdraw",
                description=f"Withdrew {COIN_EMOJI} `{amount}` from your bank.",
                color="#FAB005",
                icon_url=self.get_avatar_url(ctx.author)
            )], silent=True
        )

    @commands.server_only()
    @commands.command(name="daily")
    async def daily_command(self, ctx: commands.Context):
        user_id = ctx.author.id
        server_id = ctx.server.id
        await ensure_user(server_id, user_id)

        if not await can_claim_daily(server_id, user_id):
            return await ctx.message.reply("🕒 Already claimed today. Come back in 24h!", silent=True)

        await claim_daily(server_id, user_id, amount=500)
        await ctx.message.reply(
            embeds=[pyvolt.SendableEmbed(
                title="🎁 Daily Reward",
                description=f"You claimed your daily {COIN_EMOJI} `500`!",
                color="#74C0FC",
                icon_url=self.get_avatar_url(ctx.author)
            )], silent=True
        )

    @commands.server_only()
    @commands.command(name="roulette")
    async def roulette_command(self, ctx: commands.Context, bet: str, amount: str = "100"):
        JOB_COOLDOWN_HOURS = 24
        user_id = ctx.author.id
        server_id = ctx.server.id
        await ensure_user(server_id, user_id)
        balance = await get_balance(server_id, user_id)

        if amount.lower() == "all":
            amount = balance["wallet"]
        elif amount.isdigit():
            amount = int(amount)
        else:
            return await ctx.message.reply("❌ Invalid amount.", silent=True)

        if amount <= 0 or balance["wallet"] < amount:
            return await ctx.message.reply("❌ Invalid or insufficient amount.", silent=True)

        result = random.randint(0, 36)
        color = ROULETTE_COLORS[result]
        win = False
        payout = 0
        bet_type = bet.lower()

        if bet_type in ["even", "odd"]:
            if result != 0 and ((result % 2 == 0 and bet_type == "even") or (result % 2 == 1 and bet_type == "odd")):
                win = True
                payout = amount * 2
        elif bet_type in ["red", "black"]:
            if color == bet_type:
                win = True
                payout = amount * 2
        elif bet_type.isdigit() and 0 <= int(bet_type) <= 36:
            if int(bet_type) == result:
                win = True
                payout = amount * 35
        else:
            return await ctx.message.reply("❌ Bet must be: red, black, even, odd or 0–36", silent=True)

        if win:
            await add_wallet(server_id, user_id, payout)
            msg = f"🎉 You **won** {COIN_EMOJI} `{payout}`!"
            color_hex = "#2ECC71"
        else:
            await add_wallet(server_id, user_id, -amount)
            msg = f"💀 You **lost** {COIN_EMOJI} `{amount}`"
            color_hex = "#E74C3C"

        await ctx.message.reply(embeds=[pyvolt.SendableEmbed(
            title="🎡 Roulette Result",
            description=f"**You bet on:** `{bet}`\n**Result:** `{result}` ({color})\n\n{msg}",
            color=color_hex,
            icon_url=self.get_avatar_url(ctx.author)
        )], silent=True)

    @commands.server_only()
    @commands.command(name="jobs")
    async def jobs_list_command(self, ctx: commands.Context):
        """Show all available jobs (paginated)."""
        jobs_per_page = 5
        pages = [
            JOBS[i:i + jobs_per_page]
            for i in range(0, len(JOBS), jobs_per_page)
        ]
        total_pages = len(pages)
        page = 0

        def make_embed(page_idx):
            job_lines = [
                f"**{job['name']}** — Income: {COIN_EMOJI} `{job['min_income']} - {job['max_income']}` | Rarity: `{job['rarity']}`"
                for job in pages[page_idx]
            ]
            return pyvolt.SendableEmbed(
                title=f"📋 Available Jobs (Page {page_idx + 1}/{total_pages})",
                description="\n".join(job_lines),
                color="#98C9FF"
            )

        embed = make_embed(page)
        msg = await ctx.message.reply(embeds=[embed], silent=True)

        if total_pages == 1:
            return

        await msg.react("◀️")
        await msg.react("▶️")

        def check(reaction, user):
            return (
                reaction.message.id == msg.id
                and user.id == ctx.author.id
                and str(reaction.emoji) in ["◀️", "▶️"]
            )

        while True:
            try:
                reaction, user = await ctx.bot.wait_for("reaction_add", timeout=30.0, check=check)
            except Exception:
                break

            if str(reaction.emoji) == "▶️" and page < total_pages - 1:
                page += 1
                await msg.edit(embeds=[make_embed(page)])
            elif str(reaction.emoji) == "◀️" and page > 0:
                page -= 1
                await msg.edit(embeds=[make_embed(page)])

            try:
                await msg.remove_reaction(reaction.emoji, user)
            except Exception:
                pass

    @commands.server_only()
    @commands.command(name="job")
    async def job_command(self, ctx: commands.Context, *, job_name: str = None):
        """Apply for a specific job (use .jobs to view list)."""
        JOB_COOLDOWN_HOURS = 24
        user_id = ctx.author.id
        server_id = ctx.server.id

        now = time.time()
        if server_id not in user_cooldowns:
            user_cooldowns[server_id] = {}
        last_used = user_cooldowns[server_id].get(user_id, 0)

        if now - last_used < JOB_COOLDOWN_HOURS * 3600:
            hours_left = round((JOB_COOLDOWN_HOURS * 3600 - (now - last_used)) / 3600, 1)
            return await ctx.message.reply(
                f"🕒 You already applied for a job recently. Try again in `{hours_left}h`.", silent=True
            )

        await ensure_user(server_id, user_id)

        if job_name is None:
            await self.jobs_list_command(ctx)
            return

        job_name = job_name.lower()
        selected_job = next((job for job in JOBS if job["name"].lower() == job_name), None)

        if not selected_job:
            return await ctx.message.reply("❌ That job doesn't exist. Try `.jobs` to see options.", silent=True)

        success_chance = RARITY_WEIGHTS.get(selected_job["rarity"], 1) / 10
        success = random.random() < success_chance

        if success:
            pay = random.randint(selected_job["min_income"], selected_job["max_income"])
            await add_wallet(server_id, user_id, pay)
            msg = random.choice(SUCCESS_MESSAGES) + f" You got the job as **{selected_job['name']}** and earned {COIN_EMOJI} `{pay}`!"
            color = "#4CAF50"
        else:
            msg = random.choice(FAILURE_MESSAGES)
            color = "#F44336"

        user_cooldowns[server_id][user_id] = now

        embed = pyvolt.SendableEmbed(
            title="💼 Job Application",
            description=msg,
            color=color,
            icon_url=self.get_avatar_url(ctx.author)
        )

        await ctx.message.reply(embeds=[embed], silent=True)

async def setup(bot: Toko) -> None:
    await bot.add_gear(Economy(bot))
