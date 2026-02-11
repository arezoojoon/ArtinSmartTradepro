"""
Bot Orchestrator — QA-HARDENED Finite State Machine.
QA-1: HARD deep-link gating (no session without valid ref).
QA-5: AI rate limits per contact/day and per tenant/hour.
QA-6: Human handoff lock (bot silent until admin release).
QA-7: Timezone-safe scheduling (store UTC, display Asia/Dubai).
QA-8: Complete audit trail (every transition, AI call, RFQ, booking → BotEvent).
"""
import uuid
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.bot_session import BotSession, BotEvent, BotDeeplinkRef
from app.models.crm import CRMContact
from app.models.product import Product, RFQ
from app.services.waha_service import WAHAService
from app.services.scheduling_service import SchedulingService

# ═══════════════════════════════════════════
# QA-5: AI RATE LIMIT CONSTANTS
# ═══════════════════════════════════════════
AI_LIMIT_PER_CONTACT_DAY = 10   # Max AI calls per phone per day
AI_LIMIT_PER_TENANT_HOUR = 50   # Max AI calls across tenant per hour

# ═══════════════════════════════════════════
# QA-7: TIMEZONE CONFIG
# ═══════════════════════════════════════════
try:
    import zoneinfo
    DISPLAY_TZ = zoneinfo.ZoneInfo("Asia/Dubai")
except ImportError:
    import pytz
    DISPLAY_TZ = pytz.timezone("Asia/Dubai")

# ═══════════════════════════════════════════
# TRANSLATIONS (en, ar, fa, fr)
# ═══════════════════════════════════════════

TEXTS = {
    "welcome": {
        "en": "👋 Welcome to *Artin Smart Trade*, {name}!\n\nI'm your AI trade assistant. Choose your language:",
        "ar": "👋 مرحباً بك في *آرتین سمارت تريد*، {name}!\n\nأنا مساعدك التجاري الذكي. اختر لغتك:",
        "fa": "👋 به *آرتین اسمارت ترید* خوش آمدید، {name}!\n\nمن دستیار هوشمند تجاری شما هستم. زبان خود را انتخاب کنید:",
        "fr": "👋 Bienvenue chez *Artin Smart Trade*, {name} !\n\nJe suis votre assistant commercial IA. Choisissez votre langue :"
    },
    "language_options": {
        "en": "1️⃣ English\n2️⃣ العربية\n3️⃣ فارسی\n4️⃣ Français",
    },
    "mode_select": {
        "en": "What are you looking for?\n\n1️⃣ I want to *SELL* (Supplier / Exporter)\n2️⃣ I want to *BUY* (Buyer / Importer)\n\n0️⃣ Main Menu",
        "ar": "ماذا تبحث عنه؟\n\n1️⃣ أريد *البيع* (مورّد / مصدّر)\n2️⃣ أريد *الشراء* (مشتري / مستورد)\n\n0️⃣ القائمة الرئيسية",
        "fa": "دنبال چه هستید؟\n\n1️⃣ می‌خواهم *بفروشم* (تأمین‌کننده / صادرکننده)\n2️⃣ می‌خواهم *بخرم* (خریدار / واردکننده)\n\n0️⃣ منوی اصلی",
        "fr": "Que recherchez-vous ?\n\n1️⃣ Je veux *VENDRE* (Fournisseur / Exportateur)\n2️⃣ Je veux *ACHETER* (Acheteur / Importateur)\n\n0️⃣ Menu principal"
    },
    "seller_menu": {
        "en": "🏭 *Seller Hub*\n\n1️⃣ Browse Product Catalog\n2️⃣ Send My Catalog/Pricing\n3️⃣ 📅 Book a Meeting\n4️⃣ 🤖 AI Market Analysis\n5️⃣ 🧑‍💼 Talk to Human\n\n0️⃣ Main Menu",
        "ar": "🏭 *مركز البائع*\n\n1️⃣ تصفح كتالوج المنتجات\n2️⃣ إرسال كتالوجي / أسعاري\n3️⃣ 📅 حجز اجتماع\n4️⃣ 🤖 تحليل السوق بالذكاء الاصطناعي\n5️⃣ 🧑‍💼 التحدث مع إنسان\n\n0️⃣ القائمة الرئيسية",
        "fa": "🏭 *هاب فروشندگان*\n\n1️⃣ مشاهده کاتالوگ محصولات\n2️⃣ ارسال کاتالوگ / قیمت‌ها\n3️⃣ 📅 رزرو جلسه\n4️⃣ 🤖 تحلیل بازار هوشمند\n5️⃣ 🧑‍💼 صحبت با انسان\n\n0️⃣ منوی اصلی",
        "fr": "🏭 *Hub Vendeur*\n\n1️⃣ Parcourir le catalogue\n2️⃣ Envoyer mon catalogue / tarifs\n3️⃣ 📅 Réserver un rendez-vous\n4️⃣ 🤖 Analyse de marché IA\n5️⃣ 🧑‍💼 Parler à un humain\n\n0️⃣ Menu principal"
    },
    "buyer_menu": {
        "en": "🛒 *Buyer Hub*\n\nLet's create your request (RFQ):\n\n📦 What product are you looking for?",
        "ar": "🛒 *مركز المشتري*\n\nلنقم بإنشاء طلبك:\n\n📦 ما المنتج الذي تبحث عنه؟",
        "fa": "🛒 *هاب خریداران*\n\nبیایید درخواست شما را ایجاد کنیم:\n\n📦 به دنبال چه محصولی هستید؟",
        "fr": "🛒 *Hub Acheteur*\n\nCréons votre demande (RFQ) :\n\n📦 Quel produit cherchez-vous ?"
    },
    "rfq_quantity": {
        "en": "📊 What quantity do you need? (e.g. '500 tons', '2 containers')",
        "ar": "📊 ما الكمية التي تحتاجها؟ (مثلاً '500 طن'، '2 حاوية')",
        "fa": "📊 چه مقداری نیاز دارید؟ (مثلاً '500 تن'، '2 کانتینر')",
        "fr": "📊 Quelle quantité ? (ex: '500 tonnes', '2 containers')"
    },
    "rfq_destination": {
        "en": "🌍 Destination country/city?",
        "ar": "🌍 بلد / مدينة الوجهة؟", "fa": "🌍 کشور / شهر مقصد؟",
        "fr": "🌍 Pays / ville de destination ?"
    },
    "rfq_budget": {
        "en": "💰 Budget range? (e.g. '$5000-$10000' or 'flexible')",
        "ar": "💰 نطاق الميزانية؟", "fa": "💰 محدوده بودجه؟",
        "fr": "💰 Fourchette de budget ?"
    },
    "rfq_timeline": {
        "en": "⏰ When do you need delivery? (e.g. '2 weeks', 'March 2026')",
        "ar": "⏰ متى تحتاج التسليم؟", "fa": "⏰ زمان تحویل؟",
        "fr": "⏰ Délai souhaité ?"
    },
    "rfq_saved": {
        "en": "✅ *RFQ Created!*\n\n📦 Product: {product}\n📊 Qty: {quantity}\n🌍 Destination: {destination}\n💰 Budget: {budget}\n⏰ Timeline: {timeline}\n\nOur team will review and match you with qualified suppliers.\n\n1️⃣ 📅 Book a meeting\n2️⃣ Create another RFQ\n\n0️⃣ Main Menu",
        "ar": "✅ *تم إنشاء الطلب!*\n\n📦 {product}\n📊 {quantity}\n🌍 {destination}\n💰 {budget}\n⏰ {timeline}\n\n1️⃣ 📅 حجز اجتماع\n2️⃣ طلب جديد\n\n0️⃣ القائمة",
        "fa": "✅ *درخواست ایجاد شد!*\n\n📦 {product}\n📊 {quantity}\n🌍 {destination}\n💰 {budget}\n⏰ {timeline}\n\n1️⃣ 📅 رزرو جلسه\n2️⃣ درخواست جدید\n\n0️⃣ منو",
        "fr": "✅ *RFQ Créé !*\n\n📦 {product}\n📊 {quantity}\n🌍 {destination}\n💰 {budget}\n⏰ {timeline}\n\n1️⃣ 📅 Rendez-vous\n2️⃣ Nouveau RFQ\n\n0️⃣ Menu"
    },
    "booking_ask_type": {
        "en": "📅 *Book a Meeting*\n\n1️⃣ 💻 Online (Video Call)\n2️⃣ 📍 In-Person\n\n0️⃣ Main Menu",
        "ar": "📅 *حجز اجتماع*\n\n1️⃣ 💻 أونلاين\n2️⃣ 📍 حضوري\n\n0️⃣ القائمة",
        "fa": "📅 *رزرو جلسه*\n\n1️⃣ 💻 آنلاین\n2️⃣ 📍 حضوری\n\n0️⃣ منو",
        "fr": "📅 *Rendez-vous*\n\n1️⃣ 💻 En ligne\n2️⃣ 📍 En personne\n\n0️⃣ Menu"
    },
    "booking_ask_date": {
        "en": "📆 What date? (e.g. '2026-02-15' or 'tomorrow')",
        "ar": "📆 ما التاريخ؟ (مثلاً '2026-02-15' أو 'غداً')",
        "fa": "📆 چه تاریخی؟ (مثلاً '2026-02-15' یا 'فردا')",
        "fr": "📆 Quelle date ? (ex: '2026-02-15' ou 'demain')"
    },
    "booking_slots": {
        "en": "⏰ Available slots (Dubai time, GMT+4):\n\n{slots}\n\nReply with the number to book.",
        "ar": "⏰ الأوقات المتاحة (توقيت دبي):\n\n{slots}\n\nأرسل الرقم للحجز.",
        "fa": "⏰ زمان‌های موجود (وقت دبی):\n\n{slots}\n\nبرای رزرو شماره را ارسال کنید.",
        "fr": "⏰ Créneaux (heure de Dubaï) :\n\n{slots}\n\nRépondez avec le numéro."
    },
    "booking_confirmed": {
        "en": "✅ *Meeting Booked!*\n\n📅 {date} at {time} (Dubai, GMT+4)\n💼 Type: {type}\n\nYou'll receive a confirmation shortly.",
        "ar": "✅ *تم الحجز!*\n\n📅 {date} {time}\n💼 {type}",
        "fa": "✅ *رزرو شد!*\n\n📅 {date} {time}\n💼 {type}",
        "fr": "✅ *Réservé !*\n\n📅 {date} à {time}\n💼 {type}"
    },
    "human_handoff": {
        "en": "🧑‍💼 Transferring you to a team member. They'll reach out within a few minutes. Stay tuned!",
        "ar": "🧑‍💼 سيتم تحويلك إلى عضو في الفريق.",
        "fa": "🧑‍💼 در حال انتقال به عضو تیم.",
        "fr": "🧑‍💼 Transfert vers un membre de l'équipe."
    },
    "human_locked": {
        "en": "🧑‍💼 A team member is handling your conversation. They'll reply shortly.",
        "ar": "🧑‍💼 عضو تیم در حال بررسی پیام شما است.",
        "fa": "🧑‍💼 یک عضو تیم در حال رسیدگی است.",
        "fr": "🧑‍💼 Un membre de l'équipe traite votre demande."
    },
    "not_started_hard": {
        "en": "👋 To chat with us, please use our official link:\n🔗 Contact your provider for the access link.\n\n_This bot only accepts conversations started via official deep links._",
        "ar": "👋 للتواصل معنا، يرجى استخدام الرابط الرسمي.\n🔗 تواصل مع مزود الخدمة.",
        "fa": "👋 برای گفتگو لطفاً از لینک رسمی استفاده کنید.\n🔗 با ارائه‌دهنده تماس بگیرید.",
        "fr": "👋 Veuillez utiliser le lien officiel.\n🔗 Contactez votre fournisseur."
    },
    "main_menu": {
        "en": "📋 *Main Menu*\n\n1️⃣ I want to SELL\n2️⃣ I want to BUY\n3️⃣ 📅 Book a Meeting\n4️⃣ 🧑‍💼 Talk to Human\n\n🌐 Change Language: type 'lang'",
        "ar": "📋 *القائمة*\n\n1️⃣ البيع\n2️⃣ الشراء\n3️⃣ 📅 حجز\n4️⃣ 🧑‍💼 إنسان\n\n🌐 'lang'",
        "fa": "📋 *منو*\n\n1️⃣ فروش\n2️⃣ خرید\n3️⃣ 📅 رزرو\n4️⃣ 🧑‍💼 انسان\n\n🌐 'lang'",
        "fr": "📋 *Menu*\n\n1️⃣ VENDRE\n2️⃣ ACHETER\n3️⃣ 📅 Rendez-vous\n4️⃣ 🧑‍💼 Humain\n\n🌐 'lang'"
    },
    "media_received": {
        "en": "📎 Media received! Analyzing with AI... Please wait.",
        "ar": "📎 جاري التحليل...", "fa": "📎 در حال تحلیل...", "fr": "📎 Analyse IA..."
    },
    "ai_limit_reached": {
        "en": "⚠️ AI analysis limit reached for today ({count}/{limit}).\nPlease try again tomorrow, or type 5️⃣ to talk to a human.",
        "ar": "⚠️ تم الوصول إلى الحد اليومي ({count}/{limit}).\nجرب غداً أو اكتب 5️⃣ للتحدث مع إنسان.",
        "fa": "⚠️ محدودیت روزانه AI ({count}/{limit}).\nفردا تلاش کنید یا 5️⃣ برای انسان.",
        "fr": "⚠️ Limite IA atteinte ({count}/{limit}).\nRéessayez demain ou tapez 5️⃣ pour un humain."
    },
    "catalog_list": {
        "en": "📦 *Our Products:*\n\n{products}\n\nReply with a number for details, or 0️⃣ Main Menu",
        "ar": "📦 *منتجاتنا:*\n\n{products}\n\n0️⃣ القائمة",
        "fa": "📦 *محصولات:*\n\n{products}\n\n0️⃣ منو",
        "fr": "📦 *Produits :*\n\n{products}\n\n0️⃣ Menu"
    }
}


def t(key: str, lang: str, **kwargs) -> str:
    text_dict = TEXTS.get(key, {})
    text = text_dict.get(lang, text_dict.get("en", f"[{key}]"))
    try:
        if kwargs:
            text = text.format(**kwargs)
    except KeyError:
        pass
    return text


# ═══════════════════════════════════════════
# QA-5: AI RATE LIMIT CHECK
# ═══════════════════════════════════════════

def _check_ai_limit(db: Session, session: BotSession, tenant_id: uuid.UUID) -> bool:
    """
    Returns True if AI call is allowed, False if limit reached.
    Checks per-contact/day AND per-tenant/hour.
    """
    today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    # Per-contact/day check
    if session.ai_calls_today_date != today_str:
        session.ai_calls_today = 0
        session.ai_calls_today_date = today_str
    if session.ai_calls_today >= AI_LIMIT_PER_CONTACT_DAY:
        return False

    # Per-tenant/hour check
    hour_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    tenant_ai_count = db.query(func.count(BotEvent.id)).filter(
        BotEvent.tenant_id == tenant_id,
        BotEvent.event_type.in_(["ai_vision", "ai_audio", "ai_market"]),
        BotEvent.created_at >= hour_ago
    ).scalar() or 0
    if tenant_ai_count >= AI_LIMIT_PER_TENANT_HOUR:
        return False

    return True


def _increment_ai_usage(session: BotSession):
    """Increment contact-level AI counter."""
    session.ai_calls_today = (session.ai_calls_today or 0) + 1


# ═══════════════════════════════════════════
# QA-7: DATE PARSING (multi-lang, timezone-safe)
# ═══════════════════════════════════════════

TOMORROW_WORDS = {"tomorrow", "غدا", "غداً", "فردا", "demain"}

def _parse_date_input(text: str) -> datetime.date:
    """Parse user date input; raises ValueError on failure."""
    cleaned = text.strip().lower()
    if cleaned in TOMORROW_WORDS:
        # "tomorrow" in display timezone
        now_dubai = datetime.datetime.now(DISPLAY_TZ)
        return (now_dubai + datetime.timedelta(days=1)).date()

    import dateutil.parser as dp
    parsed = dp.parse(text)
    return parsed.date()


def _utc_to_dubai(dt: datetime.datetime) -> datetime.datetime:
    """QA-7: Convert UTC datetime to Asia/Dubai for display."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(DISPLAY_TZ)


# ═══════════════════════════════════════════
# QA-8: AUDIT HELPER
# ═══════════════════════════════════════════

def _audit(db, tenant_id, session_id, phone, event_type, payload=None,
           state_before=None, state_after=None, ai_job_id=None, ai_cost=None, message_id=None):
    event = BotEvent(
        tenant_id=tenant_id,
        session_id=session_id,
        phone=phone,
        event_type=event_type,
        payload=payload or {},
        state_before=state_before,
        state_after=state_after,
        ai_job_id=ai_job_id,
        ai_cost=ai_cost,
        message_id=message_id
    )
    db.add(event)


# ═══════════════════════════════════════════
# ORCHESTRATOR
# ═══════════════════════════════════════════

class BotOrchestrator:

    @staticmethod
    async def handle_message(
        db: Session,
        tenant_id: uuid.UUID,
        phone: str,
        text: str,
        whatsapp_name: str = None,
        media_url: str = None,
        media_type: str = None,
        deeplink_ref: str = None
    ):
        """
        Main entry point. Called by webhook for every inbound message.
        QA-1: HARD gating — no session without valid ref.
        QA-6: LOCKED check — bot silent if human handoff active.
        """
        session = db.query(BotSession).filter(
            BotSession.tenant_id == tenant_id,
            BotSession.phone == phone
        ).first()

        # ═══════════════════════════════════════
        # QA-1: HARD DEEP-LINK GATING
        # ═══════════════════════════════════════
        if not session:
            if not deeplink_ref:
                # NO session, NO ref → reject with minimal reply, NO session created
                _audit(db, tenant_id, None, phone, "deeplink_reject",
                       {"text": (text or "")[:200], "reason": "no_ref_no_session"})
                # Send minimal reply (no state, no session, no side effects)
                await WAHAService.send_and_persist(
                    db, tenant_id, phone, t("not_started_hard", "en"),
                    session_id=None, event_type="reject_reply"
                )
                db.commit()
                return

            # Has ref → validate it exists and resolve tenant
            ref_record = db.query(BotDeeplinkRef).filter(
                BotDeeplinkRef.ref == deeplink_ref,
                BotDeeplinkRef.is_active == True
            ).first()
            if not ref_record:
                _audit(db, tenant_id, None, phone, "deeplink_reject",
                       {"text": (text or "")[:200], "ref": deeplink_ref, "reason": "invalid_ref"})
                await WAHAService.send_and_persist(
                    db, tenant_id, phone, t("not_started_hard", "en"),
                    session_id=None, event_type="reject_reply"
                )
                db.commit()
                return

            # Check expiry
            if ref_record.expires_at and ref_record.expires_at < datetime.datetime.utcnow():
                _audit(db, tenant_id, None, phone, "deeplink_reject",
                       {"ref": deeplink_ref, "reason": "expired"})
                await WAHAService.send_and_persist(
                    db, tenant_id, phone, t("not_started_hard", "en"),
                    session_id=None, event_type="reject_reply"
                )
                db.commit()
                return

            # QA-2: Use tenant from ref_record, NOT from env
            tenant_id = ref_record.tenant_id

            session = BotSession(
                tenant_id=tenant_id,
                phone=phone,
                whatsapp_name=whatsapp_name,
                language="en",
                state="welcome",
                started_via_deeplink=True,
                deeplink_ref=deeplink_ref,
                is_active=True,
                locked_for_human=False,
                ai_calls_today=0,
                context={}
            )
            db.add(session)
            db.flush()

            _audit(db, tenant_id, session.id, phone, "session_created",
                   {"ref": deeplink_ref, "campaign_id": str(ref_record.campaign_id) if ref_record.campaign_id else None})

        # ═══════════════════════════════════════
        # QA-6: HUMAN HANDOFF LOCK
        # ═══════════════════════════════════════
        if session.locked_for_human:
            _audit(db, tenant_id, session.id, phone, "locked_message",
                   {"text": (text or "")[:200]})
            await WAHAService.send_and_persist(
                db, tenant_id, phone, t("human_locked", session.language),
                session_id=session.id, event_type="locked_reply"
            )
            db.commit()
            return

        # Refresh activity
        session.last_active_at = datetime.datetime.utcnow()
        if whatsapp_name:
            session.whatsapp_name = whatsapp_name

        state_before = session.state

        # QA-8: Log inbound
        _audit(db, tenant_id, session.id, phone, "inbound_text",
               {"text": (text or "")[:500], "media_url": media_url, "media_type": media_type},
               state_before=state_before)

        # Handle media (QA-5 rate limit check inside)
        if media_url and media_type in ("image", "audio"):
            await BotOrchestrator._handle_media(db, tenant_id, session, phone, media_url, media_type)
            db.commit()
            return

        # Normalize input
        inp = (text or "").strip()
        inp_lower = inp.lower()

        # Global commands
        if inp_lower in ("0", "menu", "main menu", "start", "منو", "قائمة"):
            session.state = "main_menu"
            session.mode = None
            _audit(db, tenant_id, session.id, phone, "state_change",
                   state_before=state_before, state_after="main_menu")
            await WAHAService.send_and_persist(
                db, tenant_id, phone, t("main_menu", session.language),
                session_id=session.id)
            db.commit()
            return

        if inp_lower in ("lang", "language", "زبان", "لغة"):
            session.state = "language"
            _audit(db, tenant_id, session.id, phone, "state_change",
                   state_before=state_before, state_after="language")
            msg = t("welcome", session.language, name=session.whatsapp_name or phone)
            msg += "\n\n" + t("language_options", "en")
            await WAHAService.send_and_persist(db, tenant_id, phone, msg, session_id=session.id)
            db.commit()
            return

        if inp_lower in ("5", "human", "انسان", "إنسان"):
            await BotOrchestrator._handoff_to_human(db, tenant_id, session, phone, state_before)
            db.commit()
            return

        # State-based routing
        handler = STATE_HANDLERS.get(session.state, BotOrchestrator._handle_main_menu)
        await handler(db, tenant_id, session, phone, inp)

        # QA-8: Log transition if state changed
        if session.state != state_before:
            _audit(db, tenant_id, session.id, phone, "state_change",
                   state_before=state_before, state_after=session.state)

        db.commit()

    # ═══════════════════════════════════════
    # STATE HANDLERS
    # ═══════════════════════════════════════

    @staticmethod
    async def _handle_welcome(db, tenant_id, session, phone, inp):
        msg = t("welcome", "en", name=session.whatsapp_name or phone)
        msg += "\n\n" + t("language_options", "en")
        session.state = "language"
        await WAHAService.send_and_persist(db, tenant_id, phone, msg, session_id=session.id)

    @staticmethod
    async def _handle_language(db, tenant_id, session, phone, inp):
        lang_map = {"1": "en", "2": "ar", "3": "fa", "4": "fr"}
        lang = lang_map.get(inp.strip())
        if not lang:
            await WAHAService.send_and_persist(
                db, tenant_id, phone, t("language_options", "en"), session_id=session.id)
            return
        session.language = lang
        session.state = "mode"
        await WAHAService.send_and_persist(
            db, tenant_id, phone, t("mode_select", lang), session_id=session.id)

    @staticmethod
    async def _handle_mode(db, tenant_id, session, phone, inp):
        if inp == "1":
            session.mode = "seller"
            session.state = "seller_menu"
            await WAHAService.send_and_persist(
                db, tenant_id, phone, t("seller_menu", session.language), session_id=session.id)
        elif inp == "2":
            session.mode = "buyer"
            session.state = "rfq_product"
            await WAHAService.send_and_persist(
                db, tenant_id, phone, t("buyer_menu", session.language), session_id=session.id)
        else:
            await WAHAService.send_and_persist(
                db, tenant_id, phone, t("mode_select", session.language), session_id=session.id)

    @staticmethod
    async def _handle_main_menu(db, tenant_id, session, phone, inp):
        if inp == "1":
            session.mode = "seller"
            session.state = "seller_menu"
            await WAHAService.send_and_persist(
                db, tenant_id, phone, t("seller_menu", session.language), session_id=session.id)
        elif inp == "2":
            session.mode = "buyer"
            session.state = "rfq_product"
            await WAHAService.send_and_persist(
                db, tenant_id, phone, t("buyer_menu", session.language), session_id=session.id)
        elif inp == "3":
            session.state = "booking_type"
            await WAHAService.send_and_persist(
                db, tenant_id, phone, t("booking_ask_type", session.language), session_id=session.id)
        elif inp == "4":
            await BotOrchestrator._handoff_to_human(db, tenant_id, session, phone, session.state)
        else:
            await WAHAService.send_and_persist(
                db, tenant_id, phone, t("main_menu", session.language), session_id=session.id)

    # ═══════════════════════════════════════
    # SELLER FLOW
    # ═══════════════════════════════════════

    @staticmethod
    async def _handle_seller_menu(db, tenant_id, session, phone, inp):
        if inp == "1":
            await BotOrchestrator._show_catalog(db, tenant_id, session, phone)
        elif inp == "2":
            await WAHAService.send_and_persist(db, tenant_id, phone,
                "📤 Please send your catalog as a PDF or images. I'll process them with AI.",
                session_id=session.id)
            session.state = "awaiting_catalog_upload"
        elif inp == "3":
            session.state = "booking_type"
            await WAHAService.send_and_persist(
                db, tenant_id, phone, t("booking_ask_type", session.language), session_id=session.id)
        elif inp == "4":
            # QA-5: AI limit check
            if not _check_ai_limit(db, session, tenant_id):
                _audit(db, tenant_id, session.id, phone, "ai_limit_hit",
                       {"limit": AI_LIMIT_PER_CONTACT_DAY, "count": session.ai_calls_today})
                await WAHAService.send_and_persist(db, tenant_id, phone,
                    t("ai_limit_reached", session.language,
                      count=session.ai_calls_today, limit=AI_LIMIT_PER_CONTACT_DAY),
                    session_id=session.id)
                return
            await WAHAService.send_and_persist(db, tenant_id, phone,
                "🤖 What product and market do you want to analyze?\nExample: 'Olive oil in Germany'",
                session_id=session.id)
            session.state = "ai_analysis"
        elif inp == "5":
            await BotOrchestrator._handoff_to_human(db, tenant_id, session, phone, session.state)
        else:
            await WAHAService.send_and_persist(
                db, tenant_id, phone, t("seller_menu", session.language), session_id=session.id)

    @staticmethod
    async def _show_catalog(db, tenant_id, session, phone):
        products = db.query(Product).filter(Product.tenant_id == tenant_id).limit(10).all()
        if not products:
            await WAHAService.send_and_persist(db, tenant_id, phone,
                "📦 No products in catalog yet.\n\n0️⃣ Main Menu", session_id=session.id)
            return
        product_list = "\n".join([f"{i+1}️⃣ *{p.name}* — {p.currency} {p.price}" for i, p in enumerate(products)])
        session.context = {**(session.context or {}), "catalog_products": [str(p.id) for p in products]}
        session.state = "catalog_browse"
        await WAHAService.send_and_persist(db, tenant_id, phone,
            t("catalog_list", session.language, products=product_list), session_id=session.id)

    @staticmethod
    async def _handle_catalog_browse(db, tenant_id, session, phone, inp):
        catalog_ids = (session.context or {}).get("catalog_products", [])
        try:
            idx = int(inp) - 1
            if 0 <= idx < len(catalog_ids):
                product = db.query(Product).filter(Product.id == catalog_ids[idx]).first()
                if product:
                    msg = f"📦 *{product.name}*\n💰 {product.currency} {product.price}\n📋 {product.description or 'No description'}\n📊 Stock: {product.stock_quantity}\n\n1️⃣ 📅 Book Meeting\n\n0️⃣ Main Menu"
                    await WAHAService.send_and_persist(db, tenant_id, phone, msg, session_id=session.id)
                    return
        except (ValueError, IndexError):
            pass
        await WAHAService.send_and_persist(
            db, tenant_id, phone, t("seller_menu", session.language), session_id=session.id)
        session.state = "seller_menu"

    # ═══════════════════════════════════════
    # BUYER FLOW (RFQ Collection)
    # ═══════════════════════════════════════

    @staticmethod
    async def _handle_rfq_product(db, tenant_id, session, phone, inp):
        ctx = session.context or {}
        ctx["rfq_product"] = inp
        session.context = ctx
        session.state = "rfq_quantity"
        await WAHAService.send_and_persist(
            db, tenant_id, phone, t("rfq_quantity", session.language), session_id=session.id)

    @staticmethod
    async def _handle_rfq_quantity(db, tenant_id, session, phone, inp):
        ctx = session.context or {}
        ctx["rfq_quantity"] = inp
        session.context = ctx
        session.state = "rfq_destination"
        await WAHAService.send_and_persist(
            db, tenant_id, phone, t("rfq_destination", session.language), session_id=session.id)

    @staticmethod
    async def _handle_rfq_destination(db, tenant_id, session, phone, inp):
        ctx = session.context or {}
        ctx["rfq_destination"] = inp
        session.context = ctx
        session.state = "rfq_budget"
        await WAHAService.send_and_persist(
            db, tenant_id, phone, t("rfq_budget", session.language), session_id=session.id)

    @staticmethod
    async def _handle_rfq_budget(db, tenant_id, session, phone, inp):
        ctx = session.context or {}
        ctx["rfq_budget"] = inp
        session.context = ctx
        session.state = "rfq_timeline"
        await WAHAService.send_and_persist(
            db, tenant_id, phone, t("rfq_timeline", session.language), session_id=session.id)

    @staticmethod
    async def _handle_rfq_timeline(db, tenant_id, session, phone, inp):
        ctx = session.context or {}
        ctx["rfq_timeline"] = inp
        session.context = ctx

        rfq = RFQ(
            tenant_id=tenant_id,
            title=ctx.get("rfq_product", "Untitled"),
            description=f"Product: {ctx.get('rfq_product')}\n"
                        f"Quantity: {ctx.get('rfq_quantity')}\n"
                        f"Destination: {ctx.get('rfq_destination')}\n"
                        f"Budget: {ctx.get('rfq_budget')}\n"
                        f"Timeline: {ctx.get('rfq_timeline')}\n"
                        f"WhatsApp: {phone}",
            budget=None,
            status="open"
        )
        db.add(rfq)
        db.flush()

        # QA-8: Audit RFQ creation
        _audit(db, tenant_id, session.id, phone, "rfq_created",
               {"rfq_id": str(rfq.id), "product": ctx.get("rfq_product")})

        session.state = "rfq_done"
        await WAHAService.send_and_persist(db, tenant_id, phone, t("rfq_saved", session.language,
            product=ctx.get("rfq_product", ""), quantity=ctx.get("rfq_quantity", ""),
            destination=ctx.get("rfq_destination", ""), budget=ctx.get("rfq_budget", ""),
            timeline=ctx.get("rfq_timeline", "")), session_id=session.id)

    @staticmethod
    async def _handle_rfq_done(db, tenant_id, session, phone, inp):
        if inp == "1":
            session.state = "booking_type"
            await WAHAService.send_and_persist(
                db, tenant_id, phone, t("booking_ask_type", session.language), session_id=session.id)
        elif inp == "2":
            session.state = "rfq_product"
            session.context = {}
            await WAHAService.send_and_persist(
                db, tenant_id, phone, t("buyer_menu", session.language), session_id=session.id)
        else:
            session.state = "main_menu"
            await WAHAService.send_and_persist(
                db, tenant_id, phone, t("main_menu", session.language), session_id=session.id)

    # ═══════════════════════════════════════
    # BOOKING FLOW (QA-7: Timezone-safe)
    # ═══════════════════════════════════════

    @staticmethod
    async def _handle_booking_type(db, tenant_id, session, phone, inp):
        if inp in ("1", "2"):
            ctx = session.context or {}
            ctx["booking_type"] = "online" if inp == "1" else "in_person"
            session.context = ctx
            session.state = "booking_date"
            await WAHAService.send_and_persist(
                db, tenant_id, phone, t("booking_ask_date", session.language), session_id=session.id)
        else:
            await WAHAService.send_and_persist(
                db, tenant_id, phone, t("booking_ask_type", session.language), session_id=session.id)

    @staticmethod
    async def _handle_booking_date(db, tenant_id, session, phone, inp):
        # QA-7: Safe date parsing with multi-lang support
        try:
            target_date = _parse_date_input(inp)
        except Exception:
            await WAHAService.send_and_persist(db, tenant_id, phone,
                "⚠️ Could not understand that date. " + t("booking_ask_date", session.language),
                session_id=session.id)
            return  # Stay in booking_date state, no corruption

        from app.models.user import User
        host = db.query(User).filter(User.tenant_id == tenant_id).first()
        if not host:
            await WAHAService.send_and_persist(db, tenant_id, phone,
                "❌ No availability configured.\n\n0️⃣ Main Menu", session_id=session.id)
            session.state = "main_menu"
            return

        slots = SchedulingService.get_available_slots(db, host.id, target_date)
        if not slots:
            await WAHAService.send_and_persist(db, tenant_id, phone,
                f"❌ No slots on {target_date}. Try another date.\n\n" + t("booking_ask_date", session.language),
                session_id=session.id)
            return

        # QA-7: Display slots in Dubai time
        display_slots = slots[:7]
        slots_text = ""
        for i, s in enumerate(display_slots):
            try:
                start_utc = datetime.datetime.fromisoformat(s["start"])
                start_dubai = _utc_to_dubai(start_utc)
                label = start_dubai.strftime("%I:%M %p")
            except Exception:
                label = s.get("label", f"Slot {i+1}")
            slots_text += f"{i+1}️⃣ {label}\n"

        ctx = session.context or {}
        ctx["booking_date"] = target_date.isoformat()
        ctx["booking_slots"] = display_slots
        ctx["booking_host_id"] = str(host.id)
        session.context = ctx
        session.state = "booking_select_slot"

        await WAHAService.send_and_persist(db, tenant_id, phone,
            t("booking_slots", session.language, slots=slots_text), session_id=session.id)

    @staticmethod
    async def _handle_booking_select_slot(db, tenant_id, session, phone, inp):
        ctx = session.context or {}
        slots = ctx.get("booking_slots", [])
        try:
            idx = int(inp) - 1
            if 0 <= idx < len(slots):
                slot = slots[idx]
                appt = SchedulingService.book_appointment(
                    db, tenant_id,
                    host_id=uuid.UUID(ctx["booking_host_id"]),
                    guest_name=session.whatsapp_name or phone,
                    guest_email=None,
                    start_time=datetime.datetime.fromisoformat(slot["start"]),
                    end_time=datetime.datetime.fromisoformat(slot["end"]),
                    meeting_type=ctx.get("booking_type", "online"),
                    location=None,
                    notes=f"Booked via WhatsApp Bot. Phone: {phone}"
                )

                # QA-7: Display confirmation in Dubai time
                start_dubai = _utc_to_dubai(datetime.datetime.fromisoformat(slot["start"]))

                # QA-8: Audit booking
                _audit(db, tenant_id, session.id, phone, "booking_created",
                       {"appointment_id": str(appt.id) if hasattr(appt, 'id') else None,
                        "date": ctx.get("booking_date"), "type": ctx.get("booking_type")})

                session.state = "main_menu"
                await WAHAService.send_and_persist(db, tenant_id, phone, t("booking_confirmed", session.language,
                    date=ctx.get("booking_date", ""),
                    time=start_dubai.strftime("%I:%M %p"),
                    type=ctx.get("booking_type", "online")), session_id=session.id)
                return
        except Exception:
            await WAHAService.send_and_persist(db, tenant_id, phone,
                "⚠️ Slot unavailable. " + t("booking_ask_date", session.language),
                session_id=session.id)
            session.state = "booking_date"
            return

        await WAHAService.send_and_persist(db, tenant_id, phone,
            "Please reply with a valid number.", session_id=session.id)

    # ═══════════════════════════════════════
    # MEDIA HANDLING (QA-4 + QA-5)
    # ═══════════════════════════════════════

    @staticmethod
    async def _handle_media(db, tenant_id, session, phone, media_url, media_type):
        """
        QA-4: Secure download via download_media_secure.
        QA-5: AI rate limit enforced before processing.
        QA-8: AI event with cost logged.
        """
        # QA-5: Rate limit check
        if not _check_ai_limit(db, session, tenant_id):
            _audit(db, tenant_id, session.id, phone, "ai_limit_hit",
                   {"limit": AI_LIMIT_PER_CONTACT_DAY, "count": session.ai_calls_today, "media_type": media_type})
            await WAHAService.send_and_persist(db, tenant_id, phone,
                t("ai_limit_reached", session.language,
                  count=session.ai_calls_today, limit=AI_LIMIT_PER_CONTACT_DAY),
                session_id=session.id)
            return

        await WAHAService.send_and_persist(db, tenant_id, phone,
            t("media_received", session.language), session_id=session.id)

        try:
            # QA-4: Secure download
            media_bytes, detected_mime = await WAHAService.download_media_secure(media_url, media_type)

            _increment_ai_usage(session)

            if media_type == "image":
                from app.services.gemini_service import GeminiService
                result = await GeminiService.scan_business_card_enhanced(media_bytes)

                # QA-8: Log AI event
                _audit(db, tenant_id, session.id, phone, "ai_vision",
                       {"mime": detected_mime, "size": len(media_bytes), "result_keys": list(result.keys()) if isinstance(result, dict) else None},
                       ai_cost=2.0)

                msg = "🔍 *AI Vision Analysis:*\n\n"
                if isinstance(result, dict):
                    for key, val in result.items():
                        if val and key not in ("raw_response",):
                            msg += f"• *{key}*: {val}\n"
                    # CRM upsert
                    if result.get("phone"):
                        contact = db.query(CRMContact).filter(
                            CRMContact.tenant_id == tenant_id,
                            CRMContact.phone == result["phone"]
                        ).first()
                        if not contact:
                            contact = CRMContact(
                                tenant_id=tenant_id,
                                first_name=result.get("name", "Unknown"),
                                email=result.get("email"),
                                phone=result.get("phone"),
                                position=result.get("position")
                            )
                            db.add(contact)
                        msg += "\n✅ Contact saved to CRM!"
                msg += "\n\n0️⃣ Main Menu"
                await WAHAService.send_and_persist(db, tenant_id, phone, msg, session_id=session.id)

            elif media_type == "audio":
                from app.services.gemini_service import GeminiService
                result = await GeminiService.analyze_audio(media_bytes)

                _audit(db, tenant_id, session.id, phone, "ai_audio",
                       {"mime": detected_mime, "size": len(media_bytes)},
                       ai_cost=5.0)

                msg = "🎤 *AI Audio Analysis:*\n\n"
                if isinstance(result, dict):
                    if result.get("transcript"):
                        msg += f"📝 *Transcript:* {result['transcript'][:500]}\n"
                    if result.get("intent"):
                        msg += f"🎯 *Intent:* {result['intent']}\n"
                msg += "\n\n0️⃣ Main Menu"
                await WAHAService.send_and_persist(db, tenant_id, phone, msg, session_id=session.id)

        except ValueError as e:
            # QA-4: Security rejection (SSRF, size, MIME)
            error_msg = str(e)
            _audit(db, tenant_id, session.id, phone, "media_security_reject",
                   {"error": error_msg[:200], "url": media_url[:100]})
            await WAHAService.send_and_persist(db, tenant_id, phone,
                f"⚠️ Cannot process media: file rejected.\n\n0️⃣ Main Menu",
                session_id=session.id)
        except Exception as e:
            _audit(db, tenant_id, session.id, phone, "error",
                   {"error": str(e)[:200], "context": "media_analysis"})
            await WAHAService.send_and_persist(db, tenant_id, phone,
                f"⚠️ Could not process media.\n\n0️⃣ Main Menu", session_id=session.id)

    # ═══════════════════════════════════════
    # AI ANALYSIS (QA-5 rate limited)
    # ═══════════════════════════════════════

    @staticmethod
    async def _handle_ai_analysis(db, tenant_id, session, phone, inp):
        if not _check_ai_limit(db, session, tenant_id):
            _audit(db, tenant_id, session.id, phone, "ai_limit_hit",
                   {"count": session.ai_calls_today})
            await WAHAService.send_and_persist(db, tenant_id, phone,
                t("ai_limit_reached", session.language,
                  count=session.ai_calls_today, limit=AI_LIMIT_PER_CONTACT_DAY),
                session_id=session.id)
            session.state = "seller_menu"
            return

        try:
            _increment_ai_usage(session)
            from app.services.gemini_service import GeminiService
            result = await GeminiService.analyze_market(inp, "current")

            _audit(db, tenant_id, session.id, phone, "ai_market",
                   {"query": inp[:200]}, ai_cost=8.0)

            msg = "🤖 *AI Market Analysis:*\n\n"
            if isinstance(result, dict):
                for key, val in result.items():
                    if val:
                        msg += f"• *{key}*: {val}\n"
            else:
                msg += str(result)[:1000]
            msg += "\n\n0️⃣ Main Menu"
        except Exception as e:
            _audit(db, tenant_id, session.id, phone, "error",
                   {"error": str(e)[:200], "context": "ai_market"})
            msg = f"⚠️ Analysis error.\n\n0️⃣ Main Menu"
        session.state = "seller_menu"
        await WAHAService.send_and_persist(db, tenant_id, phone, msg, session_id=session.id)

    # ═══════════════════════════════════════
    # HUMAN HANDOFF (QA-6: Lock)
    # ═══════════════════════════════════════

    @staticmethod
    async def _handoff_to_human(db, tenant_id, session, phone, state_before):
        """QA-6: Lock session — bot goes completely silent until admin releases."""
        from app.models.crm import CRMConversation
        conv = db.query(CRMConversation).filter(
            CRMConversation.tenant_id == tenant_id,
            CRMConversation.identifier == phone
        ).first()
        if conv:
            conv.status = "needs_human"

        session.locked_for_human = True
        session.state = "human"

        _audit(db, tenant_id, session.id, phone, "handoff",
               {"state_before": state_before})

        await WAHAService.send_and_persist(db, tenant_id, phone,
            t("human_handoff", session.language), session_id=session.id)

    # ═══════════════════════════════════════
    # AWAITING CATALOG UPLOAD
    # ═══════════════════════════════════════

    @staticmethod
    async def _handle_awaiting_catalog_upload(db, tenant_id, session, phone, inp):
        await WAHAService.send_and_persist(db, tenant_id, phone,
            "📤 Please send an image or PDF file.\n\n0️⃣ Main Menu", session_id=session.id)


# ═══════════════════════════════════════════
# STATE → HANDLER DISPATCH TABLE
# ═══════════════════════════════════════════

STATE_HANDLERS = {
    "welcome": BotOrchestrator._handle_welcome,
    "language": BotOrchestrator._handle_language,
    "mode": BotOrchestrator._handle_mode,
    "main_menu": BotOrchestrator._handle_main_menu,
    "seller_menu": BotOrchestrator._handle_seller_menu,
    "catalog_browse": BotOrchestrator._handle_catalog_browse,
    "rfq_product": BotOrchestrator._handle_rfq_product,
    "rfq_quantity": BotOrchestrator._handle_rfq_quantity,
    "rfq_destination": BotOrchestrator._handle_rfq_destination,
    "rfq_budget": BotOrchestrator._handle_rfq_budget,
    "rfq_timeline": BotOrchestrator._handle_rfq_timeline,
    "rfq_done": BotOrchestrator._handle_rfq_done,
    "booking_type": BotOrchestrator._handle_booking_type,
    "booking_date": BotOrchestrator._handle_booking_date,
    "booking_select_slot": BotOrchestrator._handle_booking_select_slot,
    "ai_analysis": BotOrchestrator._handle_ai_analysis,
    "awaiting_catalog_upload": BotOrchestrator._handle_awaiting_catalog_upload,
}
