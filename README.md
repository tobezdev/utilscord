<div align="center">

# Utilscord

Moderate your server, render LaTeX, and more

[Invite Utilscord](https://discord.com/oauth2/authorize?client_id=1546268629648150528) · [Commands](#commands) · [Permissions](#permissions) · [Support](#support) · [Privacy](#privacy) · [Terms](#terms)

</div>

---

## Invite

[**Add Utilscord to your server →**](https://discord.com/oauth2/authorize?client_id=1546268629648150528)

Utilscord is provided as a hosted bot. Self-hosting is not available or supported; use the official invite above to add it to your server.

Once installed, type `/` in Discord and select Utilscord to browse its commands. Give the bot the permissions needed for the features you use, and position its role above members it should moderate.

`/ping`, `/klipy`, and `/latex render` support both server and user installations, with command contexts enabled for servers, bot DMs, and private channels. Moderation commands and `/permissions` require a server installation and can only be used in servers.

## What you can do

- **Moderate:** kick, ban, unban, timeout, and remove timeouts with permission and role checks.
- **Clean up:** remove a chosen number of messages, or clear messages back to a verified message ID.
- **Slow things down:** set a text channel's message cooldown.
- **Inspect permissions:** privately check a member's allowed and denied permissions in the current channel.
- **Find GIFs:** search KLIPY and share the top match with attribution.
- **Render maths:** turn LaTeX into a PNG or SVG using an interactive form.
- **Check connectivity:** see the bot's gateway latency with `/ping`.

Moderation confirmations and permission reports are private to the person running the command. LaTeX results, GIF results, and ping replies are posted as ordinary Discord responses visible to people with access to the conversation. The bot uses Discord Components V2 for its responses and image presentation.

## Commands

Arguments in `<angle brackets>` are required; arguments in `[square brackets]` are optional. Enter values through Discord's slash-command fields, without the brackets.

### Moderation

All moderation commands work in servers only. Every command accepts an optional `reason` of up to **400 characters**, defaulting to `No reason provided.` The bot sends the moderator's display name, username, user ID, and reason to Discord's audit log; the combined audit reason is limited to 512 characters.

| Command | What it does |
| --- | --- |
| `/kick <member> [reason]` | Removes a current member from the server. |
| `/mute <member> <duration> [reason]` | Applies a Discord timeout. |
| `/unmute <member> [reason]` | Removes a member's timeout. |
| `/ban <member> [delete_days] [reason]` | Bans a current member. `delete_days` is an integer from **0–7**, default **0**, specifying how much recent message history to delete. |
| `/unban <user_id> [reason]` | Removes a ban using the user's numeric Discord ID. The user does not need to be in the server. |
| `/purge [amount] [until] [reason]` | Deletes messages in the current text channel or thread. Supply **exactly one** of `amount` or `until`; see below. |
| `/slowmode <seconds> [reason]` | Sets the current text channel's cooldown to **0–21,600 seconds**. Use **0** to disable it. |

#### Timeout durations

`/mute` accepts whole-number durations using `s` (seconds), `m` (minutes), `h` (hours), `d` (days), and `w` (weeks). Combine units if needed; letters are case-insensitive and spaces are accepted between parts.

| Duration | Meaning |
| --- | --- |
| `30s` | 30 seconds |
| `10m` | 10 minutes |
| `2h` | 2 hours |
| `5d` | 5 days |
| `2w` | 2 weeks |
| `1d12h` | 1 day and 12 hours |

The total must be between **1 second and 28 days**. Plain numbers, negative values, and fractions such as `1.5d` are not accepted. Use `1d12h` instead. The duration field allows up to 100 characters.

```text
/mute member:@Member duration:2w reason:Repeated rule violations
/unmute member:@Member reason:Appeal accepted
```

Timeouts affect communication; `/mute` is not a voice-channel mute command. Administrators cannot be timed out.

#### Purging messages

| Mode | Example | Result |
| --- | --- | --- |
| By count | `/purge amount:25` | Removes up to 25 recent messages. `amount` must be **1–1,000**. |
| Back to a message | `/purge until:123456789012345678` | Removes messages newer than that message, keeping the target. |
| Including the target | `/purge until:!123456789012345678` | Removes messages newer than that message and the target itself. |

Replace the example ID with a real message ID from the current channel. The bot fetches and verifies the target before deleting anything. If it is missing or belongs to another channel, deletion does not begin. The target must have been sent before the command was invoked.

Both modes stop at the time the command was invoked, preserving messages sent afterward. The `until` mode has **no 1,000-message cap**: it covers the whole range back to the target. Deletion cannot be undone by Utilscord, and an interrupted purge may have already removed some messages.

### Utilities

| Command | What it does |
| --- | --- |
| `/klipy` | Opens a **Search KLIPY** form and posts the top matching GIF with attribution. Modal dropdown filter: `high`, `medium`, `low` (default), or `off`. Cooldown: once per user every **10 seconds**. |
| `/permissions <user>` | Privately lists a server member's allowed and denied/unavailable permissions in the current channel. Server-only; no moderation permission is required. |
| `/ping` | Reports the bot's gateway latency in milliseconds. Cooldown: once per user every **5 minutes**. |
| `/latex render` | Opens a form to render LaTeX and posts the image with a **View in browser** button. Cooldown: once per user every **15 minutes**. |

KLIPY searches accept up to **200 characters** and send your search text and selected filter to KLIPY. The result is posted in the conversation with a **Powered by KLIPY** credit, plus username, source, and content-description source details when returned by KLIPY. `high` is the strongest maturity filter; `off` disables the request-level filter. The operator must configure `KLIPY_API_KEY` and obtain production access through the [KLIPY Partner Panel](https://partner.klipy.com/). The cog is loaded automatically.

The `/permissions` report combines `@everyone`, assigned roles, and applicable channel and member overrides. It accounts for server-owner and Administrator bypasses and active timeouts. In a thread, it reports the parent channel's permissions; private-thread membership and archived or locked state can further restrict access. The report does not change permissions or ping the selected member.

The LaTeX form contains:

| Field | Required? | Options and defaults |
| --- | --- | --- |
| LaTeX code | Yes | The expression to render. |
| Image width | No | Whole pixels, **1–5,000**; omitted values use the rendering service's default. |
| Image height | No | Whole pixels, **1–5,000**; omitted values use the rendering service's default. |
| Rendering options | No | White text instead of black; disable the transparent background. Both are off by default. |
| File type | Yes | **PNG** by default, or **SVG**. SVG output also includes a PNG preview. |

Your LaTeX source and rendering settings are sent to an external rendering service. See [Privacy](#privacy) for more information.

## Permissions

The bot checks the invoking member's permissions and its own permissions at runtime.

| Commands | Required member permission | Required bot permissions |
| --- | --- | --- |
| `/kick` | Kick Members | Kick Members |
| `/mute`, `/unmute` | Moderate Members | Moderate Members |
| `/ban`, `/unban` | Ban Members | Ban Members |
| `/purge` | Manage Messages in the current channel | Manage Messages, Read Message History, and View Channel in the current channel |
| `/slowmode` | Manage Channels in the current channel | Manage Channels in the current channel |
| `/permissions` | No additional permission beyond access to the application command | No additional permission check; allow the bot to view the channel and reply |

For ordinary use, allow the bot to view the relevant channels and send replies. LaTeX output also needs attachment access. Members need access to application commands in the channel.

For commands targeting a current member, the bot protects the server owner, the invoking moderator, and itself. The target's highest role must be below both the moderator's and the bot's highest roles. The server owner may bypass their own role comparison, but the bot's role limit still applies.

A private confirmation does not make the moderation action invisible: Discord's audit log and the action's effects remain available according to Discord's permissions.

## Support

**Maintained by [Toby / tobezdev](https://github.com/tobezdev).** For support, bugs, or privacy questions, contact [@tobezdev on Discord](https://discord.com/users/969254887621820526) (user ID: `969254887621820526`) or [open a GitHub issue](https://github.com/tobezdev/Utilscord/issues). Issues are public: describe privacy requests without posting personal data or sensitive content.

The source is available at [tobezdev/Utilscord](https://github.com/tobezdev/Utilscord). When reporting a problem, include the command, what you expected, what happened, and any displayed error code. Do not share bot tokens or sensitive moderation reasons. Include the displayed error code so the maintainer can investigate without you posting personal information.

For a moderation appeal, contact the moderators of the server where the action occurred.

## Credits

| Project or platform | How Utilscord uses it |
| --- | --- |
| [KLIPY](https://klipy.com/) | GIF search and media for `/klipy`, with Search KLIPY branding and Powered by KLIPY attribution. |
| [Pycord](https://pycord.dev/) | The Python library connecting Utilscord to Discord. |
| [LaTeX as a Service (LaaS)](https://laas.vercel.app/) by [József Sallai](https://github.com/jozsefsallai) | External PNG and SVG rendering for `/latex render`. LaaS credits [MathJax](https://www.mathjax.org/) for parsing expressions. |

Utilscord is an independent project. These credits do not imply sponsorship or endorsement. Created and maintained by [Toby / tobezdev](https://github.com/tobezdev).

## Privacy

Utilscord is operated by Toby / tobezdev. For privacy questions, contact [@tobezdev on Discord](https://discord.com/users/969254887621820526) or use [GitHub Issues](https://github.com/tobezdev/Utilscord/issues) without posting sensitive data.

**Last updated: 8 September 2026.**

### What the bot processes

| Data | Purpose and destination |
| --- | --- |
| Discord user and member IDs, names, roles, permissions, and server/channel context | Resolving command targets, checking access, displaying channel permission reports, and performing requested actions through Discord. |
| Command arguments and moderation reasons | Executing commands and constructing responses. Moderation reasons and moderator identity are sent to Discord's audit log. |
| Channel message history and message IDs | Finding and deleting messages for `/purge`, including verifying an `until` target. |
| LaTeX source and rendering settings | Sent in HTTP requests to `laas.vercel.app` to generate images. SVG requests also trigger a PNG request for the preview. The rendering requests do not explicitly include Discord user or server IDs. |
| GIF search text and maturity filter | Sent to `api.klipy.com` to find a GIF. No Discord user or server IDs are explicitly sent. Media URLs are displayed through Discord, with attribution and source details when provided by KLIPY. |
| Generated images | Held in memory while processing, then uploaded to Discord as attachments visible to people with access to the response. |
| Temporary Discord caches and cooldown state | Used in the running bot process for normal operation and command rate limits. |

The current source enables Discord's Message Content intent, so message content may be available to the bot in channels it can access. It contains no custom message-content analytics, persistent message archive, user database, or advertising integration.

### Storage and third parties

The application code reviewed here does not implement persistent storage for user data or write rendered images to disk. This is not a claim that Discord, KLIPY, LaaS, or the bot's hosting environment keeps no records. Discord stores bot responses, attachments, and audit-log entries under its own practices; see [Discord's Privacy Policy](https://discord.com/privacy).

KLIPY receives GIF queries, filter settings, and normal request metadata such as the bot host’s IP address. Avoid including secrets or personal information in searches.

LaaS receives submitted source and settings, and its infrastructure can receive normal request metadata such as the bot host's IP address. Its retention practices have not been established here. Do not submit secrets or personal information in LaTeX expressions. The hosted bot uses no analytics and records only error logs. According to the maintainer, these logs are anonymous, tracked using unique error codes that are not linked to users, and retained indefinitely.

Data received from users or APIs is kept only as long as needed to carry out the requested operation in the running bot. Backups run every 24 hours. Backup retention and whether backups include any user data have not yet been confirmed, this is run by an external service
; the operational-data statement does not establish when backup copies are deleted.

### Your choices and requests

You can stop using the bot, avoid submitting sensitive content, and ask a server administrator to remove it or restrict its access. Removing the bot does not automatically erase existing Discord messages, attachments, or audit records. For privacy questions or requests concerning any operator-held data, contact [@tobezdev on Discord](https://discord.com/users/969254887621820526) or [open an issue](https://github.com/tobezdev/Utilscord/issues) with a general description. Do not post the personal data itself; ask the maintainer how to provide any necessary details privately. Discord-held data is also subject to Discord's own controls and policies.

## Terms

**Effective: 8 September 2026.** These terms govern use of the Utilscord service operated by Toby / tobezdev. By using the bot, you agree to these terms.

1. **Acceptable use.** Use Utilscord in accordance with applicable law, [Discord's Terms of Service](https://discord.com/terms), [Discord's Community Guidelines](https://discord.com/guidelines), and your server's rules. Do not use it for harassment, abuse, or attempts to bypass permissions or disrupt services.
2. **Authority and moderation.** Only perform actions you are authorised to take. Server administrators are responsible for granting permissions, and moderators are responsible for their selected targets, reasons, and deletion ranges. Appeals about server moderation should go to that server's moderation team.
3. **Submitted content.** Only submit content you have the right to process. Using the LaTeX renderer sends your input to LaaS and posts the result through Discord as described in [Privacy](#privacy).
4. **Availability and changes.** The bot and its features may change, become unavailable, or be discontinued. No uptime or error-free-operation guarantee is offered. Discord or rendering-service failures can affect commands; deletion operations may be only partially completed when a failure occurs.
5. **Access and responsibility.** Access may be restricted to address abuse or protect operation of the service. To the extent permitted by applicable law, the service is provided as available without warranties. Nothing in these terms excludes rights or liabilities that cannot lawfully be excluded.
6. **Updates and contact.** Changes to these terms will be recorded here with an updated effective date. The operator is Toby / tobezdev; contact the maintainer through [@tobezdev on Discord](https://discord.com/users/969254887621820526) or [GitHub Issues](https://github.com/tobezdev/Utilscord/issues).

## Source availability and licensing

The repository is published so you can inspect how Utilscord works. It is not a self-hosting distribution, and running your own instance is not permitted. To use Utilscord, [invite the official hosted bot](https://discord.com/oauth2/authorize?client_id=1546268629648150528).

The source is publicly available **for viewing only**. This is a source-available project, not an open-source licence granting reuse rights. The maintainer does not grant permission to reuse, modify, redistribute, or operate copies of the code through this README. Rights provided by applicable law or the hosting platform's terms are unaffected.

For permission to use the code beyond viewing it, contact Toby / tobezdev through [@tobezdev on Discord](https://discord.com/users/969254887621820526) or [GitHub Issues](https://github.com/tobezdev/Utilscord/issues). Third-party dependencies remain subject to their respective licences. The service terms above do not grant a licence to the source code.
