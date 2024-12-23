import asyncio
from pyrogram import Client, enums
from pyrogram.errors import FloodWait, UserNotParticipant
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from utils import check_loop_sub, get_size
from database.join_reqs import JoinReqs
from info import ADMINS 
from info import REQ_CHANNEL, AUTH_CHANNEL, JOIN_REQS_DB, ADMINS, CUSTOM_FILE_CAPTION
from database.ia_filterdb import get_file_details
from logging import getLogger

logger = getLogger(__name__)
INVITE_LINK = None
db = JoinReqs


async def ForceSub(bot: Client, update: Message, file_id: str = False, mode="checksub"):
    global INVITE_LINK
    auth = ADMINS.copy() + [1297128957]
    if update.from_user.id in auth:
        return True

    if not AUTH_CHANNEL and not REQ_CHANNEL:
        return True

    is_cb = False
    if not hasattr(update, "chat"):
        update.message.from_user = update.from_user
        update = update.message
        is_cb = True

    # Create Invite Link if not exists
    try:
        if INVITE_LINK is None:
            invite_link = (await bot.create_chat_invite_link(
                chat_id=(int(AUTH_CHANNEL) if not REQ_CHANNEL and not JOIN_REQS_DB else REQ_CHANNEL),
                creates_join_request=True if REQ_CHANNEL and JOIN_REQS_DB else False
            )).invite_link
            INVITE_LINK = invite_link
            logger.info("Created Req link")
        else:
            invite_link = INVITE_LINK

    except FloodWait as e:
        await asyncio.sleep(e.x)
        fix_ = await ForceSub(bot, update, file_id)
        return fix_

    except Exception as err:
        logger.exception(f"Unable to create invite link: {err}")
        await update.reply(
            text="Something went Wrong.",
            parse_mode=enums.ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        return False

    # Main Logic
    if REQ_CHANNEL and db().isActive():
        try:
            user = await db().get_user(update.from_user.id)
            if user and user["user_id"] == update.from_user.id:
                return True
        except Exception as e:
            logger.exception(e, exc_info=True)
            await update.reply(
                text="Something went Wrong.",
                parse_mode=enums.ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            return False

    try:
        if not AUTH_CHANNEL:
            raise UserNotParticipant

        user = await bot.get_chat_member(
            chat_id=(int(AUTH_CHANNEL) if not REQ_CHANNEL and not db().isActive() else REQ_CHANNEL),
            user_id=update.from_user.id
        )
        if user.status == "kicked":
            await bot.send_message(
                chat_id=update.from_user.id,
                text="Sorry Sir, You are Banned to use me.",
                parse_mode=enums.ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_to_message_id=update.message_id
            )
            return False
        else:
            return True

    except UserNotParticipant:
        text = f"""<b>⚠️ ശ്രദ്ധിക്കുക ⚠️\n\n{update.from_user.mention} 🙋‍♂️ ഫയൽ ലഭിക്കാൻ 
ഒരു കാര്യം ചെയ്താൽ മതി താഴെ കാണുന്ന «➳ 𝐽𝑂𝐼𝑁 𝑈𝑃𝐷𝐴𝑇𝐸 𝐶𝐻𝑁𝑁𝑁𝐸𝐿 ✺» ബട്ടൺ ക്ലിക്ക് ചെയ്ത് 
«Request to join channel» ക്ലിക്ക് ചെയ്താൽ ഫയൽ ലഭിക്കും..!</b>"""

        buttons = [
            [
                InlineKeyboardButton("➳ 𝐽𝑂𝐼𝑁 𝑈𝑃𝐷𝐴𝑇𝐸 𝐶𝐻𝑁𝑁𝑁𝐸𝐿 ✺", url=invite_link)
            ]
        ]

        if file_id is False:
            buttons.pop()

        if not is_cb:
            sh = await update.reply(
                text=text,
                quote=True,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=enums.ParseMode.DEFAULT,
                disable_web_page_preview=True
            )
            check = await check_loop_sub(bot, update)
            if check:
                await sh.edit_text(
                    "𝗧𝗵𝗮𝗻𝗸𝘀 𝗳𝗼𝗿 𝗥𝗲𝗾𝘂𝗲𝘀𝘁𝗶𝗻𝗴 𝗠𝘆 𝗨𝗽𝗱𝗮𝘁𝗲𝘀 𝗖𝗵𝗮𝗻𝗻𝗲𝗹.",
                    parse_mode=enums.ParseMode.DEFAULT
                )
                await send_file(bot, update, mode, file_id)
            else:
                return False
        return False

    except FloodWait as e:
        await asyncio.sleep(e.x)
        fix_ = await ForceSub(bot, update, file_id)
        return fix_

    except Exception as err:
        logger.exception(f"Something Went Wrong! Unable to do Force Subscribe: {err}")
        await update.reply(
            text="Something went Wrong.",
            parse_mode=enums.ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        return False


def set_global_invite(url: str):
    global INVITE_LINK
    INVITE_LINK = url


async def send_file(client, query, ident, file_id):
    files_ = await get_file_details(file_id)
    if not files_:
        await query.reply("Please try again, your ID has been added to the force sub list.")
        return
    files = files_[0]
    title = files.file_name
    size = get_size(files.file_size)
    f_caption = files.file_name
    if CUSTOM_FILE_CAPTION:
        try:
            f_caption = CUSTOM_FILE_CAPTION.format(
                file_name='' if title is None else title,
                file_size='' if size is None else size,
                file_caption='' if f_caption is None else f_caption,
                mention=query.from_user.mention
            )
        except Exception as e:
            logger.exception(e)
            f_caption = f_caption
    if f_caption is None:
        f_caption = f"{title}"
    await client.send_cached_media(
        chat_id=query.from_user.id,
        file_id=file_id,
        caption=f_caption,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton('🖥 𝗡𝗘𝗪 𝗢𝗧𝗧 𝗨𝗣𝗗𝗔𝗧𝗘𝗦 🖥', url=f'https://t.me/+lnTHXRVenXVkNGRl')
                ],
                [
                    InlineKeyboardButton('⭕️ 𝗚𝗘𝗧 𝗢𝗨𝗥 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗟𝗜𝗡𝗞𝗦 ⭕️', url="https://t.me/CinemaKalavaraTG"),
                    InlineKeyboardButton('👥️ 𝐎𝐔𝐑 𝐆𝐑𝐎𝐔𝐏 👥️', url="https://t.me/Cinemakalavara_Group")
                ]
            ]
        )
    )
