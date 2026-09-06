from django.db import migrations


AI_CATEGORY_SLUG = 'ai'
VIDHYORA_IMAGE = 'categories/Vidhyora_AI_Modern_Logo1.png'

VIDHYORA_PLANS = (
    {
        'slug': 'vidhyora-ai-1-month',
        'name': 'Vidhyora AI — 1 Month',
        'duration': '1 month',
        'price': 99,
        'order': 1,
        'flag': 'Starter Plan',
    },
    {
        'slug': 'vidhyora-ai-6-months',
        'name': 'Vidhyora AI — 6 Months',
        'duration': '6 months',
        'price': 299,
        'order': 2,
        'flag': 'Popular',
    },
    {
        'slug': 'vidhyora-ai-1-year',
        'name': 'Vidhyora AI — 1 Year',
        'duration': '1 year',
        'price': 499,
        'order': 3,
        'flag': 'Best Value',
    },
)

ADDITIONAL_AI_PRODUCTS = (
    {
        'slug': 'studysphere-ai-monthly',
        'name': 'StudySphere AI — 1 Month',
        'short_description': 'A multi-model AI study companion for explanations, notes, quizzes and revision.',
        'description': (
            'StudySphere AI brings multiple API-based AI models into one focused learning workspace. '
            'Use ChatGPT and other supported models to understand difficult topics, simplify lessons, '
            'prepare revision notes, create practice questions and plan your studies.'
        ),
        'speciality': 'Learning, explanations, revision notes and practice quizzes',
        'icon': 'fa-graduation-cap',
        'gradient': 'linear-gradient(135deg,#7c3aed,#4f46e5)',
        'flag': 'For Students',
        'order': 4,
    },
    {
        'slug': 'codeorbit-ai-monthly',
        'name': 'CodeOrbit AI — 1 Month',
        'short_description': 'API-powered coding help for development, debugging and technical explanations.',
        'description': (
            'CodeOrbit AI is a multi-model coding assistant for programmers and learners. Use ChatGPT '
            'and other supported AI models to explain code, find bugs, plan features, write tests and '
            'work across popular programming languages and frameworks.'
        ),
        'speciality': 'Programming, debugging, code explanations and test generation',
        'icon': 'fa-code',
        'gradient': 'linear-gradient(135deg,#0f172a,#2563eb)',
        'flag': 'For Developers',
        'order': 5,
    },
    {
        'slug': 'writebloom-ai-monthly',
        'name': 'WriteBloom AI — 1 Month',
        'short_description': 'A multi-model writing assistant for content, emails, scripts and polished copy.',
        'description': (
            'WriteBloom AI combines multiple API-based AI models in a writing-focused workspace. Use '
            'ChatGPT and other supported models to draft and improve articles, emails, social posts, '
            'video scripts, product copy and other everyday content.'
        ),
        'speciality': 'Articles, emails, scripts, social content and rewriting',
        'icon': 'fa-pen-nib',
        'gradient': 'linear-gradient(135deg,#db2777,#f97316)',
        'flag': 'For Creators',
        'order': 6,
    },
    {
        'slug': 'visionspark-ai-monthly',
        'name': 'VisionSpark AI — 1 Month',
        'short_description': 'AI assistance for understanding images and developing creative visual ideas.',
        'description': (
            'VisionSpark AI provides access to supported vision-capable and general AI models through '
            'API-based integrations. Analyse images, explore visual concepts, improve creative prompts '
            'and get practical feedback for presentations, posts and design ideas.'
        ),
        'speciality': 'Image understanding, visual concepts, prompts and creative feedback',
        'icon': 'fa-eye',
        'gradient': 'linear-gradient(135deg,#0891b2,#10b981)',
        'flag': 'Vision AI',
        'order': 7,
    },
    {
        'slug': 'taskpilot-ai-monthly',
        'name': 'TaskPilot AI — 1 Month',
        'short_description': 'A practical multi-model assistant for planning, research and daily productivity.',
        'description': (
            'TaskPilot AI is an API-powered productivity workspace with ChatGPT and other supported AI '
            'models. Turn ideas into action plans, summarise information, organise projects, brainstorm '
            'solutions and prepare clear professional documents from one convenient interface.'
        ),
        'speciality': 'Planning, summaries, research, organisation and business productivity',
        'icon': 'fa-list-check',
        'gradient': 'linear-gradient(135deg,#0369a1,#14b8a6)',
        'flag': 'Productivity AI',
        'order': 8,
    },
)


def _description(duration):
    return (
        "Get {duration} of Vidhyora AI, a multi-model AI workspace powered "
        "through API-based integrations. Access ChatGPT and other supported "
        "AI models from one place for studying, writing, research, coding, "
        "brainstorming, summarising and everyday questions. Switch models to "
        "match the task and benefit from ongoing model and product updates."
    ).format(duration=duration)


def _specs(duration):
    return (
        f"Plan duration: {duration}\n"
        "Access: Multiple API-based AI models in one workspace\n"
        "Models: ChatGPT and other supported AI models\n"
        "Use cases: Study, writing, research, coding, brainstorming and summaries\n"
        "Platform: Web access at vidhyora.online\n"
        "Updates: Ongoing model, feature and reliability improvements\n"
        "Delivery: Digital subscription activation after payment confirmation\n"
        "Availability: Individual models and usage are subject to provider availability and plan terms"
    )


def _additional_product_specs(speciality):
    return (
        "Plan duration: 1 month\n"
        "Access: Multiple API-based AI models in one workspace\n"
        "Models: ChatGPT and other supported AI models\n"
        f"Best for: {speciality}\n"
        "Delivery: Digital subscription activation after payment confirmation\n"
        "Availability: Individual models and usage are subject to provider availability and plan terms"
    )


def seed_vidhyora_ai_plans(apps, schema_editor):
    Category = apps.get_model('myapp', 'Category')
    Product = apps.get_model('myapp', 'Product')

    category, _ = Category.objects.get_or_create(
        slug=AI_CATEGORY_SLUG,
        defaults={
            'name': 'AI',
            'description': 'AI assistants and multi-model subscriptions',
            'image': VIDHYORA_IMAGE,
            'order': 0,
            'is_active': True,
        },
    )
    category.name = 'AI'
    category.description = 'AI assistants and multi-model subscriptions'
    category.is_active = True
    if not category.image:
        category.image = VIDHYORA_IMAGE
    category.save(update_fields=['name', 'description', 'image', 'is_active'])

    for plan in VIDHYORA_PLANS:
        Product.objects.update_or_create(
            slug=plan['slug'],
            defaults={
                'category': category,
                'brand': 'Vidhyora',
                'name': plan['name'],
                'short_description': (
                    f"{plan['duration'].title()} access to ChatGPT and other "
                    "API-based AI models in one workspace."
                ),
                'description': _description(plan['duration']),
                'specs': _specs(plan['duration']),
                'price': plan['price'],
                'mrp': plan['price'],
                'image': VIDHYORA_IMAGE,
                'icon': 'fa-brain',
                'gradient': 'linear-gradient(135deg,#6d28d9,#2563eb)',
                'flag': plan['flag'],
                'stock_status': 'Available',
                'tags': 'AI, API models, ChatGPT, multi-model, digital subscription',
                'rating': 4.8,
                'reviews_count': 0,
                'is_active': True,
                'is_digital': True,
                'order': plan['order'],
            },
        )

    for product in ADDITIONAL_AI_PRODUCTS:
        Product.objects.update_or_create(
            slug=product['slug'],
            defaults={
                'category': category,
                'brand': product['name'].split(' AI')[0],
                'name': product['name'],
                'short_description': product['short_description'],
                'description': product['description'],
                'specs': _additional_product_specs(product['speciality']),
                'price': 99,
                'mrp': 99,
                'icon': product['icon'],
                'gradient': product['gradient'],
                'flag': product['flag'],
                'stock_status': 'Available',
                'tags': 'AI, API models, ChatGPT, multi-model, digital subscription',
                'rating': 4.8,
                'reviews_count': 0,
                'is_active': True,
                'is_digital': True,
                'order': product['order'],
            },
        )


def unseed_vidhyora_ai_plans(apps, schema_editor):
    Product = apps.get_model('myapp', 'Product')
    slugs = [plan['slug'] for plan in VIDHYORA_PLANS]
    slugs.extend(product['slug'] for product in ADDITIONAL_AI_PRODUCTS)
    Product.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0044_remove_personal_name_and_address_knowledge'),
    ]

    operations = [
        migrations.RunPython(seed_vidhyora_ai_plans, unseed_vidhyora_ai_plans),
    ]
