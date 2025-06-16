import pyvolt
from pyvolt.ext import commands
from tools.db_funcs import *
from bot import Toko
from tools.permission_flags import PERMISSION_FLAGS  # move flags to separate file

class Logging(commands.Gear):
    def __init__(self, bot: Toko):
        self.bot = bot
        self.log_cache = {}

    def get_avatar_url(self, user: pyvolt.User) -> str:
        if user.avatar:
            return user.avatar.url()
        return self.bot.http.url_for(pyvolt.routes.USERS_GET_DEFAULT_AVATAR.compile(user_id=user.id))

    async def get_cached_log_channel(self, server_id: str, category: str, event_type: str):
        if server_id not in self.log_cache:
            self.log_cache[server_id] = {}
        if category not in self.log_cache[server_id]:
            self.log_cache[server_id][category] = {}
        if event_type not in self.log_cache[server_id][category]:
            await ensure_logging_config(server_id, None)
            if await should_log(server_id, category, event_type):
                config = await get_log_channel(server_id, category, event_type)
                self.log_cache[server_id][category][event_type] = config
            else:
                self.log_cache[server_id][category][event_type] = None
        return self.log_cache[server_id][category][event_type]

    async def send_log_embed(self, channel_id: str, embed: pyvolt.SendableEmbed):
        try:
            channel = await self.bot.fetch_channel(channel_id)
            if channel:
                await channel.send(embeds=[embed])
        except Exception:
            pass

    def decode_permissions(self, bitmask: int) -> str:
        return ", ".join(name for bit, name in PERMISSION_FLAGS.items() if bitmask & bit) or "None"

    @commands.Gear.listener()
    async def on_message_delete(self, m: pyvolt.MessageDeleteEvent):
        message = m.message
        author = message.author
        server = message.server
        if not server or author.bot:
            return

        log_config = await self.get_cached_log_channel(server.id, "message_logs", "message_delete")
        if not log_config or not log_config.get("channel_id"):
            return

        avatar_url = self.get_avatar_url(author)
        timestamp = getattr(message, "created_at", None)
        content = message.content or "[No content]"

        attachment_links = ""
        if message.attachments:
            attachment_links = "\n".join(f"[{a.filename}]({a.url()})" for a in message.attachments)

        embed_description = (
            f"**Channel:** {message.channel.mention}\n"
            f"**Author:** {author.mention} (`{author.id}`)\n"
        )

        if timestamp:
            embed_description += f"**Time:** <t:{int(timestamp.timestamp())}:F>\n\n"
        else:
            embed_description += "**Time:** Unknown\n\n"

        embed_description += (
            f"**Content:**\n```text\n{content}\n```\n"
            f"`Message ID:` `{message.id}`"
        )

        if attachment_links:
            embed_description += f"\n\n**Attachments:**\n{attachment_links}"

        embed = pyvolt.SendableEmbed(
            title="🗑️ Message Deleted",
            description=embed_description,
            color="#e74c3c",
            icon_url=avatar_url
        )

        await self.send_log_embed(log_config["channel_id"], embed)


    @commands.Gear.listener()
    async def on_message_edit(self, m: pyvolt.MessageUpdateEvent):
        before, after = m.before, m.after
        message = m.message
        author = before.author
        server = message.server
        if not server or author.bot:
            return

        log_config = await self.get_cached_log_channel(server.id, "message_logs", "message_edit")
        if not log_config or not log_config.get("channel_id"):
            return

        embed = pyvolt.SendableEmbed(
            title="✏️ Message Edited",
            description=(
                f"**Channel:** {message.channel.mention}\n"
                f"**Author:** {author.mention} (`{author.id}`)\n"
                f"[Jump to Message](https://app.revolt.chat/server/{server.id}/channel/{message.channel.id}/{message.id})\n\n"
                f"**Original Content:**\n```text\n{before.content or '[No content]'}\n```\n"
                f"**New Content:**\n```text\n{after.content or '[No content]'}\n```\n"
                f"`Message ID:` `{message.id}`"
            ),
            color="#f1c40f",
            icon_url=self.get_avatar_url(author)
        )
        await self.send_log_embed(log_config["channel_id"], embed)

    @commands.Gear.listener()
    async def on_server_role_create_or_update(self, e: pyvolt.RawServerRoleUpdateEvent):
        server = e.server
        if not server:
            return

        is_creation = e.old_role is None and e.new_role is not None
        event_type = "role_create" if is_creation else "role_update"
        log_config = await self.get_cached_log_channel(server.id, "role_logs", event_type)
        if not log_config or not log_config.get("channel_id"):
            return

        icon_url = server.icon.url() if server.icon else None
        role = e.new_role

        if is_creation:
            embed = pyvolt.SendableEmbed(
                title="🆕 Role Created",
                description=f"**Role:** {role.name} (`{role.id}`)",
                color="#2ecc71",
                icon_url=icon_url
            )
        else:
            old, new = e.old_role, e.new_role
            changes = []

            def diff(attr, label=None):
                before = getattr(old, attr, None)
                after = getattr(new, attr, None)

                if attr == "permissions":
                    allow_before = self.decode_permissions(before.allow.value if before and before.allow else 0)
                    allow_after = self.decode_permissions(after.allow.value if after and after.allow else 0)
                    deny_before = self.decode_permissions(before.deny.value if before and before.deny else 0)
                    deny_after = self.decode_permissions(after.deny.value if after and after.deny else 0)

                    if allow_before != allow_after:
                        changes.append(f"**Permissions (Allow):** `{allow_before}` → `{allow_after}`")
                    if deny_before != deny_after:
                        changes.append(f"**Permissions (Deny):** `{deny_before}` → `{deny_after}`")
                    return

                if before != after:
                    label = label or attr.capitalize()
                    before_str = before if before is not None else "None"
                    after_str = after if after is not None else "None"
                    changes.append(f"**{label}:** `{before_str}` → `{after_str}`")

            for field in ["name", "color", "mentionable", "hoist", "permissions", "rank"]:
                diff(field)

            if not changes:
                return

            embed = pyvolt.SendableEmbed(
                title="✏️ Role Updated",
                description=(
                    f"**Role:** {new.name} (`{new.id}`)\n\n"
                    f"**Changes:**\n" + "\n".join(changes)
                ),
                color="#f1c40f",
                icon_url=icon_url
            )

        await self.send_log_embed(log_config["channel_id"], embed)
    
    @commands.Gear.listener()
    async def on_server_role_delete(self, e: pyvolt.ServerRoleDeleteEvent):
        server = e.server
        role = e.role

        if not server or not role:
            return

        log_config = await self.get_cached_log_channel(server.id, "role_logs", "role_delete")
        if not log_config or not log_config.get("channel_id"):
            return

        icon_url = server.icon.url() if server.icon else None

        embed = pyvolt.SendableEmbed(
            title="❌ Role Deleted",
            description=f"**Role:** {role.name} (`{role.id}`)",
            color="#e74c3c",
            icon_url=icon_url
        )

        await self.send_log_embed(log_config["channel_id"], embed)
    
    @commands.Gear.listener()
    async def on_server_channel_create(self, e: pyvolt.ChannelCreateEvent):
        server = e.server
        channel = e.channel
        if not server or not channel:
            return

        log_config = await self.get_cached_log_channel(server.id, "channel_logs", "channel_create")
        if not log_config or not log_config.get("channel_id"):
            return

        icon_url = server.icon.url() if server.icon else None

        embed = pyvolt.SendableEmbed(
            title="🆕 Channel Created",
            description=(
                f"**Channel:** {channel.mention if hasattr(channel, 'mention') else channel.name} (`{channel.id}`)\n"
                f"**Type:** `{getattr(channel, 'type', 'Unknown')}`"
            ),
            color="#2ecc71",
            icon_url=icon_url
        )
        await self.send_log_embed(log_config["channel_id"], embed)

    @commands.Gear.listener()
    async def on_server_channel_update(self, e: pyvolt.ChannelUpdateEvent):
        server = e.server
        old = e.old_channel
        new = e.new_channel
        if not server or not old or not new:
            return

        log_config = await self.get_cached_log_channel(server.id, "channel_logs", "channel_update")
        if not log_config or not log_config.get("channel_id"):
            return

        icon_url = server.icon.url() if server.icon else None
        changes = []

        def diff(attr, label=None):
            before = getattr(old, attr, None)
            after = getattr(new, attr, None)
            if before != after:
                label = label or attr.capitalize()
                before_str = before if before is not None else "None"
                after_str = after if after is not None else "None"
                changes.append(f"**{label}:** `{before_str}` → `{after_str}`")

        for field in ["name", "description", "type"]:
            diff(field)

        if not changes:
            return

        embed = pyvolt.SendableEmbed(
            title="✏️ Channel Updated",
            description=(
                f"**Channel:** {new.mention if hasattr(new, 'mention') else new.name} (`{new.id}`)\n\n"
                f"**Changes:**\n" + "\n".join(changes)
            ),
            color="#f1c40f",
            icon_url=icon_url
        )
        await self.send_log_embed(log_config["channel_id"], embed)

    @commands.Gear.listener()
    async def on_server_channel_delete(self, e: pyvolt.ChannelDeleteEvent):
        server = e.server
        channel = e.channel
        if not server or not channel:
            return

        log_config = await self.get_cached_log_channel(server.id, "channel_logs", "channel_delete")
        if not log_config or not log_config.get("channel_id"):
            return

        icon_url = server.icon.url() if server.icon else None

        embed = pyvolt.SendableEmbed(
            title="❌ Channel Deleted",
            description=f"**Channel:** {channel.name} (`{channel.id}`)",
            color="#e74c3c",
            icon_url=icon_url
        )
        await self.send_log_embed(log_config["channel_id"], embed)

async def setup(bot: Toko) -> None:
    await bot.add_gear(Logging(bot))