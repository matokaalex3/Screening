import os
import re
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TARGET_CHANNEL_ID = os.environ.get("TARGET_CHANNEL_ID")

def parse_pesan_gmgn(teks):
    jaringan = "base" if any(x in teks for x in ["ROBINHOOD", "BASE"]) else "solana"
    data = {'network': jaringan, 'name': 'Unknown', 'ticker': 'UNKNOWN', 'ca': 'None', 'mc_usd': 0.0, 'lp_usd': 0.0, 'bundle_pct': 0.0, 'insider_count': 0, 'top10_pct': 0.0, 'bot_pct': 0.0, 'smart_count': 0, 'creator_launches': 0, 'top1_pct': 0.0, 'is_ai_narrative': False}
    try:
        n_match = re.search(r'([a-zA-Z0-9.\s]+)\s*\(\$([a-zA-Z0-9/]+)\)', teks)
        if n_match: data['name'], data['ticker'] = n_match.group(1).strip(), n_match.group(2).strip()
        ca_sol = re.search(r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b', teks)
        ca_base = re.search(r'\b0x[a-fA-F0-9]{40}\b', teks)
        if ca_sol: data['ca'] = ca_sol.group(0)
        elif ca_base: data['ca'] = ca_base.group(0)
        mc_m = re.search(r'MC\s*\$?([0-9.]+[KMB]?)', teks)
        lp_m = re.search(r'LP\s*\$?([0-9.]+[KMB]?)', teks)
        def conv(t):
            if not t: return 0.0
            t = t.upper()
            if 'K' in t: return float(t.replace('K', '')) * 1000
            if 'M' in t: return float(t.replace('M', '')) * 1000000
            return float(t)
        if mc_m: data['mc_usd'] = conv(mc_m.group(1))
        if lp_m: data['lp_usd'] = conv(lp_m.group(1))
        t10 = re.search(r'Top10\s*([0-9.]+)%', teks)
        if t10: data['top10_pct'] = float(t10.group(1))
        th = re.search(r'TH\s*([0-9.]+)%', teks)
        if th: data['top1_pct'] = float(th.group(1))
        bdl = re.search(r'Bundle\s*([0-9.]+)%', teks)
        ins = re.search(r'Insider\s*([0-9]+)', teks)
        smr = re.search(r'Smart\s*([0-9]+)', teks)
        bot = re.search(r'Bot\s*([0-9.]+)%', teks)
        crt = re.search(r'Creator launches\s*([0-9]+)', teks)
        if bdl: data['bundle_pct'] = float(bdl.group(1))
        if ins: data['insider_count'] = int(ins.group(1))
        if smr: data['smart_count'] = int(smr.group(1))
        if bot: data['bot_pct'] = float(bot.group(1))
        if crt: data['creator_launches'] = int(crt.group(1))
        if any(x in teks.upper() for x in ["AI", "NVIDIA", "TECH"]): data['is_ai_narrative'] = True
    except: pass
    return data

def jalankan_formula_emas(data):
    jaringan = data['network']
    rekomendasi, alasan = "🚨 MERAH (SKIP)", []
    rasio = (data['lp_usd'] / data['mc_usd']) * 100 if data['mc_usd'] > 0 else 0
    if jaringan == "base":
        rekomendasi = "🟢 HIJAU PEKAT (SIKAT DIAMOND HANDS)"
        if data['bundle_pct'] > 0.0: rekomendasi = "🚨 MERAH (SKIP)"; alasan.append("Bundle > 0%")
        if data['insider_count'] >= 5: rekomendasi = "🚨 MERAH (SKIP)"; alasan.append("Insider >= 5")
        if data['smart_count'] <= 0: rekomendasi = "🚨 MERAH (SKIP)"; alasan.append("Smart Money 0")
        if rasio < 30.0 or rasio > 50.0: rekomendasi = "🚨 MERAH (SKIP)"; alasan.append(f"LP/MC {rasio:.1f}%")
        if data['top10_pct'] >= 25.0: rekomendasi = "🚨 MERAH (SKIP)"; alasan.append("Top 10 >= 25%")
        if data['bot_pct'] >= 55.0: rekomendasi = "🚨 MERAH (SKIP)"; alasan.append("Bot >= 55%")
    else:
        rekomendasi = "🟡 KUNING (SCALPING)"
        if data['mc_usd'] <= 20000 and rasio < 70.0: rekomendasi = "🚨 MERAH (SKIP)"; alasan.append("LP Lantai tipis")
        if data['mc_usd'] >= 150000 and data['top10_pct'] >= 5.0: rekomendasi = "🚨 MERAH (SKIP)"; alasan.append("Graduated Top 10 gemuk")
        if data['bundle_pct'] > 40.0 and data['top1_pct'] >= 15.0: rekomendasi = "🚨 MERAH (SKIP)"; alasan.append("Bundle jebol")
        if data['bot_pct'] > 80.0 and data['creator_launches'] > 5000:
            if data['is_ai_narrative']: rekomendasi, _ = "🔥 EMAS (HIGH RISK PUMP)", alasan.append("Saved by AI")
            else: rekomendasi = "🚨 MERAH (SKIP)"; alasan.append("Bot tinggi no AI")
    return rekomendasi, alasan

async def handle_incoming_message(update: Update, context: CallbackContext):
    teks = update.message.text
    if not teks: return
    data = parse_pesan_gmgn(teks)
    if data['ca'] == 'None': return
    status_msg = await update.message.reply_text(f"⚔️ Memproses {data['name']}...")
    status, catatan = jalankan_formula_emas(data)
    pesan = f"⚡ *FORMULA EMAS DEGEN SIGNAL* ⚡\n----------------------------------------\n🪙 Token: {data['name']} (${data['ticker']})\n🌐 Jaringan: {data['network'].upper()}\n📄 CA: `{data['ca']}`\n\n💸 MC: ${data['mc_usd']:,} · LP: ${data['lp_usd']:,}\n📦 Bundle: {data['bundle_pct']}% · Insider: {data['insider_count']} w\n👥 Top 10: {data['top10_pct']}%\n🤖 Bot: {data['bot_pct']}% · Smart: {data['smart_count']}\n----------------------------------------\n📊 *STATUS*:\n➡️ {status}\n"
    if catatan:
        pesan += "\n🔎 *Detail*:\n"
        for item in catatan: pesan += f"• {item}\n"
    if "🚨 MERAH" not in status:
        try:
            await context.bot.send_message(chat_id=TARGET_CHANNEL_ID, text=pesan, parse_mode="Markdown")
            await status_msg.edit_text("🟢 **LOLOS FILTER!** Masuk Channel.")
        except: await status_msg.edit_text("❌ Gagal kirim. Pastikan bot ADMIN di channel!")
    else: await status_msg.edit_text("🚨 **SAMPAH DITOLAK FORMULA EMAS!**")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_incoming_message))
    app.run_polling()

if __name__ == '__main__':
    main()
