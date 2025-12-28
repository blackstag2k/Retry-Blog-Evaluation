import google.genai as genai
import pandas as pd
import time
import json
from pathlib import Path

client = genai.Client(api_key="ENTER_API_KEY")

json_folder = Path("LOCATION_OF_THE_INPUT_JSON_FOLDER")

system_prompt = """You are an expert content evaluator, editor, and SEO reviewer.

Your task is to objectively evaluate a blog draft provided by the user and score it using strict, measurable criteria. 
You must behave like an automated scoring engine, not a creative writer.

Evaluation Rules:
- Scores MUST be integers only (no decimals).
- Score range: 1 to 100.
- Be consistent and deterministic in scoring.
- Do NOT add explanations, commentary, or extra text.
- Do NOT include headings, markdown, or prose.
- Output ONLY the final CSV row.

Scoring Criteria:
1. readability_score:
   - Sentence clarity
   - Grammar and fluency
   - Ease of understanding for a general audience
   - Logical sentence flow

2. content_structure_score:
   - Logical progression of ideas
   - Paragraph organization
   - Use of headings or implicit structure
   - Coherence and flow between sections

3. engagement_score:
   - Ability to maintain reader interest
   - Tone and relatability
   - Hooks, examples, or persuasive elements
   - Overall reader involvement

CSV Output Format (STRICT):
Topics,readability_score,content_structure_score,engagement_score"""

MAX_RETRIES = 3
RETRY_DELAY = 6

def evaluate_content(blog_content, topic_content):
    user_prompt = f"""User Input:
Topic: {topic_content}

Blog Content:
{blog_content}

Now evaluate the draft content strictly based on the criteria above and output exactly ONE CSV row following the specified format."""
    full_prompt = system_prompt + "\n\n" + user_prompt
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_prompt
                )
            
            text = response.text.strip()

            scores = [s.strip() for s in text.split(",")]

            if len(scores) != 4:
                raise ValueError("Invalid CSV count")
            
            topic_name = scores[0]
            readability_score = int(scores[1])
            content_structure_score = int(scores[2])
            engagement_score = int(scores[3])
            
            return {
                "topic_name": topic_name,
                "readability_score": readability_score,
                "content_structure_score": content_structure_score,
                "engagement_score": engagement_score
                }
            
        except Exception as e:
            print(
                f"retry{attempt}/{MAX_RETRIES}"
                f"Evaluation failed for the topic '{topic_content}'. Error: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    return {
        "topic_name": topic_name,
        "readability_score": 0,
        "content_structure_score": 0,
        "engagement_score": 0
        }

output = []

for file in json_folder.glob("*.json"):
    with open (file, "r", encoding="utf-8")as f:
        draft = json.load(f)
        blog_content = draft["blog"]
        topic_content = draft["topic"]

        blog_scores = evaluate_content(blog_content, topic_content)
        output.append(blog_scores)

df = pd.DataFrame(output)
df.to_csv("ENTER_NAME_OF_THE_OUTPUT_CSV_FILE", index=False)

print(f"saved in the output.csv")
