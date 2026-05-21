import pandas as pd
from matplotlib import pyplot as plt
from io import BytesIO

def calculate_averages(data):
    if not data:
        return "Данных пока нет."
    df = pd.DataFrame(data)
    avg_mood = df['mood'].mean()
    avg_work = df['work_hours'].mean()
    avg_sleep = df['sleep_hours'].mean()
    
    return (f"📊 Средние значения за период:\n"
            f"😊 Настроение: {avg_mood:.1f} / 5\n"
            f"💻 Работа/Учеба: {avg_work:.1f} ч\n"
            f"🛏 Сон: {avg_sleep:.1f} ч")

def generate_insights(data):
    if len(data) < 3:
        return "Недостаточно данных для инсайтов. Нужно хотя бы 3 дня."
    
    df = pd.DataFrame(data)
    df['record_date'] = pd.to_datetime(df['record_date'])
    df['day_of_week'] = df['record_date'].dt.day_name()
    
    insights = []
    
    # 1. Дни с лучшим настроением
    mood_by_day = df.groupby('day_of_week')['mood'].mean().sort_values(ascending=False)
    best_day = mood_by_day.index[0]
    insights.append(f"📅 Твое настроение выше всего в <b>{translate_day(best_day)}</b> (ср. {mood_by_day[0]:.1f}).")
    
    # 2. Сон vs Продуктивность
    high_sleep = df[df['sleep_hours'] >= 7]
    low_sleep = df[df['sleep_hours'] < 7]
    
    if not high_sleep.empty and not low_sleep.empty:
        if high_sleep['work_hours'].mean() > low_sleep['work_hours'].mean():
            insights.append("🛏 При сне >7 часов твоя продуктивность <b>выше</b>.")
        else:
            insights.append("🛭 Интересно: при сне <7 часов ты работаешь не меньше (или даже больше)!")
            
    # 3. Переработки vs Настроение
    hard_work = df[df['work_hours'] >= 5]
    light_work = df[df['work_hours'] < 5]
    
    if not hard_work.empty and not light_work.empty:
        if hard_work['mood'].mean() < light_work['mood'].mean():
            insights.append("🔥 Долгая работа/учеба (5+ ч) <b>снижает</b> твое настроение.")
        else:
            insights.append("💪 Долгая работа/учеба не портит тебе настроение. Ты молодец!")
            
    return "\n\n".join(insights)

def generate_plot(data):
    if not data:
        return None
    
    df = pd.DataFrame(data)
    df['record_date'] = pd.to_datetime(df['record_date'])
    
    plt.figure(figsize=(10, 5))
    plt.plot(df['record_date'], df['mood'], label='Настроение (1-5)', marker='o', color='blue')
    plt.plot(df['record_date'], df['sleep_hours'], label='Сон (ч)', marker='s', color='purple')
    plt.plot(df['record_date'], df['work_hours'], label='Работа (ч)', marker='^', color='green')
    
    plt.ylim(0, 10)
    plt.xlabel('Дата')
    plt.title('Твой трекер')
    plt.legend()
    plt.grid(True)
    
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

def translate_day(day):
    days = {
        'Monday': 'Понедельник', 'Tuesday': 'Вторник', 'Wednesday': 'Среда',
        'Thursday': 'Четверг', 'Friday': 'Пятница', 'Saturday': 'Суббота', 'Sunday': 'Воскресенье'
    }
    return days.get(day, day)