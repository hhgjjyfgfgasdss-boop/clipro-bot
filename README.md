# 🎬 คลิปโปร — Telegram AI Bot สำหรับ Video Creator

AI ผู้ช่วยสำหรับ Content Creator ไทย ทำงานบน Telegram

## ฟีเจอร์
- 🎙️ ถอดเสียงจากไฟล์เสียง/วิดีโอเป็นข้อความ
- ✂️ แนะนำการตัดต่อ จุด B-Roll Transition
- 🎵 แนะนำเพลงและซาวด์ประกอบ
- 📝 คิดบทและสคริปต์
- 🔍 วิเคราะห์คลิปที่ทำเสร็จแล้ว
- 📈 แนะนำเทรนด์และสไตล์ใหม่ๆ

---

## วิธี Deploy บน Railway

### ขั้นตอนที่ 1 — อัพโหลดไฟล์ไปที่ GitHub
1. สมัคร github.com (ฟรี)
2. กด "New repository" → ตั้งชื่อ เช่น `clipro-bot`
3. อัพโหลดไฟล์ทั้งหมดนี้: `bot.py`, `requirements.txt`, `Procfile`

### ขั้นตอนที่ 2 — Deploy บน Railway
1. เปิด railway.app → คลิก "New Project"
2. เลือก "Deploy from GitHub repo"
3. เลือก repo ที่สร้างไว้
4. Railway จะเริ่ม deploy อัตโนมัติ

### ขั้นตอนที่ 3 — ใส่ API Keys
1. ใน Railway → คลิก project ของคุณ
2. ไปที่ "Variables" tab
3. เพิ่ม 2 ตัวแปร:
   - `TELEGRAM_TOKEN` = Bot Token จาก @BotFather
   - `GEMINI_API_KEY` = API Key จาก aistudio.google.com
4. กด "Deploy" อีกครั้ง

### ขั้นตอนที่ 4 — ทดสอบ
- เปิด Telegram → ค้นหาชื่อบอทของคุณ
- พิมพ์ `/start` → บอทควรตอบกลับ ✅

---

## คำสั่งของบอท
| คำสั่ง | ความหมาย |
|--------|-----------|
| `/start` | เริ่มต้นและแสดงเมนูหลัก |
| `/menu` | แสดงเมนูหลักอีกครั้ง |
| `/clear` | ล้างประวัติการสนทนา |

---

## หมายเหตุ
- Gemini Free Tier: 15 requests/นาที, 1,500 requests/วัน
- วิดีโอสูงสุด ~10MB ต่อไฟล์
- Railway Free: $5 credit/เดือน เพียงพอสำหรับการใช้งานส่วนตัว
