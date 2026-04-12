"""
train.py — OnePulse ML Model Training Script

This script trains and saves the scheduling/recommendation model.
Currently uses a rule-based + heuristic mock model.
To upgrade: replace OnePulseModel with a real sklearn/TF model trained
on your engagement data.
"""

import pickle
import os
import random
from datetime import datetime, timedelta

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model.pkl')


class OnePulseModel:
    """
    Smart scheduling and content recommendation model.
    
    Future upgrade path:
    - Collect real engagement data (likes, views, shares) per post time/platform/niche
    - Train a gradient boosting or neural model on that data
    - Replace predict_best_time with model.predict(features)
    """

    HASHTAG_BANK = {
        'youtube': {
            'general':   ['#YouTube', '#Viral', '#Trending', '#Subscribe', '#Creator', '#ContentCreator'],
            'tech':      ['#Tech', '#TechTips', '#Coding', '#Developer', '#AI', '#MachineLearning'],
            'lifestyle': ['#Lifestyle', '#Vlog', '#DayInMyLife', '#Aesthetic', '#MindfulLiving', '#Motivation'],
            'fitness':   ['#Fitness', '#WorkoutMotivation', '#GymLife', '#Health', '#FitFam', '#Cardio'],
            'food':      ['#FoodLovers', '#Cooking', '#Recipe', '#Foodie', '#HomeCook', '#EasyRecipes'],
            'art':       ['#Art', '#Creative', '#Handmade', '#DIY', '#Craft', '#Crochet'],
        },
        'instagram': {
            'general':   ['#Instagram', '#InstaGood', '#PhotoOfTheDay', '#Explore', '#Reels', '#Trending'],
            'tech':      ['#TechLife', '#Innovation', '#StartupLife', '#SoftwareEngineer', '#MacSetup', '#Coding'],
            'lifestyle': ['#LifestyleBlogger', '#GoodVibes', '#Mindfulness', '#SelfCare', '#DailyInspo', '#Wellness'],
            'fitness':   ['#FitnessMotivation', '#BodyTransformation', '#ActiveLife', '#Wellness', '#Sweat', '#Gym'],
            'food':      ['#FoodPhotography', '#EatWell', '#CleanEating', '#Brunch', '#FoodBlogger', '#Yummy'],
            'art':       ['#ArtOfInstagram', '#HandmadeWithLove', '#CrochetCommunity', '#Crafting', '#Maker', '#DIY'],
        }
    }

    CAPTION_TEMPLATES = {
        'youtube': [
            "🎬 {title}\n\n{description}\n\nDon't forget to like, comment & subscribe! 👇",
            "✨ {description}\n\nNew video is LIVE! Watch till the end 🔥\n\n{title}",
            "💡 {title}\n\n{description}\n\nHit the bell 🔔 so you never miss an upload!",
        ],
        'instagram': [
            "✨ {description}\n\nSave this post for later! 💾",
            "💫 {title}\n\n{description}\n\nDouble tap if you agree! ❤️",
            "🌟 {description}\n\nTag someone who needs to see this! 👇",
        ]
    }

    # Peak engagement hours per platform (based on industry research)
    BEST_HOURS = {
        'youtube':   [14, 15, 16, 18, 19, 20],   # 2–8 PM
        'instagram': [7, 8, 11, 12, 17, 18, 19, 21],  # Morning + Evening
    }

    # Niche-specific multipliers (simulate engagement score weighting)
    NICHE_WEIGHTS = {
        'tech':      {'youtube': 0.9, 'instagram': 0.8},
        'lifestyle': {'youtube': 0.85, 'instagram': 0.95},
        'fitness':   {'youtube': 0.88, 'instagram': 0.93},
        'food':      {'youtube': 0.82, 'instagram': 0.97},
        'art':       {'youtube': 0.80, 'instagram': 0.91},
        'general':   {'youtube': 0.75, 'instagram': 0.80},
    }

    def predict_best_time(self, platform, niche='general', days_ahead=1):
        base = datetime.now() + timedelta(days=days_ahead)
        hour = random.choice(self.BEST_HOURS.get(platform, [12, 18]))
        minute = random.choice([0, 15, 30])
        return base.replace(hour=hour, minute=minute, second=0, microsecond=0)

    def generate_hashtags(self, platform, niche='general', count=10):
        bank = self.HASHTAG_BANK.get(platform, {})
        niche_tags = bank.get(niche, bank.get('general', []))
        general_tags = bank.get('general', [])
        combined = list(set(niche_tags + general_tags))
        selected = random.sample(combined, min(count, len(combined)))
        return selected

    def generate_caption(self, platform, title, description, niche='general'):
        templates = self.CAPTION_TEMPLATES.get(platform, self.CAPTION_TEMPLATES['instagram'])
        template = random.choice(templates)
        caption = template.format(title=title, description=description or title)
        hashtags = self.generate_hashtags(platform, niche, count=6)
        return caption + '\n\n' + ' '.join(hashtags)

    def get_optimal_schedule(self, platform, niche='general', count=5):
        weight = self.NICHE_WEIGHTS.get(niche, {}).get(platform, 0.75)
        slots = []
        for i in range(1, count + 1):
            t = self.predict_best_time(platform, niche, days_ahead=i)
            score = round(weight * random.uniform(0.85, 1.0), 2)
            slots.append({
                'datetime': t.isoformat(),
                'label': t.strftime('%A, %b %d at %I:%M %p'),
                'score': min(score, 0.99)
            })
        slots.sort(key=lambda x: x['score'], reverse=True)
        return slots


def train():
    print("🧠 Training OnePulse model...")
    model = OnePulseModel()

    # Validate model output
    test_cases = [
        ('youtube', 'tech'),
        ('instagram', 'lifestyle'),
        ('instagram', 'art'),
    ]

    for platform, niche in test_cases:
        caption = model.generate_caption(platform, 'Test Title', 'Test Description', niche)
        hashtags = model.generate_hashtags(platform, niche)
        schedule = model.get_optimal_schedule(platform, niche, count=3)
        print(f"\n✅ [{platform}/{niche}]")
        print(f"   Caption preview: {caption[:60]}...")
        print(f"   Hashtags: {', '.join(hashtags[:4])}...")
        print(f"   Best time: {schedule[0]['label']} (score: {schedule[0]['score']})")

    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)

    print(f"\n💾 Model saved to {MODEL_PATH}")
    print("✅ Training complete!")


if __name__ == '__main__':
    train()
