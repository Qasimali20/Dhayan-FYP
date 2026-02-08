"""
Seed 5 distinct speech therapy activities.
Usage:  python manage.py seed_speech_activities
        python manage.py seed_speech_activities --force   (replace existing)
"""
from django.core.management.base import BaseCommand
from speech.models import SpeechActivity


ACTIVITIES = [
    # ━━━━━━━━━ 1. Repetition Practice ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SKILL: Imitation, articulation, phonology, verbal working memory
    # MECHANIC: Therapist models → child repeats exactly
    {
        "name": "Repetition Practice",
        "category": "repetition",
        "description": (
            "Child listens and repeats words, phrases, or sentences modelled "
            "by the therapist. Targets articulation accuracy, phonological "
            "patterns, prosody, and verbal working memory. Difficulty scales "
            "from single-syllable words up to complex sentences."
        ),
        "prompt_type": "text",
        "prompt_payload": {
            "text": "Listen and say: '{phrase}'",
            "phrases_pool": [
                # Single words (1-syllable)
                "cat", "ball", "fish", "sun", "cup",
                # Single words (2-syllable)
                "apple", "water", "happy", "rabbit", "window",
                # Single words (3-syllable)
                "banana", "elephant", "umbrella", "butterfly", "dinosaur",
                # Short phrases
                "big red ball", "I want more", "my turn please",
                "look at me", "come here now", "I see it",
                "open the door", "thank you so much",
                # Full sentences
                "The cat is sitting on the mat.",
                "I want to play with the ball.",
                "She is eating a red apple.",
                "The dog is running in the park.",
                "We are going to the zoo tomorrow.",
                "Can you pass me the blue crayon?",
                "What a beautiful butterfly that is!",
                "I am so excited about my birthday!",
            ],
        },
        "expected_text": "",
        "language": "en",
        "difficulty_level": 1,
        "difficulty_json": {
            "levels": {
                "1": {"type": "single words", "examples": ["cat", "ball", "apple"]},
                "2": {"type": "short phrases (2-4 words)", "examples": ["big red ball", "I want more"]},
                "3": {"type": "full sentences (5+ words)", "examples": ["The cat is sitting on the mat."]},
            }
        },
        "prompt_levels": [
            {"level": 0, "instruction": "Full model: Say it together with the child, repeat if needed"},
            {"level": 1, "instruction": "Partial model: Say the first sound/word, child completes the rest"},
            {"level": 2, "instruction": "Visual/gestural: Show written text or picture, point to mouth shape"},
            {"level": 3, "instruction": "Independent: Play audio once, child produces from memory"},
        ],
    },

    # ━━━━━━━━━ 2. Picture Naming ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SKILL: Word retrieval, expressive vocabulary, semantic access
    # MECHANIC: Show concept → child retrieves & says the label (no model given)
    {
        "name": "Picture Naming",
        "category": "picture_naming",
        "description": (
            "Child is given a semantic cue or description and must name "
            "the object. Targets expressive vocabulary, word retrieval "
            "speed, and semantic organisation. Unlike repetition, the "
            "child must independently access and produce the word."
        ),
        "prompt_type": "text",
        "prompt_payload": {
            "text": "What is this? It's a: '{item}'",
            "items_pool": [
                {"word": "cat",       "semantic_cue": "An animal that says meow"},
                {"word": "apple",     "semantic_cue": "A red fruit you eat"},
                {"word": "car",       "semantic_cue": "You ride in it on the road"},
                {"word": "hand",      "semantic_cue": "Part of your body with five fingers"},
                {"word": "shoe",      "semantic_cue": "You wear it on your foot"},
                {"word": "banana",    "semantic_cue": "A yellow fruit monkeys love"},
                {"word": "bird",      "semantic_cue": "It has wings and can fly"},
                {"word": "chair",     "semantic_cue": "You sit on it"},
                {"word": "spoon",     "semantic_cue": "You eat soup with it"},
                {"word": "flower",    "semantic_cue": "It grows in the garden and smells nice"},
                {"word": "umbrella",  "semantic_cue": "You hold it when it rains"},
                {"word": "truck",     "semantic_cue": "A big vehicle that carries heavy things"},
                {"word": "book",      "semantic_cue": "You read stories in it"},
                {"word": "hat",       "semantic_cue": "You wear it on your head"},
                {"word": "moon",      "semantic_cue": "It shines in the sky at night"},
            ],
        },
        "expected_text": "",
        "language": "en",
        "difficulty_level": 1,
        "difficulty_json": {
            "levels": {
                "1": {"items": "high-frequency 1-syllable", "examples": ["cat", "ball", "hat"]},
                "2": {"items": "medium-frequency 2-syllable", "examples": ["apple", "flower", "rabbit"]},
                "3": {"items": "low-frequency 3+ syllable", "examples": ["umbrella", "helicopter", "refrigerator"]},
            }
        },
        "prompt_levels": [
            {"level": 0, "instruction": "Full model: 'This is a cat. Say: cat.'"},
            {"level": 1, "instruction": "Phonemic cue: 'It starts with /k/...'"},
            {"level": 2, "instruction": "Semantic cue: 'It's an animal that says meow...'"},
            {"level": 3, "instruction": "Independent: 'What is this?' — child names it freely"},
        ],
    },

    # ━━━━━━━━━ 3. Question & Answer ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SKILL: Comprehension, reasoning, formulation, pragmatic response
    # MECHANIC: Therapist asks → child thinks & formulates an answer
    {
        "name": "Question & Answer",
        "category": "questions",
        "description": (
            "Child listens to a question and formulates an answer. "
            "Covers yes/no, what, where, who, why, and when. "
            "Targets auditory comprehension, logical reasoning, "
            "and spontaneous sentence formulation — the child must "
            "generate language, not just imitate."
        ),
        "prompt_type": "text",
        "prompt_payload": {
            "text": "{question}",
            "questions_pool": [
                # Yes/No — concrete
                {"question": "Is the sky blue?", "answer": "yes", "type": "yes_no"},
                {"question": "Do fish fly?", "answer": "no", "type": "yes_no"},
                {"question": "Can you eat an apple?", "answer": "yes", "type": "yes_no"},
                {"question": "Is ice hot?", "answer": "no", "type": "yes_no"},
                {"question": "Do dogs bark?", "answer": "yes", "type": "yes_no"},
                {"question": "Can a chair talk?", "answer": "no", "type": "yes_no"},
                # What
                {"question": "What do you eat for breakfast?", "type": "what", "expected_keywords": ["cereal", "eggs", "toast", "food", "pancakes"]},
                {"question": "What color is the grass?", "type": "what", "expected_keywords": ["green"]},
                {"question": "What sound does a cat make?", "type": "what", "expected_keywords": ["meow"]},
                {"question": "What do you do when you are cold?", "type": "what", "expected_keywords": ["jacket", "blanket", "warm", "coat"]},
                # Where
                {"question": "Where do fish live?", "type": "where", "expected_keywords": ["water", "sea", "ocean", "river"]},
                {"question": "Where do you sleep?", "type": "where", "expected_keywords": ["bed", "room", "home"]},
                {"question": "Where do we buy food?", "type": "where", "expected_keywords": ["store", "shop", "market"]},
                # Who
                {"question": "Who reads you stories?", "type": "who", "expected_keywords": ["mom", "dad", "teacher", "parent"]},
                {"question": "Who helps you at school?", "type": "who", "expected_keywords": ["teacher"]},
                # Why / When
                {"question": "Why do we brush our teeth?", "type": "why", "expected_keywords": ["clean", "healthy", "cavity"]},
                {"question": "Why do we wear shoes?", "type": "why", "expected_keywords": ["protect", "feet", "walk"]},
                {"question": "When do you eat lunch?", "type": "when", "expected_keywords": ["noon", "afternoon", "midday"]},
            ],
        },
        "expected_text": "",
        "language": "en",
        "difficulty_level": 2,
        "difficulty_json": {
            "levels": {
                "1": {"type": "yes/no (concrete)", "examples": ["Is the sky blue?", "Do fish fly?"]},
                "2": {"type": "what/where/who", "examples": ["What color is the grass?", "Where do fish live?"]},
                "3": {"type": "why/when/how (inference)", "examples": ["Why do we brush our teeth?"]},
            }
        },
        "prompt_levels": [
            {"level": 0, "instruction": "Full model: Ask question, give answer, child repeats answer"},
            {"level": 1, "instruction": "Sentence starter: 'Fish live in the ___'"},
            {"level": 2, "instruction": "Forced choice: 'Do fish live in water or in the sky?'"},
            {"level": 3, "instruction": "Independent: Ask question, wait for child's own answer"},
        ],
    },

    # ━━━━━━━━━ 4. Story Retell ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SKILL: Narrative, sequencing, verbal memory, connected speech
    # MECHANIC: Listen to short story → retell in own words (free production)
    {
        "name": "Story Retell",
        "category": "story_retell",
        "description": (
            "Child listens to a short story (2–4 sentences) and retells it "
            "in their own words. Targets narrative structure, temporal "
            "sequencing, cause-effect reasoning, and connected speech "
            "production. This is the most linguistically demanding task — "
            "the child must comprehend, remember, organise, and produce."
        ),
        "prompt_type": "text",
        "prompt_payload": {
            "text": "Listen to the story, then tell it back to me:\n\n'{sentence}'",
            "sentences_pool": [
                "A little dog found a bone. He was so happy! He ran home to eat it.",
                "The girl put on her boots. She jumped in every puddle. Her socks got all wet!",
                "A bird made a nest in the tree. She laid three eggs. Soon the baby birds hatched.",
                "Tom was hungry. He made a peanut butter sandwich. It was very yummy!",
                "It started to rain. The children ran inside. They played with blocks until the sun came out.",
                "A frog sat on a lily pad. A fly buzzed past. The frog caught it with his long tongue!",
                "Emma lost her teddy bear. She looked everywhere. She found it under her bed!",
                "The bus came to school. All the kids got off. They ran to the playground to play.",
                "Mom baked cookies. The kitchen smelled so good! We ate them with cold milk.",
                "A caterpillar ate lots of leaves. It made a cocoon. It turned into a beautiful butterfly!",
            ],
        },
        "expected_text": "",
        "language": "en",
        "difficulty_level": 3,
        "difficulty_json": {
            "levels": {
                "1": {"type": "2-sentence simple narrative", "examples": ["A dog found a bone. He was happy!"]},
                "2": {"type": "3-sentence sequence", "examples": ["First... then... finally..."]},
                "3": {"type": "4+ sentences with cause/effect", "examples": ["It rained, so they went inside and played."]},
            }
        },
        "prompt_levels": [
            {"level": 0, "instruction": "Full model: Retell together sentence by sentence, child echoes"},
            {"level": 1, "instruction": "Partial: Start each sentence, child completes it"},
            {"level": 2, "instruction": "Sequencing cues: 'What happened first? Then what? How did it end?'"},
            {"level": 3, "instruction": "Independent: Read story once, child retells freely in own words"},
        ],
    },

    # ━━━━━━━━━ 5. Category Naming ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SKILL: Semantic fluency, divergent word retrieval, vocabulary breadth
    # MECHANIC: Given a category → child generates as many items as possible
    {
        "name": "Category Naming",
        "category": "category_naming",
        "description": (
            "Child names as many items as they can from a given category "
            "(animals, food, colours, etc.). Targets semantic fluency, "
            "divergent word retrieval, and vocabulary breadth. Unlike other "
            "tasks, there is no single correct answer — the child must "
            "self-generate multiple words from long-term memory."
        ),
        "prompt_type": "text",
        "prompt_payload": {
            "text": "{question}",
            "questions_pool": [
                {"question": "Tell me as many animals as you can!",          "expected_keywords": ["cat", "dog", "bird", "fish", "cow", "horse", "lion", "elephant"]},
                {"question": "Name some fruits you know.",                    "expected_keywords": ["apple", "banana", "orange", "grape", "mango", "strawberry", "watermelon"]},
                {"question": "What colors can you think of?",                 "expected_keywords": ["red", "blue", "green", "yellow", "purple", "orange", "pink", "black", "white"]},
                {"question": "Tell me parts of the body.",                    "expected_keywords": ["head", "hand", "arm", "leg", "foot", "nose", "eye", "ear", "mouth"]},
                {"question": "Name some things you wear.",                    "expected_keywords": ["shirt", "pants", "shoes", "hat", "socks", "jacket", "dress", "coat"]},
                {"question": "What things can you find in a kitchen?",        "expected_keywords": ["spoon", "fork", "plate", "cup", "pot", "fridge", "stove", "knife"]},
                {"question": "Name some vehicles.",                           "expected_keywords": ["car", "bus", "truck", "bike", "plane", "train", "boat", "helicopter"]},
                {"question": "Tell me some things you see at school.",        "expected_keywords": ["book", "pencil", "desk", "teacher", "board", "crayon", "chair", "backpack"]},
                {"question": "What toys do you know?",                        "expected_keywords": ["ball", "doll", "blocks", "puzzle", "car", "teddy", "lego"]},
                {"question": "Name some things that are round.",              "expected_keywords": ["ball", "wheel", "sun", "moon", "clock", "orange", "coin"]},
            ],
        },
        "expected_text": "",
        "language": "en",
        "difficulty_level": 2,
        "difficulty_json": {
            "levels": {
                "1": {"target": "2-3 items", "examples": ["Name 2 animals"]},
                "2": {"target": "4-5 items", "examples": ["Name 5 fruits"]},
                "3": {"target": "6+ items", "examples": ["Name as many colors as you can"]},
            }
        },
        "prompt_levels": [
            {"level": 0, "instruction": "Full model: Name 2 items together, child adds more"},
            {"level": 1, "instruction": "Phonemic cue: 'Think of one that starts with /d/...'"},
            {"level": 2, "instruction": "Semantic cue: 'Think of one with stripes...'"},
            {"level": 3, "instruction": "Independent: Give the category, child lists items freely"},
        ],
    },
]


class Command(BaseCommand):
    help = "Seed default speech therapy activities"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Re-create even if they exist")

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        for data in ACTIVITIES:
            exists = SpeechActivity.objects.filter(
                name=data["name"], category=data["category"]
            ).exists()

            if exists and not options["force"]:
                skipped += 1
                self.stdout.write(f"  ⏭  {data['name']} (already exists)")
                continue

            if exists:
                SpeechActivity.objects.filter(name=data["name"], category=data["category"]).delete()

            SpeechActivity.objects.create(**data)
            created += 1
            self.stdout.write(self.style.SUCCESS(f"  ✅ {data['name']}"))

        self.stdout.write(self.style.SUCCESS(f"\nDone: {created} created, {skipped} skipped"))
