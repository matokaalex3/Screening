import logging
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# --- KONFIGURASI (SUDAH DIISI DENGAN DATA KAMU) ---
BOT_TOKEN = "8877427633:AAH0UDeCNkBrSqs2xMgX7HEFD1JYf4RcYa4"
TRACKER_GROUP_ID = -1004446029433  # ID Grup Diskusi (Sumber Sinyal)
OUTPUT_CHANNEL_ID = -1004488221362  # ID Channel Output (Tujuan Sinyal Lolos)

# Setup Logging agar bisa melihat aktivitas bot di terminal
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def apply_golden_formula(text: str) -> bool:
    """
    Menerapkan 'Formula Emas' berdasarkan panduan tempur crypto degen.
    Return True jika LOLOS, False jika TIDAK LOLOS.
    """
    text_lower = text.lower()
    
    # 1. EKSTRAK DATA DARI TEKS (Format Leka Track)
    # MC (Market Cap) dalam ribuan ($K)
    mc_match = re.search(r'mc\s*\$([\d.]+)[kmb]?', text_lower)
    mc_val = float(mc_match.group(1)) if mc_match else 0
    
    # LP (Liquidity Pool) dalam ribuan ($K)
    lp_match = re.search(r'lp\s*\$([\d.]+)[kmb]?', text_lower)
    lp_val = float(lp_match.group(1)) if lp_match else 0
    
    # Top 10 Holders (%)
    top10_match = re.search(r'top10\s*([\d.]+)%', text_lower)
    top10_val = float(top10_match.group(1)) if top10_match else 100
    
    # Bot Transaksi (%)
    bot_match = re.search(r'bot\s*([\d.]+)%', text_lower)
    bot_val = float(bot_match.group(1)) if bot_match else 100
    
    # Bundle (%)
    bundle_match = re.search(r'bundle\s*([\d.]+)%', text_lower)
    bundle_val = float(bundle_match.group(1)) if bundle_match else 100
    
    # Insider (jumlah wallet)
    insider_match = re.search(r'insider\s*(\d+)', text_lower)
    insider_val = int(insider_match.group(1)) if insider_match else 100
    
    # Smart Money (jumlah) - Format: "Smart 4"
    sm_match = re.search(r'smart\s*(\d+)', text_lower)
    sm_val = int(sm_match.group(1)) if sm_match else 0
    
    # Top 1 Holder (%) - Format: "Top 1 12%"
    top1_match = re.search(r'top 1\s*([\d.]+)%', text_lower)
    top1_val = float(top1_match.group(1)) if top1_match else 100

    # Hitung Rasio LP/MC secara manual (karena sering tidak ditulis eksplisit dalam %)
    ratio_val = 0
    if mc_val > 0 and lp_val > 0:
        ratio_val = (lp_val / mc_val) * 100

    # --- LOGIKA FILTER BERDASARKAN PANDUAN TEMPUR ---
    
    # Deteksi Chain
    is_robinhood = "robinhood" in text_lower
    is_solana = "sol" in text_lower or "pump.fun" in text_lower
    
    if is_robinhood:
        # [ BASE / ROBINHOOD - SPEK DIAMOND HANDS ]
        # - Bundle wajib 0.0%
        if bundle_val != 0.0: return False
        # - Insider di bawah 5 wallet
        if insider_val >= 5: return False
        # - Smart Money wajib > 0
        if sm_val <= 0: return False
        # - Rasio LP terhadap MC: 30% - 50%
        if not (30 <= ratio_val <= 50): return False
        # - LP Tebal > $10K
        if lp_val < 10: return False 
        # - Top 10 Holders: Di bawah 25%
        if top10_val >= 25: return False
        # - Bot Transaksi: Di bawah 55%
        if bot_val >= 55: return False
        
        return True # Lolos semua kriteria Base
        
    elif is_solana:
        # [ SOLANA / PUMP.FUN - SPEK SCALPING & MOMENTUM ]
        
        # - Jika MC lantai ($10K-$20K), LP wajib MONSTER (>70% dari MC)
        if mc_val < 20:
            if ratio_val <= 70: return False 
            
        # - Jika MC sudah tinggi (>150K Graduated), Top 10 wajib ULTRA MINI (<5%)
        if mc_val > 150:
            if top10_val >= 5: return False 
            
        # - Jika Bundle > 40%, pastikan Top Holder nomor 1 di bawah 15%
        if bundle_val > 40:
            if top1_val >= 15: return False 
            
        # - Insider wajib hampir 0 (Hindari koin ratusan insider)
        if insider_val > 2: return False 
        
        # - Jika Bot > 80% & Dev rilis banyak: WAJIB ADA NARASI AI/TECH + TRENDING
        if bot_val > 80:
            if "ai" not in text_lower and "tech" not in text_lower and "trending" not in text_lower:
                return False
                
        return True # Lolos kriteria Solana
        
    else:
        # Jika tidak terdeteksi chain-nya, abaikan dulu untuk keamanan
        return False

async def handle_incoming_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    
    # Pastikan pesan adalah forward dari Grup Diskusi Tracker
    # Ini mencegah bot memproses chat biasa anggota grup
    if not message.forward_from_chat or message.forward_from_chat.id != TRACKER_GROUP_ID:
        return
    
    text = message.text or ""
    logger.info(f"Menerima sinyal baru...")
    
    # Jalankan Formula Emas
    if apply_golden_formula(text):
        try:
            # Kirim ke Channel Output jika LOLOS
            await context.bot.send_message(
                chat_id=OUTPUT_CHANNEL_ID,
                text=text,
                disable_web_page_preview=True
            )
            logger.info("✅ Sinyal LOLOS filter, berhasil diteruskan.")
        except Exception as e:
            logger.error(f"❌ Gagal mengirim pesan: {e}")
    else:
        logger.info("⛔ Sinyal TIDAK LOLOS filter, diabaikan.")

if __name__ == '__main__':
    # Inisialisasi Bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Handler untuk menangkap semua pesan teks di grup
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_incoming_message))
    
    logger.info("🚀 Bot Filtering Dimulai... Menunggu sinyal dari Tracker.")
    app.run_polling()
