import discord
from discord.ext import tasks
from discord import app_commands
from discord.ext import commands
import json
import datetime

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)
user_schedule = {}

# JSON 저장/불러오기
def load_data():
    global user_schedule
    try:
        with open("schedule_data.json", "r") as f:
            user_schedule = json.load(f)
    except FileNotFoundError:
        user_schedule = {}

def save_data():
    with open("schedule_data.json", "w") as f:
        json.dump(user_schedule, f, indent=2)

@tasks.loop(minutes=1)
async def weekly_reset():
    now = datetime.datetime.now()
    if now.weekday() == 0 and now.hour == 1 and now.minute == 0:  # 월요일 01:00
        global user_schedule
        user_schedule = {}
        save_data()
        print("🧹 스케줄 초기화 완료 (월요일 새벽 1시)")


# 봇이 켜질 때
@client.event
async def on_ready():
    load_data()
    try:
        synced = await client.tree.sync()
        print(f"✅ Slash 명령어 {len(synced)}개 동기화됨.")
    except Exception as e:
        print(f"❌ 동기화 실패: {e}")
    print(f"🤖 로그인됨: {client.user}")
    weekly_reset.start()


# 인사 명령어
@client.tree.command(name="인사", description="오늘도 좋은 하루 인사해줘요!")
async def greet(interaction: discord.Interaction):
    await interaction.response.send_message("오늘도 좋은 하루!")

# 스케줄 명령어들
@client.tree.command(name="등록", description="요일과 시간 등록하기")
@app_commands.describe(day="월/화/수/목/금/토/일", time="예: 20:00")
async def register(interaction: discord.Interaction, day: str, time: str):
    try:
        print(f"[DEBUG] 등록 명령 실행됨: {interaction.user}, {day}, {time}")
        user = str(interaction.user.id)
        if user not in user_schedule:
            user_schedule[user] = {}
        user_schedule[user][day] = time
        save_data()
        await interaction.response.send_message(f"{day}요일 {time} 시각으로 등록 완료!", ephemeral=True)
    except Exception as e:
        print(f"[ERROR] 등록 중 오류 발생: {e}")

@client.tree.command(name="확인", description="특정 유저의 특정 요일 스케줄 확인")
@app_commands.describe(user="확인할 유저", day="요일")
async def check_day(interaction: discord.Interaction, user: discord.User, day: str):
    uid = str(user.id)
    schedule = user_schedule.get(uid, {})
    time = schedule.get(day, "등록된 시간이 없어!")
    await interaction.response.send_message(f"{user.display_name}님의 {day}요일 스케줄: {time}")

@client.tree.command(name="오늘확인", description="오늘 날짜 기준으로 스케줄 확인")
@app_commands.describe(user="확인할 유저")
async def check_today(interaction: discord.Interaction, user: discord.User):
    today = ["월", "화", "수", "목", "금", "토", "일"][datetime.datetime.today().weekday()]
    uid = str(user.id)
    schedule = user_schedule.get(uid, {})
    time = schedule.get(today, "등록된 시간이 없어!")
    await interaction.response.send_message(f"오늘({today}) {user.display_name}님의 스케줄: {time}")

@client.tree.command(name="전체확인", description="일주일 전체 스케줄 확인")
@app_commands.describe(user="확인할 유저")
async def check_all(interaction: discord.Interaction, user: discord.User):
    uid = str(user.id)
    schedule = user_schedule.get(uid, {})
    days = ["월", "화", "수", "목", "금", "토", "일"]
    result = [f"{d}요일: {schedule.get(d, '❌ 없음')}" for d in days]
    await interaction.response.send_message(f"{user.display_name}님의 전체 스케줄:\n" + "\n".join(result))

with open("token.txt", "r") as f:
    token = f.read().strip()

client.run(token)

