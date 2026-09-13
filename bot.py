import os
import re
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# ==========================================
# 🔑 KREDENSIAL RAHASIA (DIAMBIL DARI GITHUB SECRETS)
# ==========================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TARGET_CHANNEL_ID = os.environ.get("TARGET_CHANNEL_ID")

def parse_pesan_gmgn(teks):
    jaringan = "solana"
    if "ROBINHOOD" in teks or "BASE" in teks:
        jaringan = "base"

    data = {
        'network': jaringan, 'name': 'Unknown', 'ticker': 'UNKNOWN', 'ca': 'None',
        'mc_usd': 0.0, 'lp_usd': 0.0, 'bundle_pct': 0.0, 'insider_count': 0,
        'top10_pct': 0.0, 'bot_pct': 0.0, 'smart_count': 0, 'creator_launches': 0,
        'top1_pct': 0.0, 'is_ai_narrative': False
    }

    try:
        name_match = re.search(r'([a-zA-Z0-9.\s]+)\s*\(\$([a-zA-Z0-9/]+)\)', teks)
        if name_match:
            data['name'] = name_match.group(1).strip()
            data['ticker'] = name_match.group(2).strip()

        ca_sol = re.search(r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b', teks)
        ca_base = re.search(r'\b0x[a-fA-F0-9]{40}\b', teks)
        if ca_sol: data['ca'] = ca_sol.group(0)
        elif ca_base: data['ca'] = ca_base.group(0)

        mc_match = re.search(r'MC\s*\$?([0-9.]+[KMB]?)', teks)
        lp_match = re.search(r'LP\s*\$?([0-9.]+[KMB]?)', teks)
        
        def konversi_angka(teks_angka):
            if not teks_angka: return 0.0
            teks_angka = teks_angka.upper()
            if 'K' in teks_angka: return float(teks_angka.replace('K', '')) * 1000
            if 'M' in teks_angka: return float(teks_angka.replace('M', '')) * 1000000
            return float(teks_angka)

        if mc_match: data['mc_usd'] = konversi_angka(mc_match.group(1))
        if lp_match: data['lp_usd'] = konversi_angka(lp_match.group(1))

        top10_match = re.search(r'Top10\s*([0-9.]+)%', teks)
        if top10_match: data['top10_pct'] = float(top10_match.group(1))

        # Mengambil persentase Wallet Top 1 dari baris TH di bot GMGN
        th_match = re.search(r'TH\s*([0-9.]+)%', teks)
        if th_match: data['top1_pct'] = float(th_match.group(1))

        bundle_match = re.search(r'Bundle\s*([0-9.]+)%', teks)
        insider_match = re.search(r'Insider\s*([0-9]+)', teks)
        smart_match = re.search(r'Smart\s*([0-9]+)', teks)
        bot_match = re.search(r'Bot\s*([0-9.]+)%', teks)
        creator_match = re.search(r'Creator launches\s*([0-9]+)', teks)

        if bundle_match: data['bundle_pct'] = float(bundle_match.group(1))
        if insider_match: data['insider_count'] = int(insider_match.group(1))
        if smart_match: data['smart_count'] = int(smart_match.group(1))
        if bot_match: data['bot_pct'] = float(bot_match.group(1))
        if creator_match: data['creator_launches'] = int(creator_match.group(1))

        if any(x in teks.upper() for x in ["AI", "NVIDIA", "TECH", "ROBOT"]):
            data['is_ai_narrative'] = True
    except: pass
    return data

def jalankan_formula_emas(data):
    jaringan = data['network']
    rekomendasi = "🚨 MERAH (SKIP)"
    alasan = []
    rasio_lp_mc = (data['lp_usd'] / data['mc_usd']) * 100 if data['mc_usd'] > 0 else 0

    # 🟢 1. JARINGAN BASE / ROBINHOOD (DIAMOND HANDS)
    if jaringan == "base":
        rekomendasi = "🟢 HIJAU PEKAT (SIKAT DIAMOND HANDS)"
        if data['bundle_pct'] > 0.0:
            rekomendasi = "🚨 MERAH (SKIP)"
            alasan.append(f"Bundle {data['bundle_pct']}% (Wajib 0.0%)")
        if data['insider_count'] >= 5:
            rekomendasi = "🚨 MERAH (SKIP)"
            alasan.append(f"Insider kebanyakan: {data['insider_count']} wallet (Wajib < 5)")
        if data['smart_count'] <= 0:
            rekomendasi = "🚨 MERAH (SKIP)"
            alasan.append(f"Smart Money {data['smart_count']} (Wajib > 0)")
        if rasio_lp_mc < 30.0 or rasio_lp_mc > 50.0:
            rekomendasi = "🚨 MERAH (SKIP)"
            alasan.append(f"Rasio LP/MC {rasio_lp_mc:.1f}% (Wajib 30%-50%)")
        if data['top10_pct'] >= 25.0:
            rekomendasi = "🚨 MERAH (SKIP)"
            alasan.append(f"Top 10 berkuasa: {data['top10_pct']}% (Wajib < 25%)")
        if data['bot_pct'] >= 55.0:
            rekomendasi = "🚨 MERAH (SKIP)"
            alasan.append(f"Volume Bot tinggi: {data['bot_pct']}% (Wajib < 55%)")
            
    # 🟡 / 🔥 2. JARINGAN SOLANA (SCALPING & MOMENTUM)
    else:
        rekomendasi = "🟡 KUNING (SCALPING HIT & RUN)"
        
        # Koin Dasar Lantai (MC < $20K)
        if data['mc_usd'] <= 20000 and rasio_lp_mc < 70.0:
            rekomendasi = "🚨 MERAH (SKIP)"
            alasan.append(f"Koin dasar tapi LP tipis: {rasio_lp_mc:.1f}% (Wajib > 70%)")
            
        # Koin Lulus Graduated (MC > $150K)
        if data['mc_usd'] >= 150000 and data['top10_pct'] >= 5.0:
            rekomendasi = "🚨 MERAH (SKIP)"
            alasan.append(f"Koin lulus tapi Top 10 gemuk: {data['top10_pct']}% (Wajib < 5%)")
            
        # Kondisi Bundle Tim Internal (> 40%)
        if data['bundle_pct'] > 40.0:
            if data['top1_pct'] < 15.0:
                rekomendasi = "🟡 KUNING (SCALPING - TIM BUNDLE LOCK)"
            else:
                rekomendasi = "🚨 MERAH (SKIP)"
                alasan.append(f"Bundle > 40% tapi Top 1 jebol: {data['top1_pct']}% (Wajib < 15%)")
                
        # Kondisi Penyelamat Malpraktik Dev & Bot Masif
        if data['bot_pct'] > 80.0 and data['creator_launches'] > 5000:
            if data['is_ai_narrative']:
                rekomendasi = "🔥 EMAS (HIGH RISK MOMENTUM PUMP)"
                alasan.append("⚠️ DISELAMATKAN: Faktor Narasi AI/Tech Sangat Kuat")
            else:
                rekomendasi = "🚨 MERAH (SKIP)"
                alasan.append(f"Bot {data['bot_pct']}% & Dev Spam {data['creator_launches']} koin tanpa Narasi AI")

    return rekomendasi, alasan

async def handle_incoming_message(update: Update, context: ContextTypes.ContextWithBaseArgs):
    teks_masuk = update.message.text
    if not teks_masuk: return
    data = parse_pesan_gmgn(teks_masuk)
    if data['ca'] == 'None': return

    status_msg = await update.message.reply_text(f"⚔️ Memproses token {data['name']} (${data['ticker']}) via Formula Emas...")
    status, catatan = jalankan_formula_emas(data)

    pesan_hasil = (
        f"⚡ *FORMULA EMAS DEGEN TRADING SIGNAL* ⚡\n"
        f"----------------------------------------\n"
        f"🪙 Token: {data['name']} (${data['ticker']})\n"
        f"🌐 Jaringan: {data['network'].upper()}\n"
        f"📄 CA: `{data['ca']}`\n\n"
        f"💸 MC: ${data['mc_usd']:,}  ·  LP: ${data['lp_usd']:,}\n"
        f"📦 Bundle: {data['bundle_pct']}%  ·  Insider: {data['insider_count']} w\n"
        f"👥 Top 10 Holders: {data['top10_pct']}%\n"
        f"🤖 Bot: {data['bot_pct']}%  ·  Smart Money: {data['smart_count']}\n"
        f"----------------------------------------\n"
        f"📊 *STATUS HASIL FILTER*:\n"
        f"➡️ {status}\n"
    )
    if catatan:
        pesan_hasil += "\n🔎 *Detail Alasan*:\n"
        for item in catatan: pesan_hasil += f"• {item}\n"

    if "🚨 MERAH" not in status:
        try:
            await context.bot.send_message(chat_id=TARGET_CHANNEL_ID, text=pesan_hasil, parse_mode="Markdown")
            await status_msg.edit_text("🟢 **LOLOS FILTER!** Sinyal dikirim ke Channel pribadi lu.")
        except Exception as e:
            await status_msg.edit_text(f"❌ Bot gagal kirim ke Channel. Jadikan bot ADMIN dulu! Error: {e}")
    else:
        await status_msg.edit_text("🚨 **SAMPAH DITOLAK FORMULA EMAS!**")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_incoming_message))
    print("Bot GitHub Actions Aktif...")
    app.run_polling()

if __name__ == '__main__':
    main()
